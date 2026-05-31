import mimetypes
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse, HttpResponseServerError
from django.shortcuts import render
from django.urls import reverse


def _status_response(request, template_name, context, status_code):
    response = render(request, template_name, context, status=status_code)
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response


def bad_request_view(request, exception=None):
    return _status_response(request, "400.html", {}, 400)


def permission_denied_view(request, exception=None):
    return _status_response(request, "403.html", {}, 403)


def page_not_found_view(request, exception=None):
    return _status_response(request, "404.html", {}, 404)


def server_error_view(request, exception=None):
    return _status_response(
        request,
        "500.html",
        {
            "page_title": "Servidor no disponible",
            "error_title": "No pudimos conectar con el servidor",
            "error_message": (
                "La aplicacion sigue disponible en tu dispositivo, pero el servidor o la base de datos "
                "no respondieron en este momento."
            ),
            "error_hint": (
                "Si el equipo servidor fue apagado al final de la jornada, vuelve a intentarlo cuando el "
                "servidor este encendido otra vez."
            ),
            "error_code": "HTTP 500",
        },
        500,
    )


def offline_view(request):
    return render(
        request,
        "offline.html",
        {
            "page_title": "Servidor en pausa",
        },
    )


def _media_search_roots():
    roots = []
    primary = Path(settings.MEDIA_ROOT)
    roots.append(primary)
    secondary = primary.parent.parent / "media"
    if secondary not in roots:
        roots.append(secondary)
    return roots


def media_file_view(request, path):
    relative_path = str(path or "").strip().replace("\\", "/").lstrip("/")
    if not relative_path:
        raise Http404()
    for root in _media_search_roots():
        try:
            candidate = (Path(root) / relative_path).resolve()
            root_resolved = Path(root).resolve()
        except Exception:
            continue
        if root_resolved not in candidate.parents and candidate != root_resolved:
            continue
        if candidate.exists() and candidate.is_file():
            content_type, _ = mimetypes.guess_type(str(candidate))
            response = FileResponse(open(candidate, "rb"), content_type=content_type or "application/octet-stream")
            response["Cache-Control"] = "no-cache"
            return response
    raise Http404()


def service_worker_view(request):
    script = f"""
const CACHE_NAME = "ca-erp-shell-v2";
const OFFLINE_URL = "{reverse('app_offline')}";

self.addEventListener("install", (event) => {{
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll([OFFLINE_URL]))
      .then(() => self.skipWaiting())
  );
}});

self.addEventListener("activate", (event) => {{
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
    )).then(() => self.clients.claim())
  );
}});

self.addEventListener("fetch", (event) => {{
  if (event.request.method !== "GET") {{
    return;
  }}

  if (event.request.mode === "navigate") {{
    event.respondWith(
      fetch(event.request).catch(() => caches.match(OFFLINE_URL))
    );
  }}
}});

self.addEventListener("notificationclick", (event) => {{
  const targetUrl = event.notification?.data?.url || "/";
  event.notification.close();
  event.waitUntil(
    clients.matchAll({{ type: "window", includeUncontrolled: true }}).then((clientList) => {{
      for (const client of clientList) {{
        if ("focus" in client) {{
          client.postMessage({{ type: "ca-erp-focus-url", url: targetUrl }});
          return client.focus();
        }}
      }}
      if (clients.openWindow) {{
        return clients.openWindow(targetUrl);
      }}
      return undefined;
    }})
  );
}});
"""
    response = HttpResponse(script, content_type="application/javascript; charset=utf-8")
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"
    return response
