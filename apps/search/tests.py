from django.test import TestCase
from rest_framework.test import APIClient

from apps.products.models import Category, Product

from .models import SearchIndex


class SearchTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(  # type: ignore
            name="Electronics",
            slug="electronics",
        )
        self.product = Product.objects.create(  # type: ignore
            name="Laptop",
            slug="laptop",
            description="High-end laptop",
            base_price=999.99,
            category=self.category,
        )
        SearchIndex.objects.create(product=self.product)  # type: ignore

    def test_search_product(self):
        response = self.client.get("/api/search/?q=laptop")
        self.assertEqual(response.status_code, 200)  # type: ignore
        self.assertEqual(len(response.data), 1)  # type: ignore
        self.assertEqual(response.data[0]["name"], "Laptop")  # type: ignore
