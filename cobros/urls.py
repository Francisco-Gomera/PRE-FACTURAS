from django.urls import path

from .views import index

app_name = "cobros"

urlpatterns = [
    path("", index, name="index"),
]
