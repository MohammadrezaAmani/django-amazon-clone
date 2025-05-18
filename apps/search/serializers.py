from rest_framework import serializers

from apps.products.models import Product
from apps.products.serializers import ProductSerializer


class SearchResultSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "slug", "description", "base_price", "category"]
