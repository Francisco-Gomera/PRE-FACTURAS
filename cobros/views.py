from django.shortcuts import redirect, render

from ajustes.permissions import has_perm
from core.views import _base_context, render_denied


def index(request):
    ctx = _base_context(request, page_title="Gestion de cobros", active_nav="cobros")
    if not ctx:
        return redirect("login")
    if not has_perm(ctx["auth_payload"]["usuario_id"], "cobros", "ver"):
        return render_denied(request, active_nav="cobros")
    ctx["submodules"] = {
        "estado_cuenta": has_perm(ctx["auth_payload"]["usuario_id"], "cobros", "ver_estado_cuenta"),
        "alertas": has_perm(ctx["auth_payload"]["usuario_id"], "cobros", "ver_alertas"),
        "acuerdos": has_perm(ctx["auth_payload"]["usuario_id"], "cobros", "ver_acuerdos"),
    }
    return render(request, "cobros/index.html", ctx)
