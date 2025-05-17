from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.audit_log.models import AuditLog
from apps.audit_log.utils import log_user_action

from .models import Action, Comment, React, Tag, View  # , Location
from .serializers import (  # LocationSerializer,
    ActionSerializer,
    CommentSerializer,
    ReactSerializer,
    TagSerializer,
    ViewSerializer,
)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["name", "parent"]
    search_fields = ["name", "slug"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
        log_user_action(
            request=self.request,
            action_type=AuditLog.ActionType.CREATE,
            content_object=serializer.instance,
            priority=AuditLog.Priority.MEDIUM,
        )

    @action(detail=False, methods=["post"])
    def bulk_create(self, request):
        names = request.data.get("names", [])
        if not names:
            return Response(
                {"error": "Names list is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        tags = Tag.bulk_create_from_names(names, created_by=self.request.user)
        serializer = self.get_serializer(tags, many=True)
        log_user_action(
            request=request,
            action_type=AuditLog.ActionType.CREATE,
            priority=AuditLog.Priority.MEDIUM,
            metadata={"bulk_tags": names},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ActionViewSet(viewsets.ModelViewSet):
    queryset = Action.objects.all()  # type: ignore
    serializer_class = ActionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Action.objects.all()  # type: ignore
        return Action.objects.filter(user=self.request.user)  # type: ignore

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        log_user_action(
            request=self.request,
            action_type=AuditLog.ActionType.CREATE,
            content_object=serializer.instance,
            priority=AuditLog.Priority.MEDIUM,
        )


class ReactViewSet(viewsets.ModelViewSet):
    queryset = React.objects.all()  # type: ignore
    serializer_class = ReactSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return React.objects.all()  # type: ignore
        return React.objects.filter(user=self.request.user)  # type: ignore

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        log_user_action(
            request=self.request,
            action_type=AuditLog.ActionType.CREATE,
            content_object=serializer.instance,
            priority=AuditLog.Priority.LOW,
        )


class ViewViewSet(viewsets.ModelViewSet):
    queryset = View.objects.all()  # type: ignore
    serializer_class = ViewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return View.objects.all()  # type: ignore
        return View.objects.filter(user=self.request.user)  # type: ignore

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        log_user_action(
            request=self.request,
            action_type=AuditLog.ActionType.CREATE,
            content_object=serializer.instance,
            priority=AuditLog.Priority.LOW,
        )


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["content_type", "object_id", "parent"]
    search_fields = ["text"]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Comment.objects.all()
        return Comment.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        log_user_action(
            request=self.request,
            action_type=AuditLog.ActionType.CREATE,
            content_object=serializer.instance,
            priority=AuditLog.Priority.MEDIUM,
        )


# class LocationViewSet(viewsets.ModelViewSet):
#     queryset = Location.objects.all()  # type: ignore
#     serializer_class = LocationSerializer
#     permission_classes = [IsAuthenticated]
#     filter_backends = [DjangoFilterBackend, filters.SearchFilter]
#     filterset_fields = ["location_type", "country", "parent"]
#     search_fields = ["name", "address", "postal_code"]

#     def perform_create(self, serializer):
#         serializer.save()
#         log_user_action(
#             request=self.request,
#             action_type=AuditLog.ActionType.CREATE,
#             content_object=serializer.instance,
#             priority=AuditLog.Priority.MEDIUM,
#         )
