from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    content_type = serializers.StringRelatedField()
    user = serializers.StringRelatedField()

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user",
            "action_type",
            "status",
            "priority",
            "ip_address",
            "user_agent",
            "content_type",
            "object_id",
            "object_repr",
            "changes",
            "metadata",
            "created_at",
            "error_message",
        ]
        read_only_fields = fields
