from django.urls import path

from .views import (
    acciones_personal,
    acciones_personal_cancelar,
    acciones_personal_detalle,
    acciones_personal_guardar,
    acciones_personal_listar,
    buscar,
    control_vacaciones,
    control_vacaciones_calendario,
    control_vacaciones_descontar,
    control_vacaciones_eliminar_plan,
    control_vacaciones_listar,
    control_vacaciones_planificar,
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
    path("control-vacaciones/", control_vacaciones, name="control_vacaciones"),
    path("control-vacaciones/listar/", control_vacaciones_listar, name="control_vacaciones_listar"),
    path("control-vacaciones/calendario/", control_vacaciones_calendario, name="control_vacaciones_calendario"),
    path("control-vacaciones/descontar/", control_vacaciones_descontar, name="control_vacaciones_descontar"),
    path("control-vacaciones/planificar/", control_vacaciones_planificar, name="control_vacaciones_planificar"),
    path("control-vacaciones/eliminar-plan/", control_vacaciones_eliminar_plan, name="control_vacaciones_eliminar_plan"),
    path("buscar/", buscar, name="buscar"),
    path("detalle/<int:empleado_id>/", detalle, name="detalle"),
    path("guardar/", guardar, name="guardar"),
]
