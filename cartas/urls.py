from django.urls import path

from .views import index, saldo_view, saldo_detalle_view

app_name = "cartas"

urlpatterns = [
    path("", index, name="index"),
    path("saldo/", saldo_view, name="saldo"),
    path("saldo/detalle/", saldo_detalle_view, name="saldo_detalle"),
]
