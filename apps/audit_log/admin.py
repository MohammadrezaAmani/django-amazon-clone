from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "action_type",
        "status",
        "priority",
        "ip_address",
        "object_repr",
        "created_at",
    )
    list_filter = ("action_type", "status", "priority", "created_at")
    search_fields = ("user__username", "object_repr", "error_message", "ip_address")
    readonly_fields = [field.name for field in AuditLog._meta.fields]  # type: ignore
    ordering = ("-created_at",)
