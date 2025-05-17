# from common.models import Location
import uuid
from io import BytesIO

import qrcode
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from django.db import models
from django.utils.translation import gettext_lazy as _
from encrypted_model_fields.fields import (
    EncryptedCharField,
)

User = get_user_model()


class PaymentGatewayConfig(models.Model):
    """Configuration for payment gateways."""

    name = models.CharField(max_length=100, unique=True)
    merchant_id = EncryptedCharField(max_length=255)
    api_key = EncryptedCharField(max_length=255)
    callback_url = models.URLField()
    is_active = models.BooleanField(default=True)  # type: ignore
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("payment gateway config")
        verbose_name_plural = _("payment gateway configs")

    def __str__(self):  # type: ignore
        return self.name


class Payment(models.Model):
    """Main payment model."""

    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        SUCCESS = "SUCCESS", _("Success")
        FAILED = "FAILED", _("Failed")
        REFUNDED = "REFUNDED", _("Refunded")

    class Currency(models.TextChoices):
        IRR = "IRR", _("Rial")
        USD = "USD", _("US Dollar")
        EUR = "EUR", _("Euro")

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    gateway = models.ForeignKey(
        PaymentGatewayConfig,
        on_delete=models.SET_NULL,
        null=True,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.IRR,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    transaction_id = models.CharField(max_length=100, unique=True, blank=True)
    token = models.CharField(max_length=255, blank=True)
    qr_code = models.ImageField(upload_to="payment/qrcodes/", blank=True)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")
    # billing_location = models.ForeignKey(
    #     Location,
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     related_name="payments",
    # )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("payment")
        verbose_name_plural = _("payments")
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["transaction_id"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.amount} {self.currency}"

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = str(uuid.uuid4())[:16]
        if not self.qr_code and self.token:
            qr = qrcode.QRCode()
            qr.add_data(self.token)  # type: ignore
            qr.make(fit=True)
            img = qr.make_image(fill="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")  # type: ignore
            self.qr_code.save(f"qr_{self.transaction_id}.png", File(buffer), save=False)
        super().save(*args, **kwargs)


class Transaction(models.Model):
    """Tracks payment transactions."""

    class Status(models.TextChoices):
        INITIATED = "INITIATED", _("Initiated")
        COMPLETED = "COMPLETED", _("Completed")
        FAILED = "FAILED", _("Failed")

    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.INITIATED,
    )
    bank_response = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("transaction")
        verbose_name_plural = _("transactions")
        indexes = [
            models.Index(fields=["payment", "status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Transaction for {self.payment} - {self.status}"


class Refund(models.Model):
    """Manages refund requests."""

    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="refunds",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="refunds",
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", _("Pending")),
            ("APPROVED", _("Approved")),
            ("REJECTED", _("Rejected")),
        ],
        default="PENDING",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("refund")
        verbose_name_plural = _("refunds")
        indexes = [
            models.Index(fields=["payment", "status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Refund for {self.payment} - {self.amount}"
