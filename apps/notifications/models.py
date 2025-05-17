import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class NotificationTemplate(models.Model):
    """Stores reusable notification templates."""

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text=_("Unique name for the template (e.g., 'welcome_message')."),
    )
    subject = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Subject for email notifications."),
    )
    message = models.TextField(
        help_text=_("Template message with placeholders (e.g., {username})."),
    )
    category = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("Category for grouping templates (e.g., 'system', 'marketing')."),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("notification template")
        verbose_name_plural = _("notification templates")
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.category or 'Uncategorized'})"


class NotificationBatch(models.Model):
    """Represents a batch of notifications sent to multiple users."""

    batch_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text=_("Unique identifier for the batch."),
    )
    description = models.CharField(
        max_length=255,
        help_text=_("Description of the batch (e.g., 'Welcome campaign')."),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("User who initiated the batch."),
    )

    class Meta:
        verbose_name = _("notification batch")
        verbose_name_plural = _("notification batches")

    def __str__(self):
        return f"Batch {self.batch_id} ({self.description})"


class Notification(models.Model):
    """Stores individual notifications for users."""

    class Priority(models.TextChoices):
        LOW = "LOW", _("Low")
        MEDIUM = "MED", _("Medium")
        HIGH = "HIGH", _("High")

    class Channel(models.TextChoices):
        IN_APP = "IN_APP", _("In-App")
        EMAIL = "EMAIL", _("Email")
        WEBSOCKET = "WEBSOCKET", _("WebSocket")

    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        SENT = "SENT", _("Sent")
        FAILED = "FAILED", _("Failed")

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
        help_text=_("Recipient of the notification."),
    )
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("Optional template used for this notification."),
    )
    batch = models.ForeignKey(
        NotificationBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
        help_text=_("Batch this notification belongs to, if any."),
    )
    message = models.TextField(
        help_text=_("Rendered notification message."),
    )
    subject = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Subject for email notifications."),
    )
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        help_text=_("Priority level of the notification."),
    )
    channels = models.JSONField(
        default=list,
        help_text=_("List of delivery channels (e.g., ['IN_APP', 'EMAIL'])."),
    )
    category = models.CharField(
        max_length=50,
        blank=True,
        help_text=_(
            "Category for grouping notifications (e.g., 'system', 'marketing')."
        ),
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text=_("Delivery status of the notification."),
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=_(
            "Custom metadata (e.g., {'link': '/dashboard', 'action': 'view'})."
        ),
    )
    is_read = models.BooleanField(
        default=False,
        help_text=_("Whether the notification has been read (in-app)."),
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Optional expiration date for the notification."),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("notification")
        verbose_name_plural = _("notifications")
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["is_read"]),
            models.Index(fields=["category"]),
            models.Index(fields=["status"]),
            models.Index(fields=["expires_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification for {self.user.username} ({self.priority} - {self.category or 'Uncategorized'})"

    def mark_as_read(self):
        """Mark the notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])

    def mark_as_sent(self):
        """Mark the notification as sent."""
        if self.status != self.Status.SENT:
            self.status = self.Status.SENT
            self.sent_at = timezone.now()
            self.save(update_fields=["status", "sent_at"])

    def mark_as_failed(self, error_message=None):
        """Mark the notification as failed."""
        if self.status != self.Status.FAILED:
            self.status = self.Status.FAILED
            if error_message:
                self.metadata["error"] = error_message
            self.save(update_fields=["status", "metadata"])

    def is_expired(self):
        """Check if the notification has expired."""
        if self.expires_at and timezone.now() > self.expires_at:
            return True
        return False
