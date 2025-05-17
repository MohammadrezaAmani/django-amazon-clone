from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150, required=True, help_text=_("Username to authenticate with")
    )
    password = serializers.CharField(
        max_length=128,
        required=True,
        write_only=True,
        help_text=_("Password for authentication"),
    )

    def validate(self, attrs):
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "last_login",
            "date_joined",
            "is_verified",
            "last_activity",
        ]
        read_only_fields = fields


class TokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField(help_text=_("JWT access token"))
    refresh = serializers.CharField(help_text=_("JWT refresh token"))
    user = UserSerializer(help_text=_("User details"))


class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField(
        required=True, help_text=_("JWT refresh token to get a new access token")
    )


class VerifySerializer(serializers.Serializer):
    access = serializers.CharField(
        required=True, help_text=_("JWT access token to verify")
    )


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        style={"input_type": "password"},
        help_text=_("Password must be at least 8 characters"),
    )

    class Meta:
        model = User
        fields = ["username", "email", "password", "first_name", "last_name"]
        extra_kwargs = {
            "username": {"required": True},
            "email": {"required": True},
            "first_name": {"required": False},
            "last_name": {"required": False},
        }

    def validate_email(self, value):
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError(_("Email already exists"))
        return value.lower()

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(_("Username already exists"))
        return value

    def validate_password(self, value):
        try:
            password_validation.validate_password(value)
        except ValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )
        return user


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True, help_text=_("Email address to send password reset link")
    )


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(required=True, help_text=_("Password reset token"))
    uid = serializers.CharField(
        required=True, help_text=_("User identifier for password reset")
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        style={"input_type": "password"},
        help_text=_("New password (minimum 8 characters)"),
    )

    def validate_password(self, value):
        try:
            password_validation.validate_password(value)
        except ValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value
