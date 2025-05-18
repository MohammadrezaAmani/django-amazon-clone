from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.orders.models import Order, OrderItem
from apps.products.models import Category, Product, ProductVariant

from .models import SalesReport

User = get_user_model()


class AnalyticsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username="admin", password="adminpass"
        )
        self.category = Category.objects.create(  # type: ignore
            name="Electronics", slug="electronics"
        )
        self.product = Product.objects.create(  # type: ignore
            name="Laptop",
            slug="laptop",
            description="High-end laptop",
            base_price=999.99,
            category=self.category,
        )
        self.variant = ProductVariant.objects.create(  # type: ignore
            product=self.product,
            name="16GB RAM",
            sku="LAP-16GB",
            additional_price=100.00,
        )
        self.order = Order.objects.create(  # type: ignore
            user=self.admin,
            subtotal_amount=1000.00,
            total_amount=1000.00,
            shipping_address="123 Test St",
            status="delivered",
        )
        OrderItem.objects.create(  # type: ignore
            order=self.order,
            variant=self.variant,
            quantity=1,
            price_at_time=1000.00,
        )
        self.admin_token = str(RefreshToken.for_user(self.admin).access_token)

    def test_generate_sales_report(self):
        from .tasks import generate_sales_report

        generate_sales_report()
        report = SalesReport.objects.first()  # type: ignore
        self.assertEqual(report.total_orders, 1)
        self.assertEqual(report.total_revenue, 1000.00)
