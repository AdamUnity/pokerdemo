# kasyno/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import lobby.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kasyno.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            lobby.routing.websocket_urlpatterns
        )
    ),
})