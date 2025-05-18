from django.contrib import admin

from .models import SalesReport, UserActivity


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ("user", "activity_type", "created_at")
    list_filter = ("activity_type", "created_at")
    search_fields = ("user__username", "metadata__query")
    readonly_fields = ("created_at", "metadata")
    ordering = ("-created_at",)


@admin.register(SalesReport)
class SalesReportAdmin(admin.ModelAdmin):
    list_display = (
        "start_date",
        "end_date",
        "total_orders",
        "total_revenue",
        "created_at",
    )
    list_filter = ("start_date", "end_date")
    readonly_fields = ("created_at", "top_products")
    ordering = ("-created_at",)

    def get_changelist_template(self):
        return "admin/analytics/salesreport_changelist.html"
