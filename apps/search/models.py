from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.utils.translation import gettext_lazy as _


class SearchIndex(models.Model):
    product = models.OneToOneField(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="search_index",
        help_text=_("Associated product"),
    )
    search_vector = SearchVectorField(
        null=True,
        help_text=_("Search vector for full-text search"),  # type: ignore
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("search index")
        verbose_name_plural = _("search indexes")
        indexes = [
            GinIndex(fields=["search_vector"], name="search_vector_idx"),
            models.Index(fields=["product"], name="search_product_idx"),
        ]

    def __str__(self):
        return f"Search index for {self.product.name}"
