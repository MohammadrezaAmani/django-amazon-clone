from celery import shared_task
from django.contrib.auth import get_user_model

from apps.audit_log.models import AuditLog
from apps.audit_log.utils import log_user_action
from apps.notifications.utils import send_notification

from .models import Order

User = get_user_model()


@shared_task
def notify_user_on_order_status_change(order_id):
    order = Order.objects.get(id=order_id)  # type: ignore
    send_notification(
        user=order.user,
        message=f"Your order {order.id} status changed to {order.get_status_display()}",
        category="order",
        priority=AuditLog.Priority.MEDIUM,  # type: ignore
        channels=["IN_APP", "EMAIL", "WEBSOCKET"],
        metadata={"order_id": order_id, "status": order.status},
    )
    admins = User.objects.filter(is_staff=True)
    for admin in admins:
        send_notification(
            user=admin,
            message=f"Order {order.id} status changed to {order.get_status_display()}",
            category="order",
            priority=AuditLog.Priority.MEDIUM,  # type: ignore
            channels=["IN_APP", "EMAIL"],
            metadata={"order_id": order_id, "status": order.status},
        )
    log_user_action(
        user=None,
        action_type=AuditLog.ActionType.SYSTEM,
        content_object=order,
        object_repr=f"Order {order.id}",
        priority=AuditLog.Priority.MEDIUM,
        metadata={"task": "notify_user_on_order_status_change", "order_id": order_id},
    )
