from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class AuditLog(models.Model):
    """Stores detailed logs of user and system actions."""

    class ActionType(models.TextChoices):
        LOGIN = "LOGIN", _("Login")
        LOGOUT = "LOGOUT", _("Logout")
        CREATE = "CREATE", _("Create")
        UPDATE = "UPDATE", _("Update")
        DELETE = "DELETE", _("Delete")
        VIEW = "VIEW", _("View")
        SYSTEM = "SYSTEM", _("System")

    class Status(models.TextChoices):
        SUCCESS = "SUCCESS", _("Success")
        FAILED = "FAILED", _("Failed")

    class Priority(models.TextChoices):
        LOW = "LOW", _("Low")
        MEDIUM = "MED", _("Medium")
        HIGH = "HIGH", _("High")

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        help_text=_("User who performed the action, if applicable."),
    )
    action_type = models.CharField(
        max_length=20,
        choices=ActionType.choices,
        help_text=_("Type of action performed."),
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUCCESS,
        help_text=_("Status of the action."),
    )
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.LOW,
        help_text=_("Priority level of the action."),
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text=_("IP address of the client."),
    )
    user_agent = models.TextField(
        blank=True,
        help_text=_("User agent of the client (browser/server details)."),
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("Model associated with the action."),
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_("ID of the object affected."),  # type: ignore
    )
    content_object = GenericForeignKey("content_type", "object_id")
    object_repr = models.TextField(
        blank=True,
        help_text=_("String representation of the affected object."),
    )
    changes = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Changes made (before and after) in JSON format."),
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Additional metadata (e.g., request URL, method)."),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    error_message = models.TextField(
        blank=True,
        help_text=_("Error message if the action failed."),
    )

    class Meta:
        verbose_name = _("audit log")
        verbose_name_plural = _("audit logs")
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["action_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["priority"]),
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["ip_address"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.action_type} ({self.priority}) by {self.user} at {self.created_at}"
        )

    @classmethod
    def log_action(
        cls,
        user=None,
        action_type=None,
        status=Status.SUCCESS,
        priority=None,
        ip_address=None,
        user_agent=None,
        content_object=None,
        object_repr=None,
        changes=None,
        metadata=None,
        error_message=None,
    ):
        """Helper method to create an audit log entry."""
        content_type = None
        object_id = None
        if content_object:
            content_type = ContentType.objects.get_for_model(content_object)
            object_id = content_object.pk

        # Set default priority based on action_type if not provided
        if priority is None:
            priority_map = {
                cls.ActionType.LOGIN: cls.Priority.LOW,
                cls.ActionType.LOGOUT: cls.Priority.LOW,
                cls.ActionType.VIEW: cls.Priority.LOW,
                cls.ActionType.CREATE: cls.Priority.MEDIUM,
                cls.ActionType.UPDATE: cls.Priority.MEDIUM,
                cls.ActionType.DELETE: cls.Priority.HIGH,
                cls.ActionType.SYSTEM: cls.Priority.HIGH,
            }
            priority = priority_map.get(action_type, cls.Priority.LOW)  # type: ignore

        cls.objects.create(  # type: ignore
            user=user,
            action_type=action_type,
            status=status,
            priority=priority,
            ip_address=ip_address,
            user_agent=user_agent,
            content_type=content_type,
            object_id=object_id,
            object_repr=object_repr or (str(content_object) if content_object else ""),
            changes=changes or {},
            metadata=metadata or {},
            error_message=error_message or "",
        )
