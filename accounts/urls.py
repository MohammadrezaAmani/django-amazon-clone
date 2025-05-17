from django.urls import path
from rest_framework.routers import DefaultRouter

from .views.auth import (
    ForgotPasswordView,
    LoginView,
    LogoutView,
    MeView,
    RefreshView,
    RegisterView,
    ResetPasswordView,
    VerifyView,
)
from .views.user import UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("refresh/", RefreshView.as_view(), name="refresh"),
    path("verify/", VerifyView.as_view(), name="verify"),
    path("register/", RegisterView.as_view(), name="register"),
    path(
        "forgot-password/",
        ForgotPasswordView.as_view(),
        name="forgot-password",
    ),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),
]

urlpatterns.extend(router.urls)
