from rest_framework import serializers

from .models import Feedback


class FeedbackSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Feedback
        fields = [
            "id",
            "user",
            "feedback_type",
            "status",
            "title",
            "description",
            "created_at",
            "updated_at",
            "metadata",
        ]
        read_only_fields = [
            "id",
            "user",
            "status",
            "created_at",
            "updated_at",
            "metadata",
        ]
