from rest_framework import serializers

from .models import SalesReport, UserActivity


class UserActivitySerializer(serializers.ModelSerializer):
    activity_type_display = serializers.CharField(
        source="get_activity_type_display", read_only=True
    )

    class Meta:
        model = UserActivity
        fields = [
            "id",
            "user",
            "activity_type",
            "activity_type_display",
            "metadata",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class SalesReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesReport
        fields = [
            "id",
            "start_date",
            "end_date",
            "total_orders",
            "total_revenue",
            "average_order_value",
            "top_products",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
