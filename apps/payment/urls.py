from azbankgateways.urls import az_bank_gateways_urls
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    GoToGatewayView,
    PaymentCallbackView,
    PaymentGatewayConfigViewSet,
    PaymentViewSet,
    RefundViewSet,
    TransactionViewSet,
)

router = DefaultRouter()
router.register(r"gateways", PaymentGatewayConfigViewSet, basename="gateway")
router.register(r"payments", PaymentViewSet, basename="payment")
router.register(r"transactions", TransactionViewSet, basename="transaction")
router.register(r"refunds", RefundViewSet, basename="refund")

urlpatterns = [
    path("go-to-gateway/", GoToGatewayView.as_view(), name="go-to-bank-gateway"),
    path("callback/", PaymentCallbackView.as_view(), name="callback"),
    path("bankgateways/", az_bank_gateways_urls()),
]
urlpatterns.extend(router.urls)
