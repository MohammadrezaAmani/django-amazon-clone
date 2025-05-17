from channels.auth import get_user_model
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import Notification, NotificationBatch, NotificationTemplate
from .serializers import (
    NotificationBatchSerializer,
    NotificationSerializer,
    NotificationTemplateSerializer,
)
from .utils import send_batch_notification


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    queryset = NotificationTemplate.objects.all()  # type: ignore
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAdminUser]


class NotificationBatchViewSet(viewsets.ModelViewSet):
    queryset = NotificationBatch.objects.all()  # type: ignore
    serializer_class = NotificationBatchSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        """Set the created_by field to the current user."""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def send_batch(self, request, pk=None):
        """Send a batch notification to specified users."""
        batch = self.get_object()
        user_ids = request.data.get("user_ids", [])
        users = get_user_model().objects.filter(id__in=user_ids, is_active=True)
        if not users:
            return Response(
                {"error": "No valid users provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        batch, notifications = send_batch_notification(
            users=users,
            message=request.data.get("message"),
            template_name=request.data.get("template_name"),
            context=request.data.get("context", {}),
            subject=request.data.get("subject"),
            priority=request.data.get("priority", Notification.Priority.MEDIUM),
            channels=request.data.get(
                "channels",
                [Notification.Channel.IN_APP, Notification.Channel.WEBSOCKET],
            ),
            category=request.data.get("category"),
            metadata=request.data.get("metadata", {}),
            expires_at=request.data.get("expires_at"),
            description=batch.description,
            created_by=request.user,
        )
        return Response(
            {
                "message": f"Sent {len(notifications)} notifications in batch {batch.batch_id}",
                "batch": NotificationBatchSerializer(batch).data,
            },
            status=status.HTTP_200_OK,
        )


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return non-expired notifications for the authenticated user."""
        return Notification.objects.filter(  # type: ignore
            user=self.request.user,
            expires_at__gte=timezone.now(),
        ) | Notification.objects.filter(  # type: ignore
            user=self.request.user,
            expires_at__isnull=True,
        )

    def create(self, request, *args, **kwargs):
        return Response(
            {"error": "Use send_notification utility to create notifications."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        try:
            notification = self.get_object()
            notification.mark_as_read()
            return Response({"message": "Notification marked as read."})
        except Notification.DoesNotExist:  # type: ignore
            return Response(
                {"error": "Notification not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        notifications = self.get_queryset().filter(is_read=False)
        count = notifications.count()
        notifications.update(is_read=True, read_at=timezone.now())
        return Response({"message": f"Marked {count} notifications as read."})

    @extend_schema(
        parameters=[
            OpenApiParameter(name="pk", type=int, location=OpenApiParameter.PATH)
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="pk", type=int, location=OpenApiParameter.PATH)
        ]
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="pk", type=int, location=OpenApiParameter.PATH)
        ]
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="pk", type=int, location=OpenApiParameter.PATH)
        ]
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
