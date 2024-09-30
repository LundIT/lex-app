"""
This module configures the ASGI application for handling different protocol types.

It sets up the routing for WebSocket connections using Django Channels.
"""

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import generic_app.rest_api.routing

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': AuthMiddlewareStack(
        URLRouter(
            generic_app.rest_api.routing.websocket_urlpatterns
        )
    ),
})