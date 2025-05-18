from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAdminUser

from .models import SalesReport, UserActivity
from .serializers import SalesReportSerializer, UserActivitySerializer


class UserActivityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserActivity.objects.all()  # type: ignore
    serializer_class = UserActivitySerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["user", "activity_type", "created_at"]
    ordering_fields = ["created_at"]


class SalesReportViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SalesReport.objects.all()  # type: ignore
    serializer_class = SalesReportSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["start_date", "end_date"]
    ordering_fields = ["created_at", "total_revenue"]
