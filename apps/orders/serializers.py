from rest_framework import serializers

from apps.payment.serializers import PaymentSerializer
from apps.products.models import Category, ProductVariant
from apps.products.serializers import ProductVariantSerializer

from .models import Coupon, CouponUsage, Discount, Order, OrderItem, OrderStatusHistory


class DiscountSerializer(serializers.ModelSerializer):
    discount_type_display = serializers.CharField(
        source="get_discount_type_display", read_only=True
    )

    class Meta:
        model = Discount
        fields = [
            "id",
            "name",
            "discount_type",
            "discount_type_display",
            "value",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CouponSerializer(serializers.ModelSerializer):
    discount = DiscountSerializer(read_only=True)
    discount_id = serializers.PrimaryKeyRelatedField(
        queryset=Discount.objects.all(),  # type: ignore
        source="discount",
        write_only=True,
    )
    applicable_categories = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),  # type: ignore
        many=True,
        required=False,
    )

    class Meta:
        model = Coupon
        fields = [
            "id",
            "code",
            "discount",
            "discount_id",
            "valid_from",
            "valid_until",
            "max_usage",
            "usage_count",
            "min_order_amount",
            "one_per_user",
            "applicable_categories",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "usage_count", "created_at", "updated_at"]


class CouponUsageSerializer(serializers.ModelSerializer):
    coupon = CouponSerializer(read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    order = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = CouponUsage
        fields = ["id", "coupon", "user", "order", "applied_at"]
        read_only_fields = ["id", "coupon", "user", "order", "applied_at"]


class OrderItemSerializer(serializers.ModelSerializer):
    variant = ProductVariantSerializer(read_only=True)
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(),  # type: ignore
        source="variant",
        write_only=True,
    )

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "variant",
            "variant_id",
            "quantity",
            "price_at_time",
            "created_at",
        ]
        read_only_fields = ["id", "price_at_time", "created_at"]


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = ["id", "status", "note", "created_at"]
        read_only_fields = ["id", "created_at"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    payment = PaymentSerializer(read_only=True)
    coupon = CouponSerializer(read_only=True)
    coupon_id = serializers.PrimaryKeyRelatedField(
        queryset=Coupon.objects.all(),  # type: ignore
        source="coupon",
        write_only=True,
        allow_null=True,
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "payment",
            "coupon",
            "coupon_id",
            "subtotal_amount",
            "tax_amount",
            "shipping_amount",
            "discount_amount",
            "total_amount",
            "status",
            "shipping_address",
            "billing_address",
            "items",
            "status_history",
            "created_at",
            "updated_at",
            "metadata",
        ]
        read_only_fields = [
            "id",
            "user",
            "payment",
            "subtotal_amount",
            "tax_amount",
            "shipping_amount",
            "discount_amount",
            "total_amount",
            "created_at",
            "updated_at",
            "metadata",
        ]

    def validate_coupon_id(self, value):
        if value:
            # Calculate subtotal from items in the request (if provided) or existing order
            items = self.context["request"].data.get("items", [])
            subtotal = (
                sum(
                    item["quantity"]
                    * ProductVariant.objects.get(  # type: ignore
                        id=item["variant_id"]
                    ).product.base_price
                    for item in items
                )
                if items
                else (self.instance.subtotal_amount if self.instance else 0)
            )
            is_valid, error = value.is_valid(
                order_amount=subtotal,
                user=self.context["request"].user,
                order_items=self.instance.items.all() if self.instance else [],
            )
            if not is_valid:
                raise serializers.ValidationError(error)
        return value
