from django.urls import path

from .views import index

app_name = "prefacturas_mod"

urlpatterns = [
    path("", index, name="index"),
]
