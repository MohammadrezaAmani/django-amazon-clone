from django.urls import path, re_path
from rest_framework.routers import DefaultRouter

from .consumers import NotificationConsumer
from .views import (
    NotificationBatchViewSet,
    NotificationTemplateViewSet,
    NotificationViewSet,
)

router = DefaultRouter()
router.register(
    r"templates", NotificationTemplateViewSet, basename="notification-template"
)
router.register(r"notifications", NotificationViewSet, basename="notification")
router.register(r"batches", NotificationBatchViewSet, basename="notification-batch")
notification_list = NotificationViewSet.as_view({"get": "list", "post": "create"})
notification_detail = NotificationViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
notification_mark_read = NotificationViewSet.as_view({"post": "mark_read"})
notification_mark_all_read = NotificationViewSet.as_view({"post": "mark_all_read"})
urlpatterns = [
    path("notifications/", notification_list, name="notification-list"),
    path("notifications/<int:pk>/", notification_detail, name="notification-detail"),
    path(
        "notifications/<int:pk>/mark_read/",
        notification_mark_read,
        name="notification-mark-read",
    ),
    path(
        "notifications/mark_all_read/",
        notification_mark_all_read,
        name="notification-mark-all-read",
    ),
]
urlpatterns.extend(router.urls)
websocket_urlpatterns = [
    re_path(r"ws/notifications/$", NotificationConsumer.as_asgi()),
]
