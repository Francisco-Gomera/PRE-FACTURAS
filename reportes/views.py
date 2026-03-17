from django.shortcuts import redirect, render

from ajustes.permissions import has_perm
from core.views import _base_context, render_denied


def index(request):
    ctx = _base_context(request, page_title="Reportes", active_nav="reportes")
    if not ctx:
        return redirect("login")
    if not has_perm(ctx["auth_payload"]["usuario_id"], "reportes", "ver"):
        return render_denied(request, active_nav="reportes")
    ctx["submodules"] = {
        "ventas": has_perm(ctx["auth_payload"]["usuario_id"], "reportes", "ver_ventas"),
        "clientes": has_perm(ctx["auth_payload"]["usuario_id"], "reportes", "ver_clientes"),
        "inventario": has_perm(ctx["auth_payload"]["usuario_id"], "reportes", "ver_inventario"),
    }
    return render(request, "reportes/index.html", ctx)
