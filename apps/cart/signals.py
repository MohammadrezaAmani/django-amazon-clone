from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CartItem
from .tasks import notify_admins_on_cart_item_added


@receiver(post_save, sender=CartItem)
def notify_admins_on_cart_item_added_signal(sender, instance, created, **kwargs):
    if created:
        notify_admins_on_cart_item_added.delay(instance.id)  # type: ignore
