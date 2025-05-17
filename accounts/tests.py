from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class RegistrationViewTests(TransactionTestCase):
    def setUp(self):
        User.objects.all().delete()

        self.client = APIClient()
        self.register_url = reverse("register")
        self.login_url = reverse("login")
        self.admin_user = User.objects.create_superuser(
            "admin", "admin@example.com", "adminpassword"
        )

        refresh = RefreshToken.for_user(self.admin_user)
        self.admin_token = str(refresh.access_token)

    def tearDown(self):
        User.objects.all().delete()

    def test_register_new_user_as_admin(self):
        self.assertEqual(User.objects.count(), 1)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "NewUserPassword123!",
            "first_name": "New",
            "last_name": "User",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore

        self.assertEqual(User.objects.count(), 2)
        new_user = User.objects.get(username="newuser")
        self.assertEqual(new_user.email, "newuser@example.com")
        self.assertEqual(new_user.first_name, "New")
        self.assertEqual(new_user.last_name, "User")

    def test_register_new_user_as_non_admin(self):
        self.assertEqual(User.objects.count(), 1)

        non_admin_user = User.objects.create_user(
            "nonadmin", "nonadmin@example.com", "nonadminpassword"
        )

        refresh = RefreshToken.for_user(non_admin_user)
        non_admin_token = str(refresh.access_token)

        self.assertEqual(User.objects.count(), 2)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {non_admin_token}")
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "NewUserPassword123!",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # type: ignore

        self.assertEqual(User.objects.count(), 2)

    def test_register_new_user_unauthenticated(self):
        self.assertEqual(User.objects.count(), 1)

        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "NewUserPassword123!",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # type: ignore

        self.assertEqual(User.objects.count(), 1)

    def test_register_with_invalid_data(self):
        self.assertEqual(User.objects.count(), 1)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")

        data = {
            "username": "newuser",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # type: ignore

        self.assertEqual(User.objects.count(), 1)

        data = {
            "username": "admin",
            "email": "unique@example.com",
            "password": "ValidPassword123!",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # type: ignore

        self.assertEqual(User.objects.count(), 1)

        data = {
            "username": "uniqueuser",
            "email": "admin@example.com",
            "password": "ValidPassword123!",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # type: ignore

        self.assertEqual(User.objects.count(), 1)


class LoginViewTests(TransactionTestCase):
    def setUp(self):
        User.objects.all().delete()

        self.client = APIClient()
        self.login_url = reverse("login")
        self.user = User.objects.create_user(
            "testuser", "test@example.com", "testpassword123"
        )
        self.user.is_active = True
        self.user.is_verified = True
        self.user.save()

    def tearDown(self):
        User.objects.all().delete()

    def test_successful_login(self):
        data = {"username": "testuser", "password": "testpassword123"}
        response = self.client.post(self.login_url, data, format="json")
        if not response.data:  # type: ignore
            self.fail("Response data is empty")
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertIn("access", response.data)  # type: ignore
        self.assertIn("refresh", response.data)  # type: ignore
        self.assertIn("user", response.data)  # type: ignore

    def test_login_with_invalid_credentials(self):
        data = {"username": "testuser", "password": "wrongpassword"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # type: ignore

    def test_login_with_inactive_account(self):
        self.user.is_active = False
        self.user.save()

        data = {"username": "testuser", "password": "testpassword123"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # type: ignore
