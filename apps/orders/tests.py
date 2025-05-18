from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.orders.models import Order, OrderItem
from apps.products.models import Category, Product, ProductVariant

from .models import Coupon, CouponUsage, Discount

User = get_user_model()


class DiscountTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="testpass")  # type: ignore
        self.admin = User.objects.create_superuser(  # type: ignore
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
        self.discount = Discount.objects.create(  # type: ignore
            name="Summer Sale",
            discount_type="percentage",
            value=20.00,
            is_active=True,
        )
        self.coupon = Coupon.objects.create(  # type: ignore
            code="SUMMER20",
            discount=self.discount,
            valid_from=timezone.now(),
            valid_until=timezone.now() + timezone.timedelta(days=30),
            max_usage=100,
            min_order_amount=50.00,
            one_per_user=True,
            is_active=True,
        )
        self.coupon.applicable_categories.add(self.category)
        self.order = Order.objects.create(  # type: ignore
            user=self.user,
            subtotal_amount=100.00,
            total_amount=100.00,
            shipping_address="123 Test St",
            coupon=self.coupon,
        )
        self.order_item = OrderItem.objects.create(  # type: ignore
            order=self.order,
            variant=self.variant,
            quantity=1,
            price_at_time=100.00,
        )
        self.user_token = str(RefreshToken.for_user(self.user).access_token)
        self.admin_token = str(RefreshToken.for_user(self.admin).access_token)

    def test_create_discount_invalid_percentage(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        response = self.client.post(
            "/api/discounts/",
            {
                "name": "Invalid Sale",
                "discount_type": "percentage",
                "value": 150.00,
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)  # type: ignore
        self.assertIn(
            "Percentage discount must be between 0 and 100",
            str(response.data),  # type: ignore
        )

    def test_create_coupon_invalid_dates(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        response = self.client.post(
            "/api/coupons/",
            {
                "code": "WINTER10",
                "discount_id": self.discount.id,
                "valid_from": timezone.now() + timezone.timedelta(days=30),
                "valid_until": timezone.now(),
                "max_usage": 50,
                "min_order_amount": 30.00,
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)  # type: ignore
        self.assertIn("Valid until must be after valid from", str(response.data))  # type: ignore

    def test_apply_coupon_to_order(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token}")
        new_order = Order.objects.create(  # type: ignore
            user=self.user,
            subtotal_amount=100.00,
            total_amount=100.00,
            shipping_address="123 Test St",
        )
        OrderItem.objects.create(  # type: ignore
            order=new_order,
            variant=self.variant,
            quantity=1,
            price_at_time=100.00,
        )
        response = self.client.patch(
            f"/api/orders/{new_order.id}/",
            {"coupon_id": self.coupon.id},
            format="json",
        )
        self.assertEqual(response.status_code, 200)  # type: ignore
        self.assertEqual(CouponUsage.objects.count(), 2)  # type: ignore
        self.assertEqual(Coupon.objects.get(id=self.coupon.id).usage_count, 2)  # type: ignore

    def test_coupon_one_per_user(self):
        self.coupon.one_per_user = True
        self.coupon.save()
        is_valid, error = self.coupon.is_valid(
            order_amount=100.00, user=self.user, order_items=self.order.items.all()
        )
        self.assertFalse(is_valid)
        self.assertEqual(error, "Coupon can only be used once per user.")

    def test_coupon_applicable_categories(self):
        other_category = Category.objects.create(name="Books", slug="books")  # type: ignore
        self.coupon.applicable_categories.clear()
        self.coupon.applicable_categories.add(other_category)
        self.coupon.save()
        is_valid, error = self.coupon.is_valid(
            order_amount=100.00,
            user=User.objects.create_user(username="newuser", password="newpass"),  # type: ignore
            order_items=self.order.items.all(),
        )
        self.assertFalse(is_valid)
        self.assertEqual(error, "Coupon is not applicable to any items in the order.")
