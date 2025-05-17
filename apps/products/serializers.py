from rest_framework import serializers

from .models import (
    Category,
    Inventory,
    Product,
    ProductAttribute,
    ProductImage,
    ProductVariant,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "parent",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "is_primary", "created_at"]
        read_only_fields = ["id", "created_at"]


class ProductAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttribute
        fields = ["id", "name", "value", "created_at"]
        read_only_fields = ["id", "created_at"]


class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = ["id", "quantity", "minimum_stock", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProductVariantSerializer(serializers.ModelSerializer):
    inventory = InventorySerializer(read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "name",
            "sku",
            "additional_price",
            "inventory",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()
    variants = ProductVariantSerializer(many=True, read_only=True)
    attributes = ProductAttributeSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "base_price",
            "category",
            "is_active",
            "variants",
            "attributes",
            "images",
            "created_at",
            "updated_at",
            "metadata",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at", "metadata"]
