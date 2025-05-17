from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.products.models import Category, Product, ProductVariant

from .models import Cart, CartItem

User = get_user_model()


class CartTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.category = Category.objects.create(name="Electronics", slug="electronics")  # type: ignore
        self.product = Product.objects.create(  # type: ignore
            name="Laptop", slug="laptop", base_price=999.99, category=self.category
        )
        self.variant = ProductVariant.objects.create(  # type: ignore
            product=self.product, name="16GB", sku="LAP-16GB"
        )
        self.cart = Cart.objects.create(user=self.user)  # type: ignore

    def test_create_cart_item(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.post(
            f"/api/cart/{self.cart.id}/items/",
            {"variant_id": self.variant.id, "quantity": 2},
            format="json",
        )
        self.assertEqual(response.status_code, 201)  # type: ignore
        self.assertEqual(CartItem.objects.count(), 1)  # type: ignore
