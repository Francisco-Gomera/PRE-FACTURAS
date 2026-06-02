from django.urls import path

from .views import (
    acciones_personal,
    acciones_personal_cancelar,
    acciones_personal_detalle,
    acciones_personal_guardar,
    acciones_personal_listar,
    buscar,
    detalle,
    guardar,
    index,
    maestro,
)

app_name = "empleados"

urlpatterns = [
    path("", index, name="index"),
    path("maestro/", maestro, name="maestro"),
    path("acciones-personal/", acciones_personal, name="acciones_personal"),
    path("acciones-personal/listar/", acciones_personal_listar, name="acciones_personal_listar"),
    path("acciones-personal/detalle/<int:accion_id>/", acciones_personal_detalle, name="acciones_personal_detalle"),
    path("acciones-personal/guardar/", acciones_personal_guardar, name="acciones_personal_guardar"),
    path("acciones-personal/cancelar/", acciones_personal_cancelar, name="acciones_personal_cancelar"),
    path("buscar/", buscar, name="buscar"),
    path("detalle/<int:empleado_id>/", detalle, name="detalle"),
    path("guardar/", guardar, name="guardar"),
]
