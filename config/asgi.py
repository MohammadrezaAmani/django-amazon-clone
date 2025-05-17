import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

from notifications.urls import (
    websocket_urlpatterns as notifications_websocket_urlpatterns,
)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "your_project.settings")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(notifications_websocket_urlpatterns))
        ),
    }
)
