from celery import shared_task
from django.contrib.auth import get_user_model

from apps.audit_log.models import AuditLog
from apps.audit_log.utils import log_user_action
from apps.notifications.utils import send_notification

from .models import CartItem

User = get_user_model()


@shared_task
def notify_admins_on_cart_item_added(cart_item_id):
    cart_item = CartItem.objects.get(id=cart_item_id)  # type: ignore
    admins = User.objects.filter(is_staff=True)
    for admin in admins:
        send_notification(
            user=admin,
            message=f"New item added to cart: {cart_item.quantity} x {cart_item.variant}",
            category="cart",
            priority=AuditLog.Priority.LOW,  # type: ignore
            channels=["IN_APP"],
            metadata={"cart_item_id": cart_item_id},
        )
    log_user_action(
        user=None,
        action_type=AuditLog.ActionType.SYSTEM,
        content_object=cart_item,
        object_repr=f"{cart_item.quantity} x {cart_item.variant}",
        priority=AuditLog.Priority.LOW,
        metadata={
            "task": "notify_admins_on_cart_item_added",
            "cart_item_id": cart_item_id,
        },
    )
