import uuid
from datetime import date

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django_ratelimit.exceptions import Ratelimited
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.admin import UserAdmin

User = get_user_model()


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser",
        email="testuser@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
        phone_number="+1234567890",
        bio="Test user bio",
        date_of_birth=date(1990, 1, 1),
        is_verified=True,
    )


@pytest.fixture
def inactive_user(db):
    return User.objects.create_user(
        username="inactiveuser",
        email="inactive@example.com",
        password="testpass123",
        is_active=False,
    )


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass123",
    )


@pytest.fixture
def redis_client():
    redis_conn = get_redis_connection("default")
    redis_conn.flushdb()
    return redis_conn


@pytest.mark.django_db
class TestUserModel:
    def test_user_creation(self, user):
        """Test user creation with all fields."""
        assert user.username == "testuser"
        assert user.email == "testuser@example.com"
        assert user.check_password("testpass123")
        assert user.phone_number == "+1234567890"
        assert user.bio == "Test user bio"
        assert user.date_of_birth == date(1990, 1, 1)
        assert user.is_verified is True
        assert user.is_active is True
        assert user.get_full_name() == "Test User"

    def test_email_normalization(self, db):
        """Test email is stored in lowercase."""
        user = User.objects.create_user(
            username="newuser",
            email="NEWUSER@EXAMPLE.COM",
            password="testpass123",
        )
        assert user.email == "newuser@example.com"

    def test_update_last_activity(self, user):
        """Test updating last activity timestamp."""
        from django.utils import timezone

        initial_time = user.last_activity
        user.update_last_activity()
        assert user.last_activity > initial_time
        assert user.last_activity <= timezone.now()

    def test_profile_picture_upload(self, user):
        """Test profile picture upload."""
        image = SimpleUploadedFile(
            "profile.jpg", b"file_content", content_type="image/jpeg"
        )
        user.profile_picture = image
        user.save()
        assert user.profile_picture.name.startswith("profile_pictures/profile_")
        assert user.profile_picture.name.endswith(".jpg")


@pytest.mark.django_db
class TestAuthURLs(TestCase):
    def test_url_patterns(self):
        """Test that all URL patterns resolve correctly."""
        url_names = [
            "login",
            "logout",
            "me",
            "refresh",
            "verify",
            "register",
            "forgot-password",
            "reset-password",
        ]
        for name in url_names:
            url = reverse(name)
            self.assertTrue(url.startswith("/api/auth/"))
            response = self.client.get(url, follow=True)
            self.assertIn(response.status_code, [200, 401, 403, 405])  # type: ignore


@pytest.mark.django_db
class TestLoginView:
    def test_login_success(self, api_client, user):
        """Test successful login with valid credentials."""
        data = {"username": "testuser", "password": "testpass123"}
        response = api_client.post(reverse("login"), data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["user"]["username"] == "testuser"
        assert response.data["user"]["email"] == "testuser@example.com"
        assert response.data["user"]["phone_number"] == "+1234567890"
        assert response.data["user"]["bio"] == "Test user bio"

    def test_login_invalid_credentials(self, api_client):
        """Test login with invalid credentials."""
        data = {"username": "testuser", "password": "wrongpass"}
        response = api_client.post(reverse("login"), data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["error"] == "Invalid credentials"

    def test_login_inactive_user(self, api_client, inactive_user):
        """Test login with inactive user account."""
        data = {"username": "inactiveuser", "password": "testpass123"}
        response = api_client.post(reverse("login"), data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["error"] == "Account is disabled"

    def test_login_missing_fields(self, api_client):
        """Test login with missing required fields."""
        data = {"username": "testuser"}
        response = api_client.post(reverse("login"), data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data


@pytest.mark.django_db
class TestLogoutView:
    def test_logout_success(self, api_client, user):
        """Test successful logout with valid refresh token."""
        refresh = RefreshToken.for_user(user)
        api_client.force_authenticate(user=user)
        data = {"refresh": str(refresh)}
        response = api_client.post(reverse("logout"), data, format="json")
        assert response.status_code == status.HTTP_205_RESET_CONTENT
        assert response.data["message"] == "Successfully logged out"

    def test_logout_invalid_token(self, api_client, user):
        """Test logout with invalid refresh token."""
        api_client.force_authenticate(user=user)
        data = {"refresh": "invalid_token"}
        response = api_client.post(reverse("logout"), data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error"] == "Invalid refresh token"

    def test_logout_unauthenticated(self, api_client):
        """Test logout without authentication."""
        data = {"refresh": "some_token"}
        response = api_client.post(reverse("logout"), data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestMeView:
    def test_me_success(self, api_client, user):
        """Test retrieving authenticated user profile."""
        api_client.force_authenticate(user=user)
        response = api_client.get(reverse("me"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == "testuser"
        assert response.data["email"] == "testuser@example.com"
        assert response.data["phone_number"] == "+1234567890"
        assert response.data["bio"] == "Test user bio"
        assert response.data["is_verified"] is True

    def test_me_unauthenticated(self, api_client):
        """Test accessing profile without authentication."""
        response = api_client.get(reverse("me"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestRefreshView:
    def test_refresh_success(self, api_client, user):
        """Test refreshing access token with valid refresh token."""
        refresh = RefreshToken.for_user(user)
        data = {"refresh": str(refresh)}
        response = api_client.post(reverse("refresh"), data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_refresh_invalid_token(self, api_client):
        """Test refreshing with invalid refresh token."""
        data = {"refresh": "invalid_token"}
        response = api_client.post(reverse("refresh"), data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["error"] == "Invalid refresh token"

    def test_refresh_blacklisted_token(self, api_client, user, redis_client):
        """Test refreshing with blacklisted refresh token."""
        refresh = RefreshToken.for_user(user)
        redis_client.set(f"blacklist:{str(refresh)}", "1")
        data = {"refresh": str(refresh)}
        response = api_client.post(reverse("refresh"), data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["error"] == "Token is blacklisted"


@pytest.mark.django_db
class TestVerifyView:
    def test_verify_success(self, api_client, user):
        """Test verifying a valid access token."""
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        data = {"access": access}
        response = api_client.post(reverse("verify"), data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["message"] == "Token is valid"
        assert response.data["user_id"] == user.id

    def test_verify_invalid_token(self, api_client):
        """Test verifying an invalid access token."""
        data = {"access": "invalid_token"}
        response = api_client.post(reverse("verify"), data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["error"] == "Invalid or expired token"


@pytest.mark.django_db
class TestRegisterView:
    def test_register_success(self, api_client):
        """Test successful user registration."""
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepass123",
            "first_name": "New",
            "last_name": "User",
            "phone_number": "+0987654321",
            "bio": "New user bio",
            "date_of_birth": "1995-02-02",
        }
        response = api_client.post(reverse("register"), data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["user"]["username"] == "newuser"
        assert response.data["user"]["phone_number"] == "+0987654321"
        assert response.data["user"]["bio"] == "New user bio"
        assert User.objects.filter(username="newuser").exists()

    def test_register_existing_email(self, api_client, user):
        """Test registration with existing email."""
        data = {
            "username": "newuser",
            "email": "testuser@example.com",
            "password": "securepass123",
        }
        response = api_client.post(reverse("register"), data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_register_existing_username(self, api_client, user):
        """Test registration with existing username."""
        data = {
            "username": "testuser",
            "email": "newuser@example.com",
            "password": "securepass123",
        }
        response = api_client.post(reverse("register"), data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.data


@pytest.mark.django_db
class TestForgotPasswordView:
    def test_forgot_password_success(self, api_client, user, mocker):
        """Test forgot password with existing email."""
        mocker.patch("django.core.mail.send_mail")
        data = {"email": "testuser@example.com"}
        response = api_client.post(reverse("forgot-password"), data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert (
            response.data["message"]
            == "If the email exists, a reset link has been sent"
        )
        assert len(mail.outbox) == 1  # type: ignore
        assert mail.outbox[0].subject == "Password Reset Request"  # type: ignore

    def test_forgot_password_nonexistent_email(self, api_client):
        """Test forgot password with non-existent email."""
        data = {"email": "nonexistent@example.com"}
        response = api_client.post(reverse("forgot-password"), data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert (
            response.data["message"]
            == "If the email exists, a reset link has been sent"
        )
        assert len(mail.outbox) == 0  # type: ignore

    def test_forgot_password_rate_limit(self, api_client, mocker):
        """Test rate limiting on forgot password endpoint."""
        mocker.patch("django_ratelimit.decorators.ratelimit", side_effect=Ratelimited())
        data = {"email": "testuser@example.com"}
        response = api_client.post(reverse("forgot-password"), data, format="json")
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@pytest.mark.django_db
class TestResetPasswordView:
    def test_reset_password_success(self, api_client, user, redis_client):
        """Test successful password reset with valid token and UID."""
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uid = str(uuid.uuid4())
        redis_client.setex(f"reset_token:{uid}", 3600, f"{user.id}:{token}")

        data = {
            "token": token,
            "uid": uid,
            "password": "newsecurepass123",
        }
        response = api_client.post(reverse("reset-password"), data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["message"] == "Password reset successful"

        user.refresh_from_db()
        assert user.check_password("newsecurepass123")
        assert redis_client.get(f"reset_token:{uid}") is None

    def test_reset_password_invalid_token(self, api_client, user, redis_client):
        """Test password reset with invalid token."""
        uid = str(uuid.uuid4())
        redis_client.setex(f"reset_token:{uid}", 3600, f"{user.id}:valid_token")

        data = {
            "token": "invalid_token",
            "uid": uid,
            "password": "newsecurepass123",
        }
        response = api_client.post(reverse("reset-password"), data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error"] == "Invalid reset token"

    def test_reset_password_expired_token(self, api_client, user, redis_client):
        """Test password reset with expired token (missing in Redis)."""
        data = {
            "token": "some_token",
            "uid": str(uuid.uuid4()),
            "password": "newsecurepass123",
        }
        response = api_client.post(reverse("reset-password"), data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error"] == "Invalid or expired reset token"


@pytest.mark.django_db
class TestUserAdmin:
    def test_admin_list_display(self, superuser):
        """Test admin list display fields."""
        site = AdminSite()
        user_admin = UserAdmin(User, site)
        assert user_admin.list_display == (
            "username",
            "email",
            "first_name",
            "last_name",
            "is_verified",
            "is_active",
            "is_staff",
            "last_activity",
            "date_joined",
        )

    def test_admin_verify_users_action(self, superuser, user):
        """Test verify_users admin action."""
        site = AdminSite()
        user_admin = UserAdmin(User, site)
        user.is_verified = False
        user.save()
        request = type("Request", (), {"user": superuser})()
        queryset = User.objects.filter(pk=user.pk)
        user_admin.verify_users(request, queryset)
        user.refresh_from_db()
        assert user.is_verified is True

    def test_admin_deactivate_users_action(self, superuser, user):
        """Test deactivate_users admin action."""
        site = AdminSite()
        user_admin = UserAdmin(User, site)
        request = type("Request", (), {"user": superuser})()
        queryset = User.objects.filter(pk=user.pk)
        user_admin.deactivate_users(request, queryset)
        user.refresh_from_db()
        assert user.is_active is False

    def test_admin_activate_users_action(self, superuser, inactive_user):
        """Test activate_users admin action."""
        site = AdminSite()
        user_admin = UserAdmin(User, site)
        request = type("Request", (), {"user": superuser})()
        queryset = User.objects.filter(pk=inactive_user.pk)
        user_admin.activate_users(request, queryset)
        inactive_user.refresh_from_db()
        assert inactive_user.is_active is True

    def test_admin_search_and_filters(self, superuser):
        """Test admin search fields and filters."""
        site = AdminSite()
        user_admin = UserAdmin(User, site)
        assert "username" in user_admin.search_fields
        assert "email" in user_admin.search_fields
        assert "phone_number" in user_admin.search_fields
        assert "is_verified" in user_admin.list_filter
        assert "is_active" in user_admin.list_filter
