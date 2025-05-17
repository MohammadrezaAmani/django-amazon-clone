from unittest.mock import patch

import pytest
from azbankgateways import models as bank_models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import Point
from payment.models import Payment, PaymentGatewayConfig, Transaction
from rest_framework import status
from rest_framework.test import APIClient

from apps.common.models import Location
from apps.notifications.models import Notification

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser",
        email="testuser@example.com",
        password="testpass123",
        is_verified=True,
        phone_number="+989112221234",
    )


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass123",
    )


@pytest.fixture
def gateway(db):
    return PaymentGatewayConfig.objects.create(  # type: ignore
        name="SEP",
        merchant_id="test_merchant",
        api_key="test_api_key",
        callback_url="http://localhost:8000/payment/callback/",
    )


@pytest.fixture
def location(db):
    return Location.objects.create(  # type: ignore
        name="Tehran",
        location_type="CITY",
        country="IR",
        coordinates=Point(51.3890, 35.6892),
    )


@pytest.fixture
def notification(user):
    return Notification.objects.create(  # type: ignore
        user=user,
        message="Test notification",
        channels=["IN_APP"],
        priority="MED",
    )


@pytest.mark.django_db
class TestPaymentCRUD:
    def test_create_payment(self, api_client, user, gateway, location, notification):
        api_client.force_authenticate(user=user)
        data = {
            "gateway": gateway.id,
            "amount": 100000,
            "currency": "IRR",
            "content_type": ContentType.objects.get_for_model(Notification).id,
            "object_id": notification.id,
            # "billing_location": location.id,
            "metadata": {"order_id": "123"},
        }
        with patch(
            "azbankgateways.bankfactories.BankFactory.auto_create"
        ) as mock_factory:
            mock_bank = mock_factory.return_value
            mock_bank.get_gateway.return_value = {
                "url": "https://bank.test/pay",
                "method": "POST",
                "params": {"token": "test_token"},
            }
            mock_bank.ready.return_value = bank_models.Bank(
                tracking_code="test_tracking_code", token="test_token", bank_type="SEP"
            )
            response = api_client.post("/payment/api/payments/", data)
        assert response.status_code == status.HTTP_201_CREATED
        payment = Payment.objects.get()  # type: ignore
        assert payment.user == user
        assert payment.amount == 100000
        assert payment.currency == "IRR"
        assert payment.transaction_id == "test_tracking_code"
        assert payment.qr_code

    def test_go_to_gateway(self, api_client, user, gateway, location, notification):
        api_client.force_authenticate(user=user)
        data = {
            "gateway": gateway.id,
            "amount": 100000,
            "currency": "IRR",
            "content_type": ContentType.objects.get_for_model(Notification).id,
            "object_id": notification.id,
            # "billing_location": location.id,
        }
        with patch(
            "azbankgateways.bankfactories.BankFactory.auto_create"
        ) as mock_factory:
            mock_bank = mock_factory.return_value
            mock_bank.get_gateway.return_value = {
                "url": "https://bank.test/pay",
                "method": "POST",
                "params": {"token": "test_token"},
            }
            mock_bank.ready.return_value = bank_models.Bank(
                tracking_code="test_tracking_code", token="test_token", bank_type="SEP"
            )
            response = api_client.post("/payment/go-to-gateway/", data)
        assert response.status_code == 200
        assert "در حال اتصال به درگاه پرداخت" in response.content

    def test_payment_callback_success(self, api_client, user, gateway):
        payment = Payment.objects.create(  # type: ignore
            user=user,
            gateway=gateway,
            amount=50000,
            currency="IRR",
            status="PENDING",
            token="test_token",
            transaction_id="test_tracking_code",
        )
        bank_models.Bank.objects.create(
            tracking_code="test_tracking_code",
            token="test_token",
            bank_type="SEP",
            is_success=True,
            status="COMPLETE",
        )
        with patch("azbankgateways.bankfactories.BankFactory.create") as mock_factory:
            mock_bank = mock_factory.return_value
            mock_bank.verify.return_value = None
            response = api_client.get("/payment/callback/?tc=test_tracking_code")
        assert response.status_code == 302
        payment.refresh_from_db()
        assert payment.status == "SUCCESS"
        assert Transaction.objects.filter(payment=payment, status="COMPLETED").exists()  # type: ignore

    def test_payment_callback_failed(self, api_client, user, gateway):
        payment = Payment.objects.create(  # type: ignore
            user=user,
            gateway=gateway,
            amount=50000,
            currency="IRR",
            status="PENDING",
            token="test_token",
            transaction_id="test_tracking_code",
        )
        bank_models.Bank.objects.create(
            tracking_code="test_tracking_code",
            token="test_token",
            bank_type="SEP",
            is_success=False,
            status="CANCEL_BY_USER",
        )
        with patch("azbankgateways.bankfactories.BankFactory.create") as mock_factory:
            mock_bank = mock_factory.return_value
            mock_bank.verify.return_value = None
            response = api_client.get("/payment/callback/?tc=test_tracking_code")
        assert response.status_code == 302
        payment.refresh_from_db()
        assert payment.status == "FAILED"
        assert Transaction.objects.filter(payment=payment, status="FAILED").exists()  # type: ignore
