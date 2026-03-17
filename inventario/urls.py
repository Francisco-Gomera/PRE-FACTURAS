from django.urls import path

from .views import index, grupos_view, stock_view

app_name = "inventario"

urlpatterns = [
    path("", index, name="index"),
    path("grupos/", grupos_view, name="grupos"),
    path("stock/", stock_view, name="stock"),
]
