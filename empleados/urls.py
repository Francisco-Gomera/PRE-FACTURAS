from django.urls import path

from .views import acciones_personal, buscar, detalle, guardar, index, maestro

app_name = "empleados"

urlpatterns = [
    path("", index, name="index"),
    path("maestro/", maestro, name="maestro"),
    path("acciones-personal/", acciones_personal, name="acciones_personal"),
    path("buscar/", buscar, name="buscar"),
    path("detalle/<int:empleado_id>/", detalle, name="detalle"),
    path("guardar/", guardar, name="guardar"),
]
