from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from audit_log.models import AuditLog
from audit_log.utils import log_user_action

from .models import Feedback
from .serializers import FeedbackSerializer


class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()  # type: ignore
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_fields = ["feedback_type", "status", "created_at"]
    ordering_fields = ["created_at", "feedback_type", "status"]
    search_fields = ["title", "description"]

    def perform_create(self, serializer):
        feedback = serializer.save(
            user=self.request.user if self.request.user.is_authenticated else None
        )
        log_user_action(
            request=self.request,
            user=self.request.user if self.request.user.is_authenticated else None,
            action_type=AuditLog.ActionType.CREATE,
            content_object=feedback,
            object_repr=feedback.title,
            priority=AuditLog.Priority.MEDIUM,
            notify=True,
            metadata={"feedback_type": feedback.feedback_type},
        )

    def perform_update(self, serializer):
        feedback = serializer.save()
        log_user_action(
            request=self.request,
            user=self.request.user,
            action_type=AuditLog.ActionType.UPDATE,
            content_object=feedback,
            object_repr=feedback.title,
            priority=AuditLog.Priority.MEDIUM,
            metadata={"feedback_type": feedback.feedback_type},
        )

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Feedback.objects.all()  # type: ignore
        return Feedback.objects.filter(user=user)  # type: ignore
