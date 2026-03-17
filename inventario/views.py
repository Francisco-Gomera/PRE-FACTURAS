from django.shortcuts import redirect, render

from ajustes.permissions import has_perm
from core.views import _base_context, render_denied


def index(request):
    ctx = _base_context(request, page_title="Inventario", active_nav="inventario")
    if not ctx:
        return redirect("login")
    if not has_perm(ctx["auth_payload"]["usuario_id"], "inventario", "ver"):
        return render_denied(request, active_nav="inventario")
    ctx["submodules"] = {
        "articulos": has_perm(ctx["auth_payload"]["usuario_id"], "inventario", "ver_articulos"),
        "grupos": has_perm(ctx["auth_payload"]["usuario_id"], "inventario", "ver_grupos"),
        "stock": has_perm(ctx["auth_payload"]["usuario_id"], "inventario", "ver_stock"),
    }
    return render(request, "inventario/index.html", ctx)


def grupos_view(request):
    ctx = _base_context(request, page_title="Grupos de articulos", active_nav="inventario")
    if not ctx:
        return redirect("login")
    if not has_perm(ctx["auth_payload"]["usuario_id"], "inventario", "ver_grupos"):
        return render_denied(request, active_nav="inventario")
    return render(request, "inventario/grupos.html", ctx)


def stock_view(request):
    ctx = _base_context(request, page_title="Stock de articulos", active_nav="inventario")
    if not ctx:
        return redirect("login")
    if not has_perm(ctx["auth_payload"]["usuario_id"], "inventario", "ver_stock"):
        return render_denied(request, active_nav="inventario")
    return render(request, "inventario/stock.html", ctx)
