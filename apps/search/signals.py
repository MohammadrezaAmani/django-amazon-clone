from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.products.models import Product

from .tasks import update_search_index_task


@receiver(post_save, sender=Product)
def trigger_search_index_update(sender, instance, **kwargs):
    """
    Trigger asynchronous update of search index when a product is saved.
    """
    update_search_index_task.delay(instance.id)  # type: ignore
