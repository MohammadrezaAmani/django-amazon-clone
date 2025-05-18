from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class UserActivity(models.Model):
    ACTIVITY_TYPES = (
        ("view", _("Product View")),
        ("search", _("Search Query")),
        ("order", _("Order Placement")),
        ("coupon", _("Coupon Usage")),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="activities",
        help_text=_("User who performed the activity"),
        null=True,
        blank=True,
    )
    activity_type = models.CharField(
        max_length=20,
        choices=ACTIVITY_TYPES,
        help_text=_("Type of activity"),
    )
    metadata = models.JSONField(
        default=dict,
        help_text=_("Additional details (e.g., product ID, search query)"),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("user activity")
        verbose_name_plural = _("user activities")
        indexes = [
            models.Index(fields=["user", "activity_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.get_activity_type_display()} by {self.user or 'Anonymous'}"  # type: ignore


class SalesReport(models.Model):
    start_date = models.DateTimeField(help_text=_("Start date of the report period"))
    end_date = models.DateTimeField(help_text=_("End date of the report period"))
    total_orders = models.PositiveIntegerField(
        default=0,  # type: ignore
        help_text=_("Total number of orders"),  # type: ignore
    )
    total_revenue = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text=_("Total revenue generated"),
    )
    average_order_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text=_("Average order value"),
    )
    top_products = models.JSONField(
        default=list,
        help_text=_("List of top-selling products"),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("sales report")
        verbose_name_plural = _("sales reports")
        indexes = [
            models.Index(fields=["start_date", "end_date"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Report from {self.start_date} to {self.end_date}"
