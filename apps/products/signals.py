from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Inventory, Product
from .tasks import notify_admins_on_low_stock, notify_admins_on_new_product


@receiver(post_save, sender=Product)
def notify_admins_on_new_product_signal(sender, instance, created, **kwargs):
    if created:
        notify_admins_on_new_product.delay(instance.id)  # type: ignore


@receiver(post_save, sender=Inventory)
def check_low_stock(sender, instance, **kwargs):
    if instance.quantity <= instance.minimum_stock:
        notify_admins_on_low_stock.delay(instance.id)  # type: ignore
