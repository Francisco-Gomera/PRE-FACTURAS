from django.urls import path

from .consumers import (
    ChatInternoConsumer,
    CxcConsumer,
    FinanciamientoConsumer,
    InventarioSolicitudesConsumer,
    NotificationConsumer,
    PrefacturaConsumer,
)


websocket_urlpatterns = [
    path("ws/notifications/", NotificationConsumer.as_asgi()),
    path("ws/inventario-solicitudes/", InventarioSolicitudesConsumer.as_asgi()),
    path("ws/prefacturas/", PrefacturaConsumer.as_asgi()),
    path("ws/cxc/", CxcConsumer.as_asgi()),
    path("ws/financiamiento/", FinanciamientoConsumer.as_asgi()),
    path("ws/chat-interno/", ChatInternoConsumer.as_asgi()),
]
