from django.db import connection
from django.shortcuts import redirect, render

from ajustes.permissions import has_perm
from core.views import _base_context, render_denied


def index(request):
    ctx = _base_context(request, page_title="Clientes", active_nav="clientes")
    if not ctx:
        return redirect("login")
    if not has_perm(ctx["auth_payload"]["usuario_id"], "clientes", "ver"):
        return render_denied(request, active_nav="clientes")
    sectores = []
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT ID_CODIGO, DESCRIPCION
                FROM Territorio
                WHERE DESCRIPCION IS NOT NULL AND LTRIM(RTRIM(DESCRIPCION)) <> ''
                ORDER BY DESCRIPCION
                """
            )
            sectores = [
                {"id_codigo": row[0], "descripcion": row[1]}
                for row in cursor.fetchall()
            ]
    except Exception:
        sectores = []
    ctx["sectores"] = sectores
    return render(request, "clientes_mod/index.html", ctx)
