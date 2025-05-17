from rest_framework import serializers

from apps.products.models import ProductVariant
from apps.products.serializers import ProductVariantSerializer

from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    variant = ProductVariantSerializer(read_only=True)
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(),  # type:ignore
        source="variant",
        write_only=True,
    )

    class Meta:
        model = CartItem
        fields = ["id", "variant", "variant_id", "quantity", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Cart
        fields = [
            "id",
            "user",
            "session_id",
            "items",
            "created_at",
            "updated_at",
            "metadata",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at", "metadata"]
