from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Feedback(models.Model):
    class FeedbackType(models.TextChoices):
        BUG = "BUG", _("Bug Report")
        FEATURE = "FEATURE", _("Feature Request")
        SUPPORT = "SUPPORT", _("Support Request")
        OTHER = "OTHER", _("Other")

    class Status(models.TextChoices):
        NEW = "NEW", _("New")
        IN_PROGRESS = "IN_PROGRESS", _("In Progress")
        RESOLVED = "RESOLVED", _("Resolved")
        CLOSED = "CLOSED", _("Closed")

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feedbacks",
        help_text=_("User who submitted the feedback, if authenticated."),
    )
    feedback_type = models.CharField(
        max_length=20,
        choices=FeedbackType.choices,
        default=FeedbackType.OTHER,
        help_text=_("Type of feedback."),
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        help_text=_("Current status of the feedback."),
    )
    title = models.CharField(
        max_length=255,
        help_text=_("Short title or summary of the feedback."),
    )
    description = models.TextField(
        help_text=_("Detailed description of the feedback."),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Additional metadata (e.g., browser info, page URL)."),
    )

    class Meta:
        verbose_name = _("feedback")
        verbose_name_plural = _("feedbacks")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.feedback_type} - {self.title} ({self.status})"
