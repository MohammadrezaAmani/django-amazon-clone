from azbankgateways import models as bank_models
from django.conf import settings
from django.shortcuts import redirect, render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from audit_log.models import AuditLog
from audit_log.utils import log_user_action
from notifications.utils import send_notification

from .models import Payment, PaymentGatewayConfig, Refund, Transaction
from .serializers import (
    PaymentGatewayConfigSerializer,
    PaymentSerializer,
    RefundSerializer,
    TransactionSerializer,
)
from .utils import initiate_payment, verify_payment


class PaymentGatewayConfigViewSet(viewsets.ModelViewSet):
    queryset = PaymentGatewayConfig.objects.all()  # type: ignore
    serializer_class = PaymentGatewayConfigSerializer
    permission_classes = [IsAdminUser]


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()  # type: ignore
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["status", "currency", "gateway", "created_at"]
    search_fields = ["transaction_id"]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Payment.objects.all()  # type: ignore
        return Payment.objects.filter(user=self.request.user)  # type: ignore

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = serializer.save(user=self.request.user)
        initiate_payment(payment, request)
        log_user_action(
            request=self.request,
            action_type=AuditLog.ActionType.CREATE,
            content_object=payment,
            priority=AuditLog.Priority.MEDIUM,
        )
        return Response(
            {"transaction_id": payment.transaction_id}, status=status.HTTP_201_CREATED
        )


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Transaction.objects.all()  # type: ignore
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "payment"]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Transaction.objects.all()  # type: ignore
        return Transaction.objects.filter(payment__user=self.request.user)  # type: ignore


class RefundViewSet(viewsets.ModelViewSet):
    queryset = Refund.objects.all()  # type: ignore
    serializer_class = RefundSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "payment"]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Refund.objects.all()  # type: ignore
        return Refund.objects.filter(user=self.request.user)  # type: ignore

    def perform_create(self, serializer):
        refund = serializer.save(user=self.request.user)
        log_user_action(
            request=self.request,
            action_type=AuditLog.ActionType.CREATE,
            content_object=refund,
            priority=AuditLog.Priority.HIGH,
            notify=True,
        )
        send_notification(
            user=self.request.user,
            message=f"درخواست بازگشت وجه برای {refund.amount} ثبت شد.",
            category="payment",
            priority="HIGH",  # type: ignore
            channels=["IN_APP", "WEBSOCKET", "EMAIL"],
            metadata={"refund_id": refund.id},
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def approve(self, request, pk):
        refund = self.get_object()
        refund.status = "APPROVED"
        refund.payment.status = Payment.Status.REFUNDED
        refund.payment.save()
        refund.save()
        log_user_action(
            request=request,
            action_type=AuditLog.ActionType.UPDATE,
            content_object=refund,
            priority=AuditLog.Priority.HIGH,
            notify=True,
        )
        send_notification(
            user=refund.user,
            message=f"درخواست بازگشت وجه برای {refund.amount} تأیید شد.",
            category="payment",
            priority="HIGH",
            channels=["IN_APP", "WEBSOCKET", "EMAIL"],
            metadata={"refund_id": refund.id},
        )
        return Response({"status": "Refund approved"}, status=status.HTTP_200_OK)


class PaymentCallbackSerializer(serializers.Serializer):
    tracking_code = serializers.CharField(
        source=f"{settings.AZ_IRANIAN_BANK_GATEWAYS['TRACKING_CODE_QUERY_PARAM']}"
    )


class PaymentCallbackView(GenericAPIView):
    serializer_class = PaymentCallbackSerializer
    permission_classes = []

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        tracking_code = serializer.validated_data.get(
            settings.AZ_IRANIAN_BANK_GATEWAYS["TRACKING_CODE_QUERY_PARAM"]
        )

        if not tracking_code:
            log_user_action(
                request=request,
                action_type=AuditLog.ActionType.SYSTEM,
                status=AuditLog.Status.FAILED,
                priority=AuditLog.Priority.HIGH,
                error_message="Invalid tracking code",
            )
            return redirect("/payment/failed/")

        try:
            bank_models.Bank.objects.get(tracking_code=tracking_code)
            payment = Payment.objects.get(transaction_id=tracking_code)
        except (bank_models.Bank.DoesNotExist, Payment.DoesNotExist):
            log_user_action(
                request=request,
                action_type=AuditLog.ActionType.SYSTEM,
                status=AuditLog.Status.FAILED,
                priority=AuditLog.Priority.HIGH,
                error_message="Invalid payment or bank record",
            )
            return redirect("/payment/failed/")

        is_success = verify_payment(payment, tracking_code)
        redirect_url = f"/payment/{'success' if is_success else 'failed'}/{payment.transaction_id}/"
        return redirect(redirect_url)


class GoToGatewayView(GenericAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        payment = serializer.save(user=request.user)
        try:
            context = initiate_payment(payment, request)
            return render(request, "redirect_to_bank.html", context=context)
        except Exception as e:
            log_user_action(
                request=request,
                user=payment.user,
                action_type=AuditLog.ActionType.CREATE,
                status=AuditLog.Status.FAILED,
                content_object=payment,
                priority=AuditLog.Priority.HIGH,
                error_message=str(e),
                notify=True,
            )
            return render(request, "redirect_to_bank.html")
