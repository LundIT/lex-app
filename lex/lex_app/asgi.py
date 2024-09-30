"""
ASGI config for lex_app project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
"""
import os


from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

import atexit
import asyncio
import generic_app.rest_api.routing
from generic_app.rest_api.consumers.BackendHealthConsumer import BackendHealthConsumer
from generic_app.rest_api.consumers.CalculationsConsumer import CalculationsConsumer
from generic_app.rest_api.consumers.UpdateCalculationStatusConsumer import UpdateCalculationStatusConsumer
from generic_app.rest_api.consumers.CalculationLogConsumer import CalculationLogConsumer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lex_app.settings")
django_asgi_app = get_asgi_application()
application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(generic_app.rest_api.routing.websocket_urlpatterns))
        ),
    }
)
def on_server_shutdown(*args, **kwargs):
    """
    Handles server shutdown by disconnecting all active consumers.

    This function is registered to be called upon server shutdown to ensure
    that all active WebSocket consumers are properly disconnected.

    Parameters
    ----------
    *args
        Variable length argument list.
    **kwargs
        Arbitrary keyword arguments.
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(BackendHealthConsumer.disconnect_all())
    loop.run_until_complete(CalculationLogConsumer.disconnect_all())
    loop.run_until_complete(CalculationsConsumer.disconnect_all())
    loop.run_until_complete(UpdateCalculationStatusConsumer.disconnect_all())

atexit.register(on_server_shutdown)
