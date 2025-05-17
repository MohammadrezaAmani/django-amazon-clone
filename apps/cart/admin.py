from django.contrib import admin

from .models import Cart, CartItem


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "session_id", "created_at", "updated_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "session_id")
    readonly_fields = ("created_at", "updated_at", "metadata")
    ordering = ("-created_at",)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "variant", "quantity", "created_at", "updated_at")
    list_filter = ("cart__user", "created_at")
    search_fields = ("variant__product__name", "variant__name")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
