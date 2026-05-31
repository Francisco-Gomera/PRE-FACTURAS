from django.core.exceptions import PermissionDenied
from django.db import DatabaseError
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.utils import timezone

from .error_views import _status_response
from .server_time import get_server_tzinfo


class ServerLocalTimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tzinfo = get_server_tzinfo()
        if tzinfo is None:
            return self.get_response(request)

        timezone.activate(tzinfo)
        try:
            return self.get_response(request)
        finally:
            timezone.deactivate()


class ServerConnectionExperienceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except (Http404, PermissionDenied):
            raise
        except Exception as exc:
            if self._wants_json(request):
                return JsonResponse(
                    {
                        "detail": "No se pudo conectar con el servidor. Intenta nuevamente en unos minutos.",
                        "error_code": "server_unavailable",
                    },
                    status=500,
                )
            return self._build_html_response(request, exc)

        if self._wants_html(request):
            custom_response = self._maybe_wrap_html_status(request, response)
            if custom_response is not None:
                return custom_response
            if response.status_code >= 500:
                response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        return response

    def _wants_json(self, request):
        accept = (request.headers.get("Accept") or "").lower()
        requested_with = (request.headers.get("X-Requested-With") or "").lower()
        content_type = (request.headers.get("Content-Type") or "").lower()
        if "application/json" in accept:
            return True
        if requested_with == "xmlhttprequest":
            return True
        if "application/json" in content_type:
            return True
        return False

    def _wants_html(self, request):
        return not self._wants_json(request)

    def _build_html_response(self, request, exc):
        is_db_issue = isinstance(exc, DatabaseError)
        return _status_response(
            request,
            "500.html",
            {
                "page_title": "Servidor no disponible",
                "error_title": "No pudimos conectar con el servidor"
                if is_db_issue
                else "Algo interrumpio esta pantalla",
                "error_message": (
                    "La base de datos o el servidor central no respondieron. Tu acceso directo puede seguir "
                    "abriendo la app, pero esta pantalla necesita que el servidor este disponible."
                    if is_db_issue
                    else "La pagina no pudo completarse en este momento. Puedes volver a intentarlo en unos segundos."
                ),
                "error_hint": (
                    "Si el equipo servidor fue apagado al final de la jornada, vuelve a entrar cuando el servidor "
                    "este encendido otra vez."
                    if is_db_issue
                    else "Recarga la pagina. Si el problema continua, revisa si el servidor principal sigue encendido."
                ),
                "error_code": "HTTP 500",
            },
            500,
        )

    def _maybe_wrap_html_status(self, request, response):
        content_type = str(response.headers.get("Content-Type", "")).lower()
        if "text/html" not in content_type and content_type:
            return None
        if response.status_code == 400:
            return _status_response(request, "400.html", {}, 400)
        if response.status_code == 403:
            return _status_response(request, "403.html", {}, 403)
        if response.status_code == 404:
            return _status_response(request, "404.html", {}, 404)
        return None
