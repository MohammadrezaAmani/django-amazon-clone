from celery import shared_task
from django.contrib.postgres.search import SearchVector

from apps.products.models import Product

from .models import SearchIndex


@shared_task
def update_search_index_task(product_id):
    """
    Update the search index for a specific product.
    """
    try:
        product = Product.objects.get(id=product_id)  # type: ignore
        # Extract category name safely
        category_name = product.category.name if product.category else ""
        # Create search vector
        search_vector = (
            SearchVector("name", weight="A")
            + SearchVector("description", weight="B")
            + SearchVector("slug", weight="C")
            + SearchVector(
                value=category_name,  # type: ignore
                weight="B",
                config="english",
            )
        )
        SearchIndex.objects.update_or_create(  # type: ignore
            product=product, defaults={"search_vector": search_vector}
        )
    except Product.DoesNotExist:  # type: ignore
        pass  # Handle case where product is deleted


@shared_task
def update_all_search_indexes():
    """
    Update search indexes for all products.
    """
    for product in Product.objects.all():  # type: ignore
        update_search_index_task.delay(product.id)  # type: ignore
