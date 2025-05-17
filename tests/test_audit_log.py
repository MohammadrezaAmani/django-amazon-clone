import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.audit_log.models import AuditLog
from apps.audit_log.utils import log_user_action
from apps.notifications.models import Notification

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


@pytest.mark.django_db
class TestAuditLog:
    def test_log_action_with_priority(self, user):
        log_user_action(
            user=user,
            action_type=AuditLog.ActionType.LOGIN,
            status=AuditLog.Status.SUCCESS,
            priority=AuditLog.Priority.LOW,
        )
        log = AuditLog.objects.get()  # type: ignore
        assert log.user == user
        assert log.action_type == AuditLog.ActionType.LOGIN
        assert log.status == AuditLog.Status.SUCCESS
        assert log.priority == AuditLog.Priority.LOW

    def test_log_action_default_priority(self, user):
        log_user_action(
            user=user,
            action_type=AuditLog.ActionType.DELETE,
            status=AuditLog.Status.SUCCESS,
        )
        log = AuditLog.objects.get()  # type: ignore
        assert log.priority == AuditLog.Priority.HIGH

    def test_log_model_create(self, user):
        notification = Notification.objects.create(  # type: ignore
            user=user,
            message="Test",
            channels=["IN_APP"],
            _audit_log_user=user,
        )
        log = AuditLog.objects.get(action_type=AuditLog.ActionType.CREATE)  # type: ignore
        assert log.content_object == notification
        assert log.user == user
        assert log.priority == AuditLog.Priority.MEDIUM

    def test_api_logs_list_admin(self, api_client, superuser, user):
        log_user_action(
            user=user,
            action_type=AuditLog.ActionType.LOGIN,
            priority=AuditLog.Priority.LOW,
        )
        api_client.force_authenticate(user=superuser)
        response = api_client.get("/audit/api/logs/")
        assert response.status_code == 200
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["priority"] == "LOW"

    def test_api_logs_filter_priority(self, api_client, superuser, user):
        log_user_action(
            user=user,
            action_type=AuditLog.ActionType.DELETE,
            priority=AuditLog.Priority.HIGH,
        )
        api_client.force_authenticate(user=superuser)
        response = api_client.get("/audit/api/logs/?priority=HIGH")
        assert response.status_code == 200
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["priority"] == "HIGH"
