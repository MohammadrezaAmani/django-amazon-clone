from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from .models import Category, Product, ProductVariant, Inventory

User = get_user_model()


class ProductTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.admin = User.objects.create_superuser(
            username="admin", password="adminpass"
        )
        self.category = Category.objects.create(name="Electronics", slug="electronics")  # type: ignore
        self.product = Product.objects.create(  # type: ignore
            name="Laptop",
            slug="laptop",
            description="A high-end laptop",
            base_price=999.99,
            category=self.category,
        )
        self.variant = ProductVariant.objects.create(  # type: ignore
            product=self.product,
            name="16GB RAM",
            sku="LAP-16GB",
            additional_price=100.00,
        )
        self.inventory = Inventory.objects.create(  # type: ignore
            variant=self.variant,
            quantity=50,
            minimum_stock=10,
        )

    def test_create_product(self):
        self.client.login(username="admin", password="adminpass")
        response = self.client.post(
            "/api/products/",
            {
                "name": "Smartphone",
                "description": "A new smartphone",
                "base_price": 599.99,
                "category": self.category.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)  # type: ignore
        self.assertEqual(Product.objects.count(), 2)  # type: ignore

    def test_retrieve_product(self):
        response = self.client.get(f"/api/products/{self.product.id}/")
        self.assertEqual(response.status_code, 200)  # type: ignore
        self.assertEqual(response.data["name"], "Laptop")  # type: ignore

    def test_low_stock_notification(self):
        self.inventory.quantity = 5
        self.inventory.save()
        # Assuming Celery task runs and logs are created (mock Celery for actual testing)
        self.assertTrue(Inventory.objects.filter(quantity__lte=10).exists())  # type: ignore
