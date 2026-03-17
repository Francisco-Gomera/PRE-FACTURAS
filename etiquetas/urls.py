from django.urls import path

from .views import index, formatos_view, impresion_view

app_name = "etiquetas"

urlpatterns = [
    path("", index, name="index"),
    path("formatos/", formatos_view, name="formatos"),
    path("impresion/", impresion_view, name="impresion"),
]
