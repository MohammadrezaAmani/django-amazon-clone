from django.contrib.auth import get_user_model
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text=_("Category name"))
    slug = models.SlugField(
        max_length=120, unique=True, help_text=_("URL-friendly category identifier")
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
        help_text=_("Parent category for hierarchical structure"),
    )
    is_active = models.BooleanField(
        default=True,  # type: ignore
        help_text=_("Whether the category is active"),  # type: ignore
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):  # type: ignore
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200, help_text=_("Product name"))
    slug = models.SlugField(
        max_length=220, unique=True, help_text=_("URL-friendly product identifier")
    )
    description = models.TextField(
        blank=True, help_text=_("Detailed product description")
    )
    base_price = models.DecimalField(
        max_digits=10, decimal_places=2, help_text=_("Base price of the product")
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="products",
        help_text=_("Product category"),
    )
    is_active = models.BooleanField(
        default=True,  # type: ignore
        help_text=_("Whether the product is active"),  # type: ignore
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Additional metadata (e.g., SEO tags, custom fields)"),
    )

    class Meta:
        verbose_name = _("product")
        verbose_name_plural = _("products")
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):  # type: ignore
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
        help_text=_("Parent product"),
    )
    name = models.CharField(
        max_length=100, help_text=_("Variant name (e.g., 'Red', 'Large')")
    )
    sku = models.CharField(
        max_length=50, unique=True, help_text=_("Stock Keeping Unit")
    )
    additional_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("Additional price for this variant"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("product variant")
        verbose_name_plural = _("product variants")

    def __str__(self):
        return f"{self.product.name} - {self.name}"


class ProductAttribute(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="attributes",
        help_text=_("Parent product"),
    )
    name = models.CharField(
        max_length=100, help_text=_("Attribute name (e.g., 'Material', 'Weight')")
    )
    value = models.CharField(max_length=100, help_text=_("Attribute value"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("product attribute")
        verbose_name_plural = _("product attributes")

    def __str__(self):
        return f"{self.product.name} - {self.name}: {self.value}"


class Inventory(models.Model):
    variant = models.OneToOneField(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="inventory",
        help_text=_("Product variant"),
    )
    quantity = models.PositiveIntegerField(default=0, help_text=_("Available stock"))  # type: ignore
    minimum_stock = models.PositiveIntegerField(
        default=10,  # type: ignore
        help_text=_("Minimum stock threshold for alerts"),  # type: ignore
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("inventory")
        verbose_name_plural = _("inventories")

    def __str__(self):
        return f"Inventory for {self.variant}"


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        help_text=_("Parent product"),
    )
    image = models.ImageField(upload_to="products/", help_text=_("Product image"))
    is_primary = models.BooleanField(
        default=False,  # type: ignore
        help_text=_("Primary image for the product"),  # type: ignore
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("product image")
        verbose_name_plural = _("product images")

    def __str__(self):
        return f"Image for {self.product.name}"
