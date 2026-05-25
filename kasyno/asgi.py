import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kasyno.settings')
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import lobby.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            lobby.routing.websocket_urlpatterns
        )
    ),
})