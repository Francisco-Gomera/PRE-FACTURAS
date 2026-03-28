from django.urls import path

from .views import (
    aviso_detalle_view,
    aviso_view,
    aviso_whatsapp_send_view,
    index,
    plantillas_view,
    saldo_detalle_view,
    saldo_view,
    whatsapp_webhook_view,
)

app_name = "cartas"

urlpatterns = [
    path("", index, name="index"),
    path("aviso/", aviso_view, name="aviso"),
    path("aviso/detalle/", aviso_detalle_view, name="aviso_detalle"),
    path("aviso/whatsapp/enviar/", aviso_whatsapp_send_view, name="aviso_whatsapp_send"),
    path("plantillas/", plantillas_view, name="plantillas"),
    path("saldo/", saldo_view, name="saldo"),
    path("saldo/detalle/", saldo_detalle_view, name="saldo_detalle"),
    path("whatsapp/webhook/", whatsapp_webhook_view, name="whatsapp_webhook"),
]
