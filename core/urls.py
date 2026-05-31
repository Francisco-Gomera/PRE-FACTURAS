from django.urls import path

from .views import dashboard_view, qz_certificate_view, qz_sign_view

app_name = "core"

urlpatterns = [
    path("", dashboard_view, name="dashboard"),
    path("qz/certificate/", qz_certificate_view, name="qz_certificate"),
    path("qz/sign/", qz_sign_view, name="qz_sign"),
]
