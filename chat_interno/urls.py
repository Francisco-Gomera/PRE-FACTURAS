from django.urls import path

from .views import (
    crear_grupo_view,
    enviar_adjuntos_view,
    enviar_mensaje_view,
    enviar_nota_voz_view,
    index,
    iniciar_directo_view,
    mensajes_view,
    ocultar_mensaje_view,
    ocultar_sala_view,
    registros_compartibles_view,
    salas_view,
    usuarios_view,
)

app_name = "chat_interno"

urlpatterns = [
    path("", index, name="index"),
    path("usuarios/", usuarios_view, name="usuarios"),
    path("registros-compartibles/", registros_compartibles_view, name="registros_compartibles"),
    path("salas/", salas_view, name="salas"),
    path("mensajes/", mensajes_view, name="mensajes"),
    path("directo/iniciar/", iniciar_directo_view, name="iniciar_directo"),
    path("grupos/crear/", crear_grupo_view, name="crear_grupo"),
    path("mensajes/enviar/", enviar_mensaje_view, name="enviar_mensaje"),
    path("mensajes/enviar-nota-voz/", enviar_nota_voz_view, name="enviar_nota_voz"),
    path("mensajes/enviar-adjuntos/", enviar_adjuntos_view, name="enviar_adjuntos"),
    path("mensajes/ocultar/", ocultar_mensaje_view, name="ocultar_mensaje"),
    path("salas/ocultar/", ocultar_sala_view, name="ocultar_sala"),
]
