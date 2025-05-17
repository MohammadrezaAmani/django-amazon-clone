from django.contrib import admin

from .models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "feedback_type",
        "status",
        "title",
        "created_at",
        "updated_at",
    )
    list_filter = ("feedback_type", "status", "created_at")
    search_fields = ("user__username", "title", "description")
    readonly_fields = ("created_at", "updated_at", "metadata")
    ordering = ("-created_at",)
