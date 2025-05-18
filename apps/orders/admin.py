from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Coupon, CouponUsage, Discount, Order, OrderItem, OrderStatusHistory


# Define the inline classes
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1  # Number of empty forms to display
    readonly_fields = ("price_at_time", "created_at")
    fields = ("variant", "quantity", "price_at_time", "created_at")


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 1  # Number of empty forms to display
    readonly_fields = ("created_at",)
    fields = ("status", "created_at")


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "discount_type",
        "value",
        "is_active",
        "created_at",
        "updated_at",
    )
    list_filter = ("discount_type", "is_active", "created_at")
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "discount",
        "valid_from",
        "valid_until",
        "usage_count",
        "max_usage",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "valid_from", "valid_until")
    search_fields = ("code", "discount__name")
    readonly_fields = ("created_at", "updated_at", "usage_count")
    ordering = ("-created_at",)


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ("coupon", "user", "order", "applied_at")
    list_filter = ("applied_at",)
    search_fields = ("coupon__code", "user__username", "order__id")
    readonly_fields = ("applied_at",)
    ordering = ("-applied_at",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "payment_status",
        "total_amount",
        "status",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "created_at", "payment__status")
    search_fields = (
        "user__username",
        "shipping_address",
        "payment__transaction_id",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "metadata",
        "subtotal_amount",
        "tax_amount",
        "shipping_amount",
        "discount_amount",
        "total_amount",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "user",
                    "payment",
                    "coupon",
                    "status",
                    "shipping_address",
                    "billing_address",
                ),
            },
        ),
        (
            _("Financial Details"),
            {
                "fields": (
                    "subtotal_amount",
                    "tax_amount",
                    "shipping_amount",
                    "discount_amount",
                    "total_amount",
                ),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("metadata", "created_at", "updated_at"),
            },
        ),
    )
    inlines = [OrderItemInline, OrderStatusHistoryInline]

    def payment_status(self, obj):
        return obj.payment.status if obj.payment else "-"

    payment_status.short_description = _("Payment Status")  # type: ignore


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "variant", "quantity", "price_at_time", "created_at")
    list_filter = ("order__status", "created_at")
    search_fields = ("variant__product__name", "variant__name")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("order", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("order__id",)
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
