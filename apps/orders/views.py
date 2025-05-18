from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, serializers, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from apps.audit_log.models import AuditLog
from apps.audit_log.utils import log_user_action
from apps.cart.models import Cart
from apps.payment.models import Payment, PaymentGatewayConfig
from apps.payment.utils import initiate_payment

from .models import Coupon, CouponUsage, Discount, Order, OrderItem
from .serializers import (
    CouponSerializer,
    CouponUsageSerializer,
    DiscountSerializer,
    OrderSerializer,
)


class DiscountViewSet(viewsets.ModelViewSet):
    queryset = Discount.objects.all()  # type: ignore
    serializer_class = DiscountSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["discount_type", "is_active"]
    ordering_fields = ["created_at", "value"]

    def perform_create(self, serializer):
        discount = serializer.save()
        log_user_action(
            request=self.request,
            user=self.request.user,
            action_type=AuditLog.ActionType.CREATE,
            content_object=discount,
            object_repr=f"Discount {discount.name}",
            priority=AuditLog.Priority.MEDIUM,
            notify=True,
            metadata={"discount_id": discount.id},
        )

    def perform_update(self, serializer):
        discount = serializer.save()
        log_user_action(
            request=self.request,
            user=self.request.user,
            action_type=AuditLog.ActionType.UPDATE,
            content_object=discount,
            object_repr=f"Discount {discount.name}",
            priority=AuditLog.Priority.MEDIUM,
            metadata={"discount_id": discount.id},
        )


class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()  # type: ignore
    serializer_class = CouponSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_fields = ["is_active", "valid_from", "valid_until"]
    ordering_fields = ["created_at", "valid_until"]
    search_fields = ["code"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        coupon = serializer.save()
        log_user_action(
            request=self.request,
            user=self.request.user,
            action_type=AuditLog.ActionType.CREATE,
            content_object=coupon,
            object_repr=f"Coupon {coupon.code}",
            priority=AuditLog.Priority.MEDIUM,
            notify=True,
            metadata={"coupon_id": coupon.id},
        )

    def perform_update(self, serializer):
        coupon = serializer.save()
        log_user_action(
            request=self.request,
            user=self.request.user,
            action_type=AuditLog.ActionType.UPDATE,
            content_object=coupon,
            object_repr=f"Coupon {coupon.code}",
            priority=AuditLog.Priority.MEDIUM,
            metadata={"coupon_id": coupon.id},
        )


class CouponUsageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CouponUsage.objects.all()  # type: ignore
    serializer_class = CouponUsageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["coupon", "user"]
    ordering_fields = ["applied_at"]

    def get_queryset(self):
        if self.request.user.is_staff:
            return CouponUsage.objects.all()  # type: ignore
        return CouponUsage.objects.filter(user=self.request.user)  # type: ignore


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()  # type: ignore
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_fields = ["user", "status", "created_at", "payment__status"]
    ordering_fields = ["created_at", "total_amount", "status"]
    search_fields = ["shipping_address", "billing_address"]

    def perform_create(self, serializer):
        cart = Cart.objects.filter(user=self.request.user).first()  # type: ignore
        if not cart or not cart.items.exists():
            raise serializers.ValidationError(_("Cart is empty"))  # type: ignore

        order = serializer.save(user=self.request.user)

        for item in cart.items.all():
            OrderItem.objects.create(  # type: ignore
                order=order,
                variant=item.variant,
                quantity=item.quantity,
                price_at_time=item.variant.product.base_price
                + item.variant.additional_price,
            )

        order.calculate_totals()

        payment = Payment.objects.create(  # type: ignore
            user=self.request.user,
            gateway=PaymentGatewayConfig.objects.filter(is_active=True).first(),  # type: ignore
            amount=order.total_amount,
            currency="IRR",
            content_object=order,
        )
        order.payment = payment
        order.save()

        initiate_payment(payment, self.request)

        cart.delete()

        log_user_action(
            request=self.request,
            user=self.request.user,
            action_type=AuditLog.ActionType.CREATE,
            content_object=order,
            object_repr=f"Order {order.id}",
            priority=AuditLog.Priority.MEDIUM,
            notify=True,
            metadata={"order_id": order.id, "payment_id": payment.id},
        )

    def perform_update(self, serializer):
        order = serializer.save()
        log_user_action(
            request=self.request,
            user=self.request.user,
            action_type=AuditLog.ActionType.UPDATE,
            content_object=order,
            object_repr=f"Order {order.id}",
            priority=AuditLog.Priority.MEDIUM,
            metadata={"order_id": order.id},
        )

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()  # type: ignore
        return Order.objects.filter(user=user)  # type: ignore
