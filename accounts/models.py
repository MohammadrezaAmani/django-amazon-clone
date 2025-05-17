from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from guardian.mixins import GuardianUserMixin


class User(GuardianUserMixin, AbstractUser):
    """
    Custom User model with additional fields and Guardian permissions.
    """

    email = models.EmailField(
        _("email address"),
        unique=True,
        error_messages={"unique": _("A user with that email already exists.")},
    )
    phone_number = models.CharField(
        _("phone number"),
        max_length=15,
        blank=True,
        null=True,
        help_text=_(
            "Optional phone number in international format (e.g., +1234567890)."
        ),
    )
    bio = models.TextField(
        _("biography"),
        max_length=500,
        blank=True,
        help_text=_("Short user biography or description."),
    )
    date_of_birth = models.DateField(
        _("date of birth"),
        blank=True,
        null=True,
        help_text=_("Optional date of birth."),
    )
    is_verified = models.BooleanField(
        _("email verified"),
        default=False,  # type: ignore
        help_text=_("Indicates if the user's email has been verified."),  # type: ignore
    )
    profile_picture = models.ImageField(
        _("profile picture"),
        upload_to="profile_pictures/",
        blank=True,
        null=True,
        help_text=_("Optional profile picture."),
    )
    last_activity = models.DateTimeField(
        _("last activity"),
        blank=True,
        null=True,
        help_text=_("Timestamp of the user's last activity."),
    )

    is_staff = models.BooleanField(
        _("staff status"),
        default=False,  # type: ignore
        help_text=_("Designates whether the user can log into the admin site."),  # type: ignore
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,  # type: ignore
        help_text=_(  # type: ignore
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )

    class Meta:  # type: ignore
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["username"]

    def __str__(self):  # type: ignore
        return self.username

    def save(self, *args, **kwargs):
        """Ensure email is stored in lowercase."""
        if self.email:
            self.email = self.email.lower()  # type: ignore
        super().save(*args, **kwargs)

    def get_full_name(self):  # type: ignore
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.username

    def update_last_activity(self):
        """Update the last_activity timestamp."""
        from django.utils import timezone

        self.last_activity = timezone.now()
        self.save(update_fields=["last_activity"])
