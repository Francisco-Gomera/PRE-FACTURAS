from django.urls import path

from .views import buscar, detalle, guardar, index, maestro

app_name = "empleados"

urlpatterns = [
    path("", index, name="index"),
    path("maestro/", maestro, name="maestro"),
    path("buscar/", buscar, name="buscar"),
    path("detalle/<int:empleado_id>/", detalle, name="detalle"),
    path("guardar/", guardar, name="guardar"),
]
