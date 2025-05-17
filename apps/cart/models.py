from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.products.models import ProductVariant

User = get_user_model()


class Cart(models.Model):
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="carts",
        help_text=_("User associated with the cart, if authenticated"),
    )
    session_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text=_("Session ID for guest users"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Additional metadata (e.g., cart source, device info)"),
    )

    class Meta:
        verbose_name = _("cart")
        verbose_name_plural = _("carts")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Cart for {self.user or self.session_id}"


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
        help_text=_("Parent cart"),
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        help_text=_("Product variant in cart"),
    )
    quantity = models.PositiveIntegerField(
        default=1,  # type: ignore
        help_text=_("Quantity of the item"),  # type: ignore
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("cart item")
        verbose_name_plural = _("cart items")
        unique_together = ["cart", "variant"]

    def __str__(self):
        return f"{self.quantity} x {self.variant} in cart"
