import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.mail import send_mail
from django.template import Context, Template

from .models import Notification, NotificationBatch, NotificationTemplate

logger = logging.getLogger(__name__)


def send_notification(
    user,
    message=None,
    template_name=None,
    context=None,
    subject=None,
    priority=Notification.Priority.MEDIUM,
    channels=None,
    category=None,
    metadata=None,
    expires_at=None,
    batch=None,
):
    """
    Send a notification to a single user.

    Args:
        user: User instance to receive the notification.
        message: Direct message content (if no template).
        template_name: Name of the NotificationTemplate to use.
        context: Dict with template variables (e.g., {"username": user.username}).
        subject: Email subject (if applicable).
        priority: Notification priority (LOW, MEDIUM, HIGH).
        channels: List of channels (e.g., ["IN_APP", "EMAIL", "WEBSOCKET"]).
        category: Notification category (e.g., "system").
        metadata: Custom metadata (e.g., {"link": "/dashboard"}).
        expires_at: Optional expiration date.
        batch: Optional NotificationBatch instance.
    """
    if channels is None:
        channels = [Notification.Channel.IN_APP, Notification.Channel.WEBSOCKET]

    if not message and not template_name:
        logger.error("Either message or template_name must be provided.")
        return None

    # Load template if provided
    template = None
    if template_name:
        try:
            template = NotificationTemplate.objects.get(name=template_name)  # type: ignore
            message = Template(template.message).render(Context(context or {}))
            subject = subject or Template(template.subject).render(
                Context(context or {})
            )
            category = category or template.category
        except NotificationTemplate.DoesNotExist:  # type: ignore
            logger.error(f"Template '{template_name}' not found.")
            return None

    # Create notification
    notification = Notification.objects.create(  # type: ignore
        user=user,
        template=template,
        batch=batch,
        message=message,
        subject=subject or "",
        priority=priority,
        channels=channels,
        category=category or "",
        metadata=metadata or {},
        expires_at=expires_at,
        status=Notification.Status.PENDING,
    )

    # Handle delivery channels
    channel_layer = get_channel_layer()

    if Notification.Channel.WEBSOCKET in channels:
        try:
            async_to_sync(channel_layer.group_send)(  # type: ignore
                f"user_{user.id}",
                {
                    "type": "send_notification",
                    "notification_id": notification.id,
                    "message": notification.message,
                    "priority": notification.priority,
                    "category": notification.category,
                    "metadata": notification.metadata,
                    "timestamp": notification.created_at.isoformat(),
                },
            )
            notification.mark_as_sent()
        except Exception as e:
            notification.mark_as_failed(str(e))
            logger.error(f"WebSocket delivery failed for {user.username}: {str(e)}")

    if Notification.Channel.EMAIL in channels and user.email:
        try:
            send_mail(
                subject=notification.subject or "New Notification",
                message=notification.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            notification.mark_as_sent()
        except Exception as e:
            notification.mark_as_failed(str(e))
            logger.error(f"Email delivery failed for {user.email}: {str(e)}")

    if Notification.Channel.IN_APP in channels:
        notification.mark_as_sent()

    logger.info(
        f"Notification {notification.id} sent to {user.username} via {channels}"
    )
    return notification


def send_batch_notification(
    users,
    message=None,
    template_name=None,
    context=None,
    subject=None,
    priority=Notification.Priority.MEDIUM,
    channels=None,
    category=None,
    metadata=None,
    expires_at=None,
    description="Batch Notification",
    created_by=None,
):
    """
    Send notifications to multiple users as a batch.

    Args:
        users: Queryset or list of User instances.
        description: Description of the batch.
        created_by: User who initiated the batch.
        (Other args same as send_notification)
    """
    batch = NotificationBatch.objects.create(  # type: ignore
        description=description,
        created_by=created_by,
    )

    notifications = []
    for user in users:
        notification = send_notification(
            user=user,
            message=message,
            template_name=template_name,
            context=context,
            subject=subject,
            priority=priority,
            channels=channels,
            category=category,
            metadata=metadata,
            expires_at=expires_at,
            batch=batch,
        )
        if notification:
            notifications.append(notification)

    logger.info(f"Batch {batch.batch_id} sent to {len(notifications)} users")
    return batch, notifications
