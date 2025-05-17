from django.contrib import admin

from .models import (
    Category,
    Product,
    ProductVariant,
    ProductAttribute,
    Inventory,
    ProductImage,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "slug")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "category",
        "base_price",
        "is_active",
        "created_at",
        "updated_at",
    )
    list_filter = ("category", "is_active", "created_at")
    search_fields = ("name", "slug", "description")
    readonly_fields = ("created_at", "updated_at", "metadata")
    ordering = ("-created_at",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("product", "name", "sku", "additional_price", "created_at")
    list_filter = ("product__category", "created_at")
    search_fields = ("product__name", "name", "sku")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ("product", "name", "value", "created_at")
    list_filter = ("product__category", "created_at")
    search_fields = ("product__name", "name", "value")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("variant", "quantity", "minimum_stock", "created_at", "updated_at")
    list_filter = ("variant__product__category", "created_at")
    search_fields = ("variant__product__name", "variant__name")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "is_primary", "created_at")
    list_filter = ("product__category", "is_primary", "created_at")
    search_fields = ("product__name",)
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
