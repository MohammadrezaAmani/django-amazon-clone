import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from .models import Notification

User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = self.scope["query_string"].decode()
        token = None
        for param in query_string.split("&"):
            if param.startswith("token="):
                token = param.split("=")[1]
                break

        if not token:
            await self.close(code=4001, reason="Missing token")
            return

        try:
            access_token = AccessToken(token)
            user_id = access_token["user_id"]
            user = await database_sync_to_async(User.objects.get)(id=user_id)

            if not user.is_active:
                await self.close(code=4003, reason="Inactive user")
                return

            self.scope["user"] = user
            self.user = user
            self.group_name = f"user_{user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)  # type: ignore

            await database_sync_to_async(user.update_last_activity)()
            await self.accept()
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "welcome",
                        "message": f"Connected as {user.username}",
                    }
                )
            )

        except (TokenError, User.DoesNotExist):
            await self.close(code=4002, reason="Invalid token")

    async def disconnect(self, close_code):  # type: ignore
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)  # type: ignore

    async def receive(self, text_data):  # type: ignore
        try:
            data = json.loads(text_data)
            message_type = data.get("type")

            if message_type == "ping":
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "pong",
                            "message": "Pong!",
                        }
                    )
                )
            elif message_type == "mark_read":
                notification_id = data.get("notification_id")
                if notification_id:
                    await self.mark_notification_read(notification_id)

        except json.JSONDecodeError:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "error",
                        "message": "Invalid JSON format",
                    }
                )
            )

    async def send_notification(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "notification",
                    "notification_id": event["notification_id"],
                    "message": event["message"],
                    "priority": event["priority"],
                    "category": event["category"],
                    "metadata": event["metadata"],
                    "timestamp": event["timestamp"],
                }
            )
        )

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        try:
            notification = Notification.objects.get(id=notification_id, user=self.user)  # type: ignore
            notification.mark_as_read()
        except Notification.DoesNotExist:  # type: ignore
            pass
