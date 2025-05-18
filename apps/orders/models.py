from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.payment.models import Payment
from apps.products.models import ProductVariant

User = get_user_model()


class Discount(models.Model):
    DISCOUNT_TYPE_CHOICES = (
        ("fixed", _("Fixed Amount")),
        ("percentage", _("Percentage")),
    )
    name = models.CharField(max_length=100, help_text=_("Name of the discount"))
    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        help_text=_("Type of discount"),
    )
    value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Discount amount or percentage"),
    )
    is_active = models.BooleanField(
        default=True,  # type: ignore
        help_text=_("Is the discount active?"),  # type: ignore
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("discount")
        verbose_name_plural = _("discounts")
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.name} : {self.value})"

    def clean(self):
        if self.discount_type == "percentage" and (self.value < 0 or self.value > 100):
            raise ValidationError(_("Percentage discount must be between 0 and 100."))
        if self.discount_type == "fixed" and self.value < 0:
            raise ValidationError(_("Fixed discount cannot be negative."))


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True, help_text=_("Coupon code"))
    discount = models.ForeignKey(
        Discount,
        on_delete=models.CASCADE,
        related_name="coupons",
        help_text=_("Associated discount"),
    )
    valid_from = models.DateTimeField(help_text=_("Start date of coupon validity"))
    valid_until = models.DateTimeField(help_text=_("End date of coupon validity"))
    max_usage = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_("Maximum number of uses (null for unlimited)"),  # type: ignore
    )
    usage_count = models.PositiveIntegerField(
        default=0,  # type: ignore
        help_text=_("Number of times the coupon has been used"),  # type: ignore
    )
    min_order_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Minimum order amount to apply coupon"),
    )
    one_per_user = models.BooleanField(
        default=False,  # type: ignore
        help_text=_("Limit to one use per user"),  # type: ignore
    )
    applicable_categories = models.ManyToManyField(
        "products.Category",
        blank=True,
        help_text=_("Categories this coupon applies to (empty for all)"),
    )
    is_active = models.BooleanField(default=True, help_text=_("Is the coupon active?"))  # type: ignore
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("coupon")
        verbose_name_plural = _("coupons")
        indexes = [
            models.Index(fields=["code", "is_active"]),
            models.Index(fields=["valid_from", "valid_until"]),
        ]

    def __str__(self):  # type: ignore
        return self.code

    def clean(self):
        if self.valid_from >= self.valid_until:
            raise ValidationError(_("Valid until must be after valid from."))
        if self.min_order_amount and self.min_order_amount < 0:
            raise ValidationError(_("Minimum order amount cannot be negative."))

    def is_valid(self, order_amount, user, order_items):
        """
        Validate if the coupon is applicable for the given order.
        """
        now = timezone.now()
        if not self.is_active:
            return False, _("Coupon is not active.")
        if now < self.valid_from or now > self.valid_until:
            return False, _("Coupon is not valid at this time.")
        if self.max_usage and self.usage_count >= self.max_usage:
            return False, _("Coupon has reached maximum usage.")
        if self.min_order_amount and order_amount < self.min_order_amount:
            return False, _("Order amount is below minimum required.")
        if (
            self.one_per_user
            and CouponUsage.objects.filter(coupon=self, user=user).exists()  # type: ignore
        ):
            return False, _("Coupon can only be used once per user.")
        if self.applicable_categories.exists():  # type: ignore
            order_categories = {item.variant.product.category for item in order_items}
            if not any(
                cat in self.applicable_categories.all()  # type: ignore
                for cat in order_categories
            ):
                return False, _("Coupon is not applicable to any items in the order.")
        return True, ""


class CouponUsage(models.Model):
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE,
        related_name="usages",
        help_text=_("Associated coupon"),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="coupon_usages",
        help_text=_("User who used the coupon"),
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="coupon_usages",
        help_text=_("Order the coupon was applied to"),
    )
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("coupon usage")
        verbose_name_plural = _("coupon usages")
        indexes = [
            models.Index(fields=["coupon", "user"]),
            models.Index(fields=["applied_at"]),
        ]

    def __str__(self):
        return f"Coupon {self.coupon.code} used by {self.user} on order {self.order.id}"  # type: ignore


User = get_user_model()


class Order(models.Model):
    STATUS_CHOICES = (
        ("pending", _("Pending")),
        ("processing", _("Processing")),
        ("shipped", _("Shipped")),
        ("delivered", _("Delivered")),
        ("cancelled", _("Cancelled")),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="orders",
        help_text=_("User who placed the order"),
    )
    payment = models.OneToOneField(
        Payment,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="order",
        help_text=_("Associated payment for the order"),
    )
    coupon = models.ForeignKey(
        Coupon,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
        help_text=_("Applied coupon, if any"),
    )
    subtotal_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text=_("Subtotal amount before taxes and shipping"),
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text=_("Tax amount for the order"),
    )
    shipping_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text=_("Shipping cost for the order"),
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text=_("Discount amount applied to the order"),
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text=_("Total amount including taxes, shipping, and discounts"),
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        help_text=_("Current status of the order"),
    )
    shipping_address = models.TextField(help_text=_("Shipping address for delivery"))
    billing_address = models.TextField(
        blank=True,
        help_text=_("Billing address, if different from shipping"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Additional metadata (e.g., payment method, delivery notes)"),
    )

    class Meta:
        verbose_name = _("order")
        verbose_name_plural = _("orders")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["payment"]),
        ]

    def __str__(self):
        return f"Order {self.id} by {self.user}"  # type: ignore

    def calculate_totals(self):
        """
        Calculate subtotal, taxes, shipping, discounts, and total amount.
        """
        subtotal = sum(item.price_at_time * item.quantity for item in self.items.all())  # type: ignore
        discount = 0
        if self.coupon and self.coupon.discount:  # type: ignore
            discount = (
                self.coupon.discount.value  # type: ignore
                if self.coupon.discount.discount_type == "fixed"  # type: ignore
                else (subtotal * self.coupon.discount.value / 100)  # type: ignore
            )
        tax = subtotal * 0.09  # Example: 9% tax rate
        shipping = 10.00 if subtotal < 100 else 0.00  # Example: Free shipping over $100
        total = subtotal + tax + shipping - discount

        self.subtotal_amount = round(subtotal, 2)
        self.tax_amount = round(tax, 2)
        self.shipping_amount = round(shipping, 2)
        self.discount_amount = round(discount, 2)
        self.total_amount = round(total, 2)
        self.save()


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        help_text=_("Parent order"),
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        help_text=_("Product variant ordered"),
    )
    quantity = models.PositiveIntegerField(help_text=_("Quantity ordered"))  # type: ignore
    price_at_time = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Price of the variant at the time of order"),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("order item")
        verbose_name_plural = _("order items")
        indexes = [
            models.Index(fields=["order", "variant"]),
        ]

    def __str__(self):
        return f"{self.quantity} x {self.variant} in order {self.order.id}"  # type: ignore


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="status_history",
        help_text=_("Parent order"),
    )
    status = models.CharField(
        max_length=20,
        choices=Order.STATUS_CHOICES,
        help_text=_("Status at this point"),
    )
    note = models.TextField(
        blank=True, help_text=_("Additional notes for status change")
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("order status history")
        verbose_name_plural = _("order status histories")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order", "status"]),
        ]

    def __str__(self):
        return f"Status {self.status} for order {self.order.id}"  # type: ignore
