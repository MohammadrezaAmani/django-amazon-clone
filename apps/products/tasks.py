from celery import shared_task
from django.contrib.auth import get_user_model
from apps.audit_log.models import AuditLog
from apps.audit_log.utils import log_user_action
from apps.notifications.utils import send_notification
from .models import Product, Inventory

User = get_user_model()


@shared_task
def notify_admins_on_new_product(product_id):
    product = Product.objects.get(id=product_id)  # type: ignore
    admins = User.objects.filter(is_staff=True)
    for admin in admins:
        send_notification(
            user=admin,
            message=f"New product added: {product.name}",
            category="product",
            priority=AuditLog.Priority.MEDIUM,  # type: ignore
            channels=["IN_APP", "EMAIL"],
            metadata={"product_id": product_id},
        )
    log_user_action(
        user=None,
        action_type=AuditLog.ActionType.SYSTEM,
        content_object=product,
        object_repr=product.name,
        priority=AuditLog.Priority.MEDIUM,
        metadata={"task": "notify_admins_on_new_product", "product_id": product_id},
    )


@shared_task
def notify_admins_on_low_stock(inventory_id):
    inventory = Inventory.objects.get(id=inventory_id)  # type: ignore
    admins = User.objects.filter(is_staff=True)
    for admin in admins:
        send_notification(
            user=admin,
            message=f"Low stock alert: {inventory.variant.product.name} - {inventory.variant.name} (Quantity: {inventory.quantity})",
            category="inventory",
            priority=AuditLog.Priority.HIGH,  # type: ignore
            channels=["IN_APP", "EMAIL"],
            metadata={"inventory_id": inventory_id, "quantity": inventory.quantity},
        )
    log_user_action(
        user=None,
        action_type=AuditLog.ActionType.SYSTEM,
        content_object=inventory,
        object_repr=f"{inventory.variant.product.name} - {inventory.variant.name}",
        priority=AuditLog.Priority.HIGH,
        metadata={"task": "notify_admins_on_low_stock", "inventory_id": inventory_id},
    )
