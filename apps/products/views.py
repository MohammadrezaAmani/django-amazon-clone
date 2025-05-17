from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from apps.audit_log.models import AuditLog
from apps.audit_log.utils import log_user_action

from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(is_active=True)  # type: ignore
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_fields = ["parent", "is_active"]
    ordering_fields = ["name", "created_at"]
    search_fields = ["name", "slug"]

    def perform_create(self, serializer):
        category = serializer.save()
        log_user_action(
            request=self.request,
            user=self.request.user if self.request.user.is_authenticated else None,
            action_type=AuditLog.ActionType.CREATE,
            content_object=category,
            object_repr=category.name,
            priority=AuditLog.Priority.MEDIUM,
            notify=True,
            metadata={"category_id": category.id},
        )

    def perform_update(self, serializer):
        category = serializer.save()
        log_user_action(
            request=self.request,
            user=self.request.user,
            action_type=AuditLog.ActionType.UPDATE,
            content_object=category,
            object_repr=category.name,
            priority=AuditLog.Priority.MEDIUM,
            metadata={"category_id": category.id},
        )


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True)  # type: ignore
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_fields = ["category", "is_active"]
    ordering_fields = ["base_price", "created_at", "name"]
    search_fields = ["name", "description", "slug"]

    def perform_create(self, serializer):
        product = serializer.save()
        log_user_action(
            request=self.request,
            user=self.request.user if self.request.user.is_authenticated else None,
            action_type=AuditLog.ActionType.CREATE,
            content_object=product,
            object_repr=product.name,
            priority=AuditLog.Priority.MEDIUM,
            notify=True,
            metadata={"product_id": product.id},
        )

    def perform_update(self, serializer):
        product = serializer.save()
        log_user_action(
            request=self.request,
            user=self.request.user,
            action_type=AuditLog.ActionType.UPDATE,
            content_object=product,
            object_repr=product.name,
            priority=AuditLog.Priority.MEDIUM,
            metadata={"product_id": product.id},
        )

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Product.objects.all()  # type: ignore
        return Product.objects.filter(is_active=True)  # type: ignore
