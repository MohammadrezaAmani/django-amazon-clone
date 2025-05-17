from celery import shared_task
from django.contrib.auth import get_user_model

from apps.audit_log.models import AuditLog
from apps.audit_log.utils import log_user_action
from apps.notifications.utils import send_notification

from .models import Feedback

User = get_user_model()


@shared_task
def notify_admins_on_feedback(feedback_id):
    feedback = Feedback.objects.get(id=feedback_id)  # type: ignore
    admins = User.objects.filter(is_staff=True)
    for admin in admins:
        send_notification(
            user=admin,
            message=f"New feedback submitted: {feedback.title} ({feedback.feedback_type})",
            category="feedback",
            priority=AuditLog.Priority.MEDIUM,  # type: ignore
            channels=["IN_APP", "EMAIL"],
            metadata={"feedback_id": feedback_id},
        )
    log_user_action(
        user=None,
        action_type=AuditLog.ActionType.SYSTEM,
        content_object=feedback,
        object_repr=feedback.title,
        priority=AuditLog.Priority.MEDIUM,
        metadata={"task": "notify_admins_on_feedback", "feedback_id": feedback_id},
    )


@shared_task
def check_pending_feedbacks():
    pending_feedbacks = Feedback.objects.filter(status="NEW")  # type: ignore
    if pending_feedbacks.exists():
        admins = User.objects.filter(is_staff=True)
        for admin in admins:
            send_notification(
                user=admin,
                message=f"There are {pending_feedbacks.count()} pending feedbacks to review.",
                category="feedback",
                priority=AuditLog.Priority.MEDIUM,  # type: ignore
                channels=["IN_APP", "EMAIL"],
                metadata={"pending_count": pending_feedbacks.count()},
            )
        log_user_action(
            user=None,
            action_type=AuditLog.ActionType.SYSTEM,
            object_repr="Pending feedbacks check",
            priority=AuditLog.Priority.MEDIUM,
            metadata={
                "task": "check_pending_feedbacks",
                "pending_count": pending_feedbacks.count(),
            },
        )
