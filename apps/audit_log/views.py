from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 1000


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()  # type: ignore
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = AuditLogPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_fields = [
        "action_type",
        "status",
        "priority",
        "ip_address",
        "content_type",
        "created_at",
    ]
    ordering_fields = ["created_at", "action_type", "status", "priority"]
    search_fields = ["user__username", "object_repr", "error_message"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return AuditLog.objects.all()  # type: ignore
        return AuditLog.objects.filter(user=user)  # type: ignore
