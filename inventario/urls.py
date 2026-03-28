from django.urls import path

from .views import (
    articulos_view,
    entrada_articulos_buscar_view,
    entrada_articulos_detalle_view,
    entrada_articulos_view,
    grupos_view,
    index,
    salida_articulos_view,
    stock_view,
)

app_name = "inventario"

urlpatterns = [
    path("", index, name="index"),
    path("articulos/", articulos_view, name="articulos"),
    path("entrada-articulos/", entrada_articulos_view, name="entrada_articulos"),
    path("entrada-articulos/buscar/", entrada_articulos_buscar_view, name="entrada_articulos_buscar"),
    path("entrada-articulos/detalle/", entrada_articulos_detalle_view, name="entrada_articulos_detalle"),
    path("salida-articulos/", salida_articulos_view, name="salida_articulos"),
    path("grupos/", grupos_view, name="grupos"),
    path("stock/", stock_view, name="stock"),
]
