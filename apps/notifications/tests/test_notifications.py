import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.notifications.consumers import NotificationConsumer
from apps.notifications.models import (
    Notification,
    NotificationBatch,
    NotificationTemplate,
)
from apps.notifications.utils import send_batch_notification, send_notification

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser",
        email="testuser@example.com",
        password="testpass123",
        is_verified=True,
    )


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass123",
    )


@pytest.fixture
def notification_template(db):
    return NotificationTemplate.objects.create(  # type: ignore
        name="welcome",
        subject="Welcome to Our Platform",
        message="Hello {username}, welcome to our platform!",
        category="system",
    )


@pytest.mark.django_db
class TestNotificationModels:
    def test_notification_template_creation(self, notification_template):
        assert notification_template.name == "welcome"
        assert notification_template.subject == "Welcome to Our Platform"
        assert (
            notification_template.message
            == "Hello {username}, welcome to our platform!"
        )
        assert notification_template.category == "system"

    def test_notification_batch_creation(self, superuser):
        batch = NotificationBatch.objects.create(  # type: ignore
            description="Test Batch",
            created_by=superuser,
        )
        assert str(batch.batch_id) in str(batch)
        assert batch.description == "Test Batch"
        assert batch.created_by == superuser

    def test_notification_creation(self, user, notification_template):
        batch = NotificationBatch.objects.create(description="Test Batch")  # type: ignore
        notification = Notification.objects.create(  # type: ignore
            user=user,
            template=notification_template,
            batch=batch,
            message="Hello testuser, welcome!",
            subject="Welcome",
            priority=Notification.Priority.HIGH,
            channels=[Notification.Channel.IN_APP, Notification.Channel.WEBSOCKET],
            category="system",
            metadata={"link": "/dashboard"},
            expires_at=timezone.now() + timezone.timedelta(days=7),
            status=Notification.Status.PENDING,
        )
        assert notification.user == user
        assert notification.batch == batch
        assert notification.priority == Notification.Priority.HIGH
        assert notification.category == "system"
        assert notification.metadata == {"link": "/dashboard"}
        assert not notification.is_expired()

    def test_notification_expiration(self, user):
        notification = Notification.objects.create(  # type: ignore
            user=user,
            message="Test",
            expires_at=timezone.now() - timezone.timedelta(days=1),
            channels=[Notification.Channel.IN_APP],
        )
        assert notification.is_expired()

    def test_mark_as_failed(self, user):
        notification = Notification.objects.create(  # type: ignore
            user=user,
            message="Test",
            channels=[Notification.Channel.IN_APP],
            status=Notification.Status.PENDING,
        )
        notification.mark_as_failed("Test error")
        assert notification.status == Notification.Status.FAILED
        assert notification.metadata["error"] == "Test error"


@pytest.mark.django_db
class TestNotificationUtils:
    def test_send_notification_direct(self, user, mocker):
        mocker.patch("django.core.mail.send_mail")
        notification = send_notification(
            user=user,
            message="Direct message",
            subject="Test Subject",
            priority=Notification.Priority.HIGH,
            channels=[
                Notification.Channel.IN_APP,
                Notification.Channel.EMAIL,
                Notification.Channel.WEBSOCKET,
            ],
            category="system",
            metadata={"link": "/dashboard"},
            expires_at=timezone.now() + timezone.timedelta(days=7),
        )
        assert notification.message == "Direct message"
        assert notification.priority == Notification.Priority.HIGH
        assert notification.category == "system"
        assert notification.metadata == {"link": "/dashboard"}
        assert len(mail.outbox) == 1  # type: ignore
        assert notification.status == Notification.Status.SENT

    def test_send_batch_notification(self, user, superuser, mocker):
        mocker.patch("django.core.mail.send_mail")
        users = [user, superuser]
        batch, notifications = send_batch_notification(
            users=users,
            message="Batch message",
            priority=Notification.Priority.MEDIUM,
            channels=[Notification.Channel.IN_APP],
            category="marketing",
            description="Test Batch",
            created_by=superuser,
        )
        assert batch.description == "Test Batch"
        assert batch.created_by == superuser
        assert len(notifications) == 2
        assert notifications[0].category == "marketing"
        assert notifications[0].batch == batch

    def test_send_notification_failed_email(self, user, mocker):
        mocker.patch("django.core.mail.send_mail", side_effect=Exception("Email error"))
        notification = send_notification(
            user=user,
            message="Test",
            channels=[Notification.Channel.EMAIL],
        )
        assert notification.status == Notification.Status.FAILED
        assert "Email error" in notification.metadata["error"]


@pytest.mark.django_db
class TestNotificationAPI:
    def test_list_notifications(self, api_client, user):
        api_client.force_authenticate(user=user)
        Notification.objects.create(  # type: ignore
            user=user,
            message="Test notification",
            priority=Notification.Priority.MEDIUM,
            channels=[Notification.Channel.IN_APP],
            category="system",
        )
        response = api_client.get("/notifications/api/notifications/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["message"] == "Test notification"
        assert response.data[0]["category"] == "system"

    def test_list_excludes_expired(self, api_client, user):
        api_client.force_authenticate(user=user)
        Notification.objects.create(  # type: ignore
            user=user,
            message="Expired",
            channels=[Notification.Channel.IN_APP],
            expires_at=timezone.now() - timezone.timedelta(days=1),
        )
        response = api_client.get("/notifications/api/notifications/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_mark_read(self, api_client, user):
        api_client.force_authenticate(user=user)
        notification = Notification.objects.create(  # type: ignore
            user=user,
            message="Test",
            priority=Notification.Priority.MEDIUM,
            channels=[Notification.Channel.IN_APP],
        )
        response = api_client.post(
            f"/notifications/api/notifications/{notification.id}/mark_read/"
        )
        assert response.status_code == status.HTTP_200_OK
        notification.refresh_from_db()
        assert notification.is_read


@pytest.mark.django_db
@pytest.mark.asyncio
class TestNotificationConsumer:
    async def test_send_notification(self, user):
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        communicator = WebsocketCommunicator(
            NotificationConsumer.as_asgi(), f"/ws/notifications/?token={access_token}"
        )
        await communicator.connect()
        notification = await database_sync_to_async(send_notification)(
            user=user,
            message="Test notification",
            channels=[Notification.Channel.WEBSOCKET],
            category="system",
            metadata={"link": "/dashboard"},
        )
        response = await communicator.receive_json_from()
        assert response["type"] == "notification"
        assert response["message"] == "Test notification"
        assert response["notification_id"] == notification.id
        assert response["category"] == "system"
        assert response["metadata"] == {"link": "/dashboard"}
        await communicator.disconnect()
