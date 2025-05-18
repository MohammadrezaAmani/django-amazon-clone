from django.contrib import admin

from .models import SearchIndex


@admin.register(SearchIndex)
class SearchIndexAdmin(admin.ModelAdmin):
    list_display = ("product", "updated_at")
    search_fields = ("product__name", "product__slug")
    readonly_fields = ("search_vector", "updated_at")
    ordering = ("-updated_at",)
