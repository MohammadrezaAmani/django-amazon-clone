from celery import shared_task
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from apps.audit_log.models import AuditLog
from apps.audit_log.utils import log_user_action
from apps.notifications.utils import send_notification
from apps.payment.models import Payment

from .models import Order, OrderStatusHistory
from .tasks import notify_user_on_order_status_change

User = get_user_model()


@shared_task
def notify_user_on_coupon_usage(order_id):
    order = Order.objects.get(id=order_id)  # type: ignore
    if order.coupon:
        send_notification(
            user=order.user,
            message=f"Coupon {order.coupon.code} applied to your order {order.id} for a {order.discount_amount} discount.",
            category="discount",
            priority=AuditLog.Priority.MEDIUM,  # type: ignore
            channels=["IN_APP", "EMAIL", "WEBSOCKET"],
            metadata={"order_id": order_id, "coupon_code": order.coupon.code},
        )
        log_user_action(
            user=None,
            action_type=AuditLog.ActionType.SYSTEM,
            content_object=order,
            object_repr=f"Order {order.id} with coupon {order.coupon.code}",
            priority=AuditLog.Priority.MEDIUM,
            metadata={"task": "notify_user_on_coupon_usage", "order_id": order_id},
        )


@receiver(post_save, sender=Order)
def create_status_history(sender, instance, created, **kwargs):
    if created:
        OrderStatusHistory.objects.create(  # type: ignore
            order=instance,
            status=instance.status,
            note=_("Initial order status"),  # type: ignore
        )
    else:
        if instance.tracker.has_changed("status"):
            previous_status = instance.tracker.previous("status")
            OrderStatusHistory.objects.create(  # type: ignore
                order=instance,
                status=instance.status,
                note=_(  # type: ignore
                    "Status changed from {} to {}".format(
                        previous_status, instance.status
                    )
                ),
            )
            notify_user_on_order_status_change.delay(instance.id)  # type: ignore


@receiver(post_save, sender=Payment)
def update_order_status_on_payment(sender, instance, **kwargs):
    if instance.order and instance.status in [
        Payment.Status.SUCCESS,
        Payment.Status.FAILED,
        Payment.Status.REFUNDED,
    ]:
        order = instance.order
        new_status = {
            Payment.Status.SUCCESS: "processing",
            Payment.Status.FAILED: "cancelled",
            Payment.Status.REFUNDED: "cancelled",
        }.get(instance.status, order.status)
        if order.status != new_status:
            order.status = new_status
            order.save()
