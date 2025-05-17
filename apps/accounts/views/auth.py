import logging
import uuid

import jwt
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.urls import reverse
from django_ratelimit.decorators import ratelimit
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from redis import Redis
from rest_framework import serializers, status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.accounts.serializers import (
    ForgotPasswordSerializer,
    LoginSerializer,
    RefreshSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    TokenResponseSerializer,
    UserSerializer,
    VerifySerializer,
)
from apps.audit_log.models import AuditLog
from apps.audit_log.utils import log_user_action

logger = logging.getLogger(__name__)

User = get_user_model()

redis_client = None
if hasattr(settings, "REDIS_HOST") and settings.REDIS_HOST:
    try:
        redis_client = Redis(
            host=settings.REDIS_HOST,
            port=getattr(settings, "REDIS_PORT", 6379),
            db=getattr(settings, "REDIS_DB", 0),
            decode_responses=True,
        )
    except (ImportError, ConnectionError):
        logger.warning("Redis is not available. Token storage will be disabled.")


def get_tokens_for_user(user):
    """Generate access and refresh tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


class LoginView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    @extend_schema(
        tags=["Authentication"],
        request=LoginSerializer,
        responses={
            200: TokenResponseSerializer,
            400: OpenApiResponse(
                description="Invalid input",
                examples=[
                    OpenApiExample(
                        "Invalid input", value={"error": "username is required"}
                    )
                ],
            ),
            401: OpenApiResponse(
                description="Invalid credentials",
                examples=[
                    OpenApiExample(
                        "Invalid credentials", value={"error": "Invalid credentials"}
                    )
                ],
            ),
            403: OpenApiResponse(
                description="Account disabled",
                examples=[
                    OpenApiExample(
                        "Account disabled", value={"error": "Account is disabled"}
                    )
                ],
            ),
        },
        description="Authenticates a user and returns JWT access and refresh tokens along with user details.",
        examples=[
            OpenApiExample(
                "Login request",
                value={"username": "johndoe", "password": "secure123"},
                request_only=True,
            ),
            OpenApiExample(
                "Login response",
                value={
                    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "user": {
                        "id": 1,
                        "username": "johndoe",
                        "email": "john@example.com",
                        "first_name": "John",
                        "last_name": "Doe",
                        "last_login": "2025-05-16T12:00:00Z",
                        "date_joined": "2025-05-16T12:00:00Z",
                    },
                },
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        """Handle user login and return JWT tokens."""
        try:
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            username = serializer.validated_data["username"]  # type: ignore
            password = serializer.validated_data["password"]  # type: ignore

            user = authenticate(username=username, password=password)
            if user is None:
                logger.warning(f"Failed login attempt for username: {username}")
                return Response(
                    {"error": "Invalid credentials"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            if not user.is_active:
                logger.warning(f"Inactive user attempted login: {username}")
                return Response(
                    {"error": "Account is disabled"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            tokens = get_tokens_for_user(user)
            logger.info(f"Successful login for user: {username}")

            refresh_token_expiry = settings.SIMPLE_JWT[
                "REFRESH_TOKEN_LIFETIME"
            ].total_seconds()

            if redis_client:
                try:
                    redis_client.setex(
                        f"refresh_token:{user.id}",
                        int(refresh_token_expiry),
                        tokens["refresh"],
                    )
                except Exception as e:
                    logger.warning(f"Failed to store token in Redis: {str(e)}")

            user_serializer = UserSerializer(user)
            user_data = user_serializer.data
            response_data = {
                "access": tokens["access"],
                "refresh": tokens["refresh"],
                "user": user_data,
            }
            log_user_action(
                request=request,
                action_type=AuditLog.ActionType.LOGIN,
                status=AuditLog.Status.SUCCESS,
                content_object=user,
                priority=AuditLog.Priority.LOW,
            )
            return Response(response_data, status=status.HTTP_200_OK)

        except serializers.ValidationError as e:
            logger.warning(f"Validation error during login: {str(e)}")
            log_user_action(
                request=request,
                action_type=AuditLog.ActionType.LOGIN,
                status=AuditLog.Status.FAILED,
                error_message="Invalid credentials",
                priority=AuditLog.Priority.LOW,
            )
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Login error: {str(e)}", exc_info=True)
            log_user_action(
                request=request,
                action_type=AuditLog.ActionType.LOGIN,
                status=AuditLog.Status.FAILED,
                error_message=str(e),
                priority=AuditLog.Priority.LOW,
            )
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LogoutView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RefreshSerializer

    @extend_schema(
        tags=["Authentication"],
        request=RefreshSerializer,
        responses={
            205: OpenApiResponse(description="Successfully logged out"),
            400: OpenApiResponse(
                description="Invalid input",
                examples=[
                    OpenApiExample(
                        "Invalid input", value={"error": "refresh is required"}
                    )
                ],
            ),
            401: OpenApiResponse(
                description="Invalid refresh token",
                examples=[
                    OpenApiExample(
                        "Invalid token", value={"error": "Invalid refresh token"}
                    )
                ],
            ),
        },
        description="Logs out a user by blacklisting the provided refresh token.",
        examples=[
            OpenApiExample(
                "Logout request",
                value={"refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."},
                request_only=True,
            ),
            OpenApiExample(
                "Logout response",
                value={"message": "Successfully logged out"},
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        """Handle user logout by blacklisting tokens."""
        try:
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            refresh_token = serializer.validated_data["refresh"]  # type: ignore

            try:
                token = RefreshToken(refresh_token)
                token.blacklist()

                user_id = request.user.id

                if redis_client:
                    try:
                        redis_client.delete(f"refresh_token:{user_id}")
                    except Exception as e:
                        logger.warning(f"Failed to delete token from Redis: {str(e)}")

                logger.info(f"Successful logout for user: {request.user.username}")
                log_user_action(
                    request=request,
                    action_type=AuditLog.ActionType.LOGOUT,
                    status=AuditLog.Status.SUCCESS,
                    content_object=request.user,
                    priority=AuditLog.Priority.LOW,
                )
                return Response(
                    {"message": "Successfully logged out"},
                    status=status.HTTP_205_RESET_CONTENT,
                )

            except TokenError as e:
                logger.warning(f"Invalid refresh token during logout: {str(e)}")
                log_user_action(
                    request=request,
                    action_type=AuditLog.ActionType.LOGOUT,
                    status=AuditLog.Status.FAILED,
                    error_message=str(e),
                    priority=AuditLog.Priority.LOW,
                )
                return Response(
                    {"error": "Invalid refresh token"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except serializers.ValidationError as e:
            logger.warning(f"Validation error during logout: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Logout error: {str(e)}", exc_info=True)
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MeView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    @extend_schema(
        tags=["User Management"],
        responses={
            200: UserSerializer,
            401: OpenApiResponse(
                description="Unauthorized",
                examples=[
                    OpenApiExample(
                        "Unauthorized",
                        value={
                            "detail": "Authentication credentials were not provided"
                        },
                    )
                ],
            ),
        },
        description="Retrieves the authenticated user's profile information.",
        examples=[
            OpenApiExample(
                "Profile response",
                value={
                    "id": 1,
                    "username": "johndoe",
                    "email": "john@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "last_login": "2025-05-16T12:00:00Z",
                    "date_joined": "2025-05-16T12:00:00Z",
                },
                response_only=True,
            )
        ],
    )
    def get(self, request):
        """Return current user profile information."""
        try:
            user = request.user
            logger.info(f"Profile accessed for user: {user.username}")

            serialized_user = self.get_serializer(user)
            return Response(serialized_user.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Profile access error: {str(e)}", exc_info=True)
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RefreshView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = RefreshSerializer

    @extend_schema(
        tags=["Authentication"],
        request=RefreshSerializer,
        responses={
            200: OpenApiResponse(
                description="New access token",
                examples=[
                    OpenApiExample(
                        "Refresh response",
                        value={"access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."},
                    )
                ],
            ),
            400: OpenApiResponse(
                description="Invalid input",
                examples=[
                    OpenApiExample(
                        "Invalid input", value={"error": "refresh is required"}
                    )
                ],
            ),
            401: OpenApiResponse(
                description="Invalid or blacklisted token",
                examples=[
                    OpenApiExample(
                        "Invalid token", value={"error": "Invalid refresh token"}
                    ),
                    OpenApiExample(
                        "Blacklisted token", value={"error": "Token is blacklisted"}
                    ),
                ],
            ),
        },
        description="Refreshes a JWT access token using a valid refresh token.",
        examples=[
            OpenApiExample(
                "Refresh request",
                value={"refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        """Refresh access token using refresh token."""
        try:
            serializer = RefreshSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            refresh_token = serializer.validated_data["refresh"]  # type: ignore

            try:
                refresh = RefreshToken(refresh_token)
                access_token = str(refresh.access_token)

                is_blacklisted = False
                if redis_client:
                    try:
                        is_blacklisted = redis_client.get(f"blacklist:{refresh_token}")
                    except Exception as e:
                        logger.warning(f"Failed to check blacklist in Redis: {str(e)}")

                if is_blacklisted:
                    logger.warning("Attempt to use blacklisted refresh token")
                    return Response(
                        {"error": "Token is blacklisted"},
                        status=status.HTTP_401_UNAUTHORIZED,
                    )

                logger.info("Successful token refresh")
                return Response({"access": access_token}, status=status.HTTP_200_OK)

            except TokenError as e:
                logger.warning(f"Invalid refresh token: {str(e)}")
                return Response(
                    {"error": "Invalid refresh token"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

        except serializers.ValidationError as e:
            logger.warning(f"Validation error during refresh: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}", exc_info=True)
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VerifyView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = VerifySerializer

    @extend_schema(
        tags=["Authentication"],
        request=VerifySerializer,
        responses={
            200: OpenApiResponse(
                description="Token is valid",
                examples=[
                    OpenApiExample(
                        "Verify response",
                        value={
                            "message": "Token is valid",
                            "user_id": 1,
                            "exp": 1620000000,
                        },
                    )
                ],
            ),
            400: OpenApiResponse(
                description="Invalid input",
                examples=[
                    OpenApiExample(
                        "Invalid input", value={"error": "access is required"}
                    )
                ],
            ),
            401: OpenApiResponse(
                description="Invalid or expired token",
                examples=[
                    OpenApiExample(
                        "Invalid token", value={"error": "Invalid or expired token"}
                    )
                ],
            ),
        },
        description="Verifies if a JWT access token is valid and returns token details.",
        examples=[
            OpenApiExample(
                "Verify request",
                value={"access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        """Verify if access token is valid."""
        try:
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            access_token = serializer.validated_data["access"]  # type: ignore

            try:
                token = AccessToken(access_token)
                token.verify()

                payload = jwt.decode(
                    access_token,
                    settings.SIMPLE_JWT["SIGNING_KEY"],
                    algorithms=[settings.SIMPLE_JWT["ALGORITHM"]],
                )

                logger.info(
                    f"Token verification successful for user_id: {payload['user_id']}"
                )
                return Response(
                    {
                        "message": "Token is valid",
                        "user_id": payload["user_id"],
                        "exp": payload["exp"],
                    },
                    status=status.HTTP_200_OK,
                )

            except TokenError as e:
                logger.warning(f"Invalid access token: {str(e)}")
                return Response(
                    {"error": "Invalid or expired token"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

        except serializers.ValidationError as e:
            logger.warning(f"Validation error during verify: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}", exc_info=True)
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RegisterView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    @extend_schema(
        tags=["User Management"],
        request=RegisterSerializer,
        responses={
            201: TokenResponseSerializer,
            400: OpenApiResponse(
                description="Invalid input",
                examples=[
                    OpenApiExample(
                        "Invalid input", value={"error": "Email already exists"}
                    )
                ],
            ),
            401: OpenApiResponse(
                description="Unauthorized",
                examples=[
                    OpenApiExample(
                        "Unauthorized",
                        value={
                            "detail": "Authentication credentials were not provided"
                        },
                    )
                ],
            ),
            403: OpenApiResponse(
                description="Forbidden",
                examples=[
                    OpenApiExample(
                        "Forbidden",
                        value={
                            "error": "You do not have permission to perform this action"
                        },
                    )
                ],
            ),
        },
        description="Registers a new user and returns JWT tokens and user details.",
        examples=[
            OpenApiExample(
                "Register request",
                value={
                    "username": "janedoe",
                    "email": "jane@example.com",
                    "password": "secure123",
                    "first_name": "Jane",
                    "last_name": "Doe",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Register response",
                value={
                    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "user": {
                        "id": 2,
                        "username": "janedoe",
                        "email": "jane@example.com",
                        "first_name": "Jane",
                        "last_name": "Doe",
                        "last_login": None,
                        "date_joined": "2025-05-16T12:00:00Z",
                    },
                },
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        """Handle user registration with rate limiting."""
        try:
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            user = serializer.save()
            tokens = get_tokens_for_user(user)
            logger.info(
                f"New user registered by admin {request.user.username}: {user.username}"
            )

            user_data = UserSerializer(user).data
            response_data = {
                "access": tokens["access"],
                "refresh": tokens["refresh"],
                "user": user_data,
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

        except serializers.ValidationError as e:
            logger.warning(f"Validation error during registration: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Registration error: {str(e)}", exc_info=True)
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ForgotPasswordView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = ForgotPasswordSerializer

    @ratelimit(key="ip", rate="5/m", method="POST", block=True)
    @extend_schema(
        tags=["Password Reset"],
        request=ForgotPasswordSerializer,
        responses={
            200: OpenApiResponse(
                description="Reset link sent if email exists",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "message": "If the email exists, a reset link has been sent"
                        },
                    )
                ],
            ),
            400: OpenApiResponse(
                description="Invalid input",
                examples=[
                    OpenApiExample(
                        "Invalid input", value={"error": "email is required"}
                    )
                ],
            ),
        },
        description="Sends a password reset link to the user's email if the email exists.",
        examples=[
            OpenApiExample(
                "Forgot password request",
                value={"email": "john@example.com"},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        """Handle forgot password request by sending a reset email."""
        try:
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            email = serializer.validated_data["email"]  # type: ignore
            user = User.objects.filter(email=email).first()
            if not user:
                logger.warning(
                    f"Password reset requested for non-existent email: {email}"
                )
                return Response(
                    {"message": "If the email exists, a reset link has been sent"},
                    status=status.HTTP_200_OK,
                )

            token_generator = PasswordResetTokenGenerator()
            token = token_generator.make_token(user)
            uid = str(uuid.uuid4())

            if redis_client:
                try:
                    redis_client.setex(f"reset_token:{uid}", 3600, f"{user.id}:{token}")
                except Exception as e:
                    logger.warning(f"Failed to store reset token in Redis: {str(e)}")

            reset_url = request.build_absolute_uri(
                reverse("reset-password") + f"?uid={uid}&token={token}"
            )

            send_mail(
                subject="Password Reset Request",
                message=f"Click the link to reset your password: {reset_url}\nThis link is valid for 1 hour.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

            logger.info(f"Password reset email sent to: {email}")
            return Response(
                {"message": "If the email exists, a reset link has been sent"},
                status=status.HTTP_200_OK,
            )

        except serializers.ValidationError as e:
            logger.warning(f"Validation error during forgot password: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Forgot password error: {str(e)}", exc_info=True)
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ResetPasswordView(GenericAPIView):
    # Anyone with valid reset token can reset password
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordSerializer

    @extend_schema(
        tags=["Password Reset"],
        request=ResetPasswordSerializer,
        responses={
            200: OpenApiResponse(
                description="Password reset successful",
                examples=[
                    OpenApiExample(
                        "Success", value={"message": "Password reset successful"}
                    )
                ],
            ),
            400: OpenApiResponse(
                description="Invalid input or token",
                examples=[
                    OpenApiExample(
                        "Invalid input", value={"error": "token is required"}
                    ),
                    OpenApiExample(
                        "Invalid token", value={"error": "Invalid reset token"}
                    ),
                ],
            ),
        },
        description="Resets a user's password using a valid token and UID.",
        examples=[
            OpenApiExample(
                "Reset password request",
                value={
                    "token": "abc123",
                    "uid": "550e8400-e29b-41d4-a716-446655440000",
                    "password": "newsecure123",
                },
                request_only=True,
            )
        ],
    )
    def post(self, request):
        """Handle password reset with token verification."""
        try:
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            token = serializer.validated_data["token"]  # type: ignore
            uid = serializer.validated_data["uid"]  # type: ignore
            new_password = serializer.validated_data["password"]  # type: ignore

            reset_data = None
            if redis_client:
                try:
                    reset_data = redis_client.get(f"reset_token:{uid}")
                except Exception as e:
                    logger.warning(f"Failed to get reset token from Redis: {str(e)}")

            if not reset_data:
                logger.warning(f"Invalid or expired reset token for uid: {uid}")
                return Response(
                    {"error": "Invalid or expired reset token"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user_id, stored_token = reset_data.split(":")  # type: ignore
            user = User.objects.filter(id=user_id).first()
            if not user:
                logger.warning(f"User not found for reset token uid: {uid}")
                return Response(
                    {"error": "Invalid reset token"}, status=status.HTTP_400_BAD_REQUEST
                )

            token_generator = PasswordResetTokenGenerator()
            if not token_generator.check_token(user, token):
                logger.warning(f"Invalid reset token for user: {user.username}")
                return Response(
                    {"error": "Invalid reset token"}, status=status.HTTP_400_BAD_REQUEST
                )

            user.set_password(new_password)
            user.save()

            if redis_client:
                try:
                    redis_client.delete(f"reset_token:{uid}")
                except Exception as e:
                    logger.warning(f"Failed to delete reset token from Redis: {str(e)}")

            logger.info(f"Password reset successful for user: {user.username}")
            return Response(
                {"message": "Password reset successful"}, status=status.HTTP_200_OK
            )

        except serializers.ValidationError as e:
            logger.warning(f"Validation error during password reset: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Password reset error: {str(e)}", exc_info=True)
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
