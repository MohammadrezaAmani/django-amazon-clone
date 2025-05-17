from rest_framework import serializers

from .models import Notification, NotificationBatch, NotificationTemplate


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = [
            "id",
            "name",
            "category",
            "subject",
            "message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class NotificationBatchSerializer(serializers.ModelSerializer):
    notification_count = serializers.IntegerField(
        source="notifications.count", read_only=True
    )

    class Meta:
        model = NotificationBatch
        fields = [
            "id",
            "batch_id",
            "description",
            "created_by",
            "created_at",
            "notification_count",
        ]
        read_only_fields = ["batch_id", "created_at", "notification_count"]


class NotificationSerializer(serializers.ModelSerializer):
    batch = NotificationBatchSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "user",
            "template",
            "batch",
            "message",
            "subject",
            "priority",
            "channels",
            "category",
            "status",
            "metadata",
            "is_read",
            "expires_at",
            "created_at",
            "sent_at",
            "read_at",
        ]
        read_only_fields = ["user", "created_at", "sent_at", "read_at", "status"]
