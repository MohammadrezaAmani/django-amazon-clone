from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.orders.models import CouponUsage, Order

from .models import UserActivity


@receiver(post_save, sender=Order)
def log_order_activity(sender, instance, created, **kwargs):
    if created:
        UserActivity.objects.create(  # type: ignore
            user=instance.user,
            activity_type="order",
            metadata={
                "order_id": instance.id,
                "total_amount": str(instance.total_amount),
            },
        )


@receiver(post_save, sender=CouponUsage)
def log_coupon_activity(sender, instance, created, **kwargs):
    if created:
        UserActivity.objects.create(  # type: ignore
            user=instance.user,
            activity_type="coupon",
            metadata={
                "coupon_code": instance.coupon.code,
                "order_id": instance.order.id,
            },
        )
