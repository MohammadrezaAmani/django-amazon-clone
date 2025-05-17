from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from apps.audit_log.models import AuditLog
from apps.audit_log.utils import log_user_action

from .models import Cart
from .serializers import CartSerializer


class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()  # type: ignore
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["user", "session_id"]
    ordering_fields = ["created_at"]

    def perform_create(self, serializer):
        cart = serializer.save(
            user=self.request.user if self.request.user.is_authenticated else None
        )
        log_user_action(
            request=self.request,
            user=self.request.user if self.request.user.is_authenticated else None,
            action_type=AuditLog.ActionType.CREATE,
            content_object=cart,
            object_repr=f"Cart for {cart.user or cart.session_id}",
            priority=AuditLog.Priority.LOW,
            notify=True,
            metadata={"cart_id": cart.id},
        )

    def perform_update(self, serializer):
        cart = serializer.save()
        log_user_action(
            request=self.request,
            user=self.request.user,
            action_type=AuditLog.ActionType.UPDATE,
            content_object=cart,
            object_repr=f"Cart for {cart.user or cart.session_id}",
            priority=AuditLog.Priority.LOW,
            metadata={"cart_id": cart.id},
        )

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Cart.objects.all()  # type: ignore
        return Cart.objects.filter(user=user) | Cart.objects.filter(  # type: ignore
            session_id=self.request.session.session_key
        )
