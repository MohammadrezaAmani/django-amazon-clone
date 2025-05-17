from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Action, Comment, React, Tag, View  # , Location

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), allow_null=True
    )

    class Meta:
        model = Tag
        fields = ["id", "name", "slug", "parent", "created_by", "created_at"]
        read_only_fields = ["slug", "created_by", "created_at"]


class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = ["id", "user", "action_type", "metadata", "created_at"]
        read_only_fields = ["user", "created_at"]


class ReactSerializer(serializers.ModelSerializer):
    content_type = serializers.StringRelatedField()
    user = serializers.StringRelatedField()

    class Meta:
        model = React
        fields = [
            "id",
            "user",
            "reaction_type",
            "content_type",
            "object_id",
            "created_at",
        ]
        read_only_fields = ["user", "created_at"]


class ViewSerializer(serializers.ModelSerializer):
    content_type = serializers.StringRelatedField()
    user = serializers.StringRelatedField()

    class Meta:
        model = View
        fields = ["id", "user", "content_type", "object_id", "created_at"]
        read_only_fields = ["user", "created_at"]


class CommentSerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.all(), allow_null=True
    )
    user = serializers.StringRelatedField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "user",
            "content_type",
            "object_id",
            "parent",
            "text",
            "media",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "created_at", "updated_at"]


# class LocationSerializer(serializers.ModelSerializer):
#     parent = serializers.PrimaryKeyRelatedField(
#         queryset=Location.objects.all(),  # type: ignore
#         allow_null=True,
#     )
#     coordinates = serializers.CharField(allow_null=True)

#     class Meta:
#         model = Location
#         fields = [
#             "id",
#             "name",
#             "slug",
#             "location_type",
#             "parent",
#             "country",
#             "coordinates",
#             "address",
#             "postal_code",
#             "metadata",
#             "created_at",
#         ]
#         read_only_fields = ["slug", "created_at"]
