import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()

# NOTE: When you add real-time bed availability updates (Week 5),
# wrap this with Django Channels' ProtocolTypeRouter to handle
# WebSocket connections alongside HTTP.
