import logging

from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from ..permissions import IsAdminUser, IsAdminUserOrReadOnly, IsOwnerOrAdmin
from ..serializers import RegisterSerializer, UserSerializer

logger = logging.getLogger(__name__)
User = get_user_model()


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )


class UserThrottle(UserRateThrottle):
    rate = "100/hour"


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("username")
    serializer_class = UserSerializer
    pagination_class = StandardResultsSetPagination
    throttle_classes = [UserThrottle]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["is_active", "is_staff", "is_verified"]
    search_fields = ["username", "email"]
    ordering_fields = ["username", "email", "date_joined", "last_activity"]
    ordering = ["username"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [permissions.IsAuthenticated, IsAdminUserOrReadOnly]
        elif self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
            "bulk_delete",
        ]:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
        elif self.action == "upload_profile_picture":
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated, IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):  # type: ignore
        if self.action == "create":
            return RegisterSerializer
        return UserSerializer

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(queryset, many=True)
            logger.info(f"User list accessed by {request.user.username}")
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error listing users: {str(e)}", exc_info=True)
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            logger.info(
                f"User {instance.username} details accessed by {request.user.username}"
            )
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving user: {str(e)}", exc_info=True)
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            logger.info(
                f"User created by {request.user.username}: {serializer.data['username']}"
            )
            return Response(
                serializer.data, status=status.HTTP_201_CREATED, headers=headers
            )
        except ValidationError as e:
            logger.warning(f"Validation error during user creation: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}", exc_info=True)
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop("partial", False)
            instance = self.get_object()
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            logger.info(f"User {instance.username} updated by {request.user.username}")
            return Response(serializer.data)
        except ValidationError as e:
            logger.warning(f"Validation error during user update: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}", exc_info=True)
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            logger.info(f"User {instance.username} deleted by {request.user.username}")
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}", exc_info=True)
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"], url_path="upload-profile-picture")
    def upload_profile_picture(self, request, pk=None):
        try:
            user = self.get_object()
            if "profile_picture" not in request.FILES:
                return Response(
                    {"error": "No file was submitted"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.profile_picture = request.FILES["profile_picture"]
            user.save()
            serializer = self.get_serializer(user)
            logger.info(
                f"Profile picture updated for user {user.username} by {request.user.username}"
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationError as e:
            logger.warning(f"Validation error during profile picture upload: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error uploading profile picture: {str(e)}", exc_info=True)
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"], url_path="bulk-delete")
    def bulk_delete(self, request):
        try:
            if not request.user.is_staff:
                return Response(
                    {"detail": "You do not have permission to perform this action"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            user_ids = request.data.get("user_ids", [])
            if not user_ids:
                return Response(
                    {"error": "user_ids is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Prevent deleting superusers or the requesting user
            users_to_delete = User.objects.filter(
                id__in=user_ids, is_superuser=False
            ).exclude(id=request.user.id)

            count = users_to_delete.count()
            if count == 0:
                return Response(
                    {"error": "No valid users to delete"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            users_to_delete.delete()
            logger.info(f"Bulk deleted {count} users by {request.user.username}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error during bulk delete: {str(e)}", exc_info=True)
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
