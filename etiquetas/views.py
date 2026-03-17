from django.shortcuts import redirect, render

from ajustes.permissions import has_perm
from core.views import _base_context, render_denied


def index(request):
    ctx = _base_context(request, page_title="Etiquetas", active_nav="etiquetas")
    if not ctx:
        return redirect("login")
    if not has_perm(ctx["auth_payload"]["usuario_id"], "etiquetas", "ver"):
        return render_denied(request, active_nav="etiquetas")
    ctx["submodules"] = {
        "formatos": has_perm(ctx["auth_payload"]["usuario_id"], "etiquetas", "ver_formatos"),
        "impresion": has_perm(ctx["auth_payload"]["usuario_id"], "etiquetas", "ver_impresion"),
        "historial": has_perm(ctx["auth_payload"]["usuario_id"], "etiquetas", "ver_historial"),
    }
    return render(request, "etiquetas/index.html", ctx)


def formatos_view(request):
    ctx = _base_context(request, page_title="Etiquetas - Formatos", active_nav="etiquetas")
    if not ctx:
        return redirect("login")
    if not has_perm(ctx["auth_payload"]["usuario_id"], "etiquetas", "ver_formatos"):
        return render_denied(request, active_nav="etiquetas")
    return render(request, "etiquetas/formatos.html", ctx)


def impresion_view(request):
    ctx = _base_context(request, page_title="Etiquetas - Impresion", active_nav="etiquetas")
    if not ctx:
        return redirect("login")
    if not has_perm(ctx["auth_payload"]["usuario_id"], "etiquetas", "ver_impresion"):
        return render_denied(request, active_nav="etiquetas")
    return render(request, "etiquetas/impresion.html", ctx)
