from django.shortcuts import redirect, render

from ajustes.permissions import has_perm
from core.views import _base_context, render_denied


def index(request):
    ctx = _base_context(request, page_title="Prefacturas", active_nav="prefacturas")
    if not ctx:
        return redirect("login")
    if not has_perm(ctx["auth_payload"]["usuario_id"], "prefacturas", "ver"):
        return render_denied(request, active_nav="prefacturas")
    usuario_id = ctx["auth_payload"]["usuario_id"]
    ctx["quick_access"] = {
        "clientes": has_perm(usuario_id, "clientes", "ver"),
        "grupos": has_perm(usuario_id, "inventario", "ver")
        and has_perm(usuario_id, "inventario", "ver_grupos"),
        "stock": has_perm(usuario_id, "inventario", "ver")
        and has_perm(usuario_id, "inventario", "ver_stock"),
        "etiquetas": has_perm(usuario_id, "etiquetas", "ver")
        and has_perm(usuario_id, "etiquetas", "ver_impresion"),
    }
    return render(request, "prefacturas_mod/index.html", ctx)
