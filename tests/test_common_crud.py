import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import Point
from rest_framework import status
from rest_framework.test import APIClient

from common.models import Action, Comment, Location, React, Tag, View
from notifications.models import Notification

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
def notification(user):
    return Notification.objects.create(  # type: ignore
        user=user,
        message="Test notification",
        channels=["IN_APP"],
        priority="MED",
    )


@pytest.mark.django_db
class TestCommonCRUD:
    def test_create_tag(self, api_client, user):
        api_client.force_authenticate(user=user)
        data = {"name": "Test Tag"}
        response = api_client.post("/common/api/tags/", data)
        assert response.status_code == status.HTTP_201_CREATED
        tag = Tag.objects.get(name="Test Tag")
        assert tag.created_by == user
        assert tag.slug == "test-tag"

    def test_bulk_create_tags(self, api_client, user):
        api_client.force_authenticate(user=user)
        data = {"names": ["Tag1", "Tag2", "Tag1"]}
        response = api_client.post("/common/api/tags/bulk_create/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Tag.objects.count() == 2
        assert Tag.objects.filter(name="Tag1").exists()
        assert Tag.objects.filter(name="Tag2").exists()

    def test_read_tag(self, api_client, user):
        Tag.objects.create(name="Test Tag", created_by=user, slug="test-tag")
        api_client.force_authenticate(user=user)
        response = api_client.get("/common/api/tags/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Test Tag"

    def test_update_tag(self, api_client, user):
        tag = Tag.objects.create(name="Old Tag", created_by=user, slug="old-tag")
        api_client.force_authenticate(user=user)
        data = {"name": "New Tag"}
        response = api_client.put(f"/common/api/tags/{tag.id}/", data)
        assert response.status_code == status.HTTP_200_OK
        tag.refresh_from_db()
        assert tag.name == "New Tag"
        assert tag.slug == "new-tag"

    def test_delete_tag(self, api_client, user):
        tag = Tag.objects.create(name="Test Tag", created_by=user, slug="test-tag")
        api_client.force_authenticate(user=user)
        response = api_client.delete(f"/common/api/tags/{tag.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Tag.objects.filter(id=tag.id).exists()

    def test_create_action(self, api_client, user):
        api_client.force_authenticate(user=user)
        data = {"action_type": "CLICK", "metadata": {"button": "submit"}}
        response = api_client.post("/common/api/actions/", data)
        assert response.status_code == status.HTTP_201_CREATED
        action = Action.objects.get()  # type: ignore
        assert action.user == user
        assert action.action_type == "CLICK"

    def test_create_react(self, api_client, user, notification):
        api_client.force_authenticate(user=user)
        data = {
            "reaction_type": "LIKE",
            "content_type": ContentType.objects.get_for_model(Notification).id,
            "object_id": notification.id,
        }
        response = api_client.post("/common/api/reacts/", data)
        assert response.status_code == status.HTTP_201_CREATED
        react = React.objects.get()  # type: ignore
        assert react.user == user
        assert react.content_object == notification

    def test_create_view(self, api_client, user, notification):
        api_client.force_authenticate(user=user)
        data = {
            "content_type": ContentType.objects.get_for_model(Notification).id,
            "object_id": notification.id,
        }
        response = api_client.post("/common/api/views/", data)
        assert response.status_code == status.HTTP_201_CREATED
        view = View.objects.get()  # type: ignore
        assert view.user == user
        assert view.content_object == notification

    def test_create_comment(self, api_client, user, notification):
        api_client.force_authenticate(user=user)
        data = {
            "content_type": ContentType.objects.get_for_model(Notification).id,
            "object_id": notification.id,
            "text": "Great post!",
        }
        response = api_client.post("/common/api/comments/", data)
        assert response.status_code == status.HTTP_201_CREATED
        comment = Comment.objects.get()
        assert comment.user == user
        assert comment.content_object == notification
        assert comment.text == "Great post!"

    def test_create_reply_comment(self, api_client, user, notification):
        parent = Comment.objects.create(
            user=user,
            content_type=ContentType.objects.get_for_model(Notification),
            object_id=notification.id,
            text="Parent comment",
        )
        api_client.force_authenticate(user=user)
        data = {
            "content_type": ContentType.objects.get_for_model(Notification).id,
            "object_id": notification.id,
            "parent": parent.id,
            "text": "Reply comment",
        }
        response = api_client.post("/common/api/comments/", data)
        assert response.status_code == status.HTTP_201_CREATED
        reply = Comment.objects.get(text="Reply comment")
        assert reply.parent == parent

    def test_create_location(self, api_client, user):
        api_client.force_authenticate(user=user)
        data = {
            "name": "Tehran",
            "location_type": "CITY",
            "country": "IR",
            "coordinates": "POINT(51.3890 35.6892)",
            "address": "Main St, Tehran",
            "postal_code": "12345",
        }
        response = api_client.post("/common/api/locations/", data)
        assert response.status_code == status.HTTP_201_CREATED
        location = Location.objects.get()  # type: ignore
        assert location.name == "Tehran"
        assert location.location_type == "CITY"
        assert location.country.code == "IR"
        assert location.coordinates == Point(51.3890, 35.6892)

    def test_read_location_filter(self, api_client, user):
        Location.objects.create(  # type: ignore
            name="Tehran",
            location_type="CITY",
            country="IR",
            coordinates=Point(51.3890, 35.6892),
        )
        api_client.force_authenticate(user=user)
        response = api_client.get("/common/api/locations/?location_type=CITY")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Tehran"
