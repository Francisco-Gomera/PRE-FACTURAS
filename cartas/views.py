import base64
from datetime import datetime

from django.db import connection
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from ajustes.permissions import has_perm
from core.views import _base_context, render_denied


def index(request):
    ctx = _base_context(request, page_title="Cartas", active_nav="cartas")
    if not ctx:
        return redirect("login")
    if not has_perm(ctx["auth_payload"]["usuario_id"], "cartas", "ver"):
        return render_denied(request, active_nav="cartas")
    ctx["submodules"] = {
        "cartas_aviso": has_perm(ctx["auth_payload"]["usuario_id"], "cartas", "ver_cartas_aviso"),
        "cartas_saldo": has_perm(ctx["auth_payload"]["usuario_id"], "cartas", "ver_cartas_saldo"),
        "plantillas": has_perm(ctx["auth_payload"]["usuario_id"], "cartas", "ver_plantillas"),
    }
    return render(request, "cartas/index.html", ctx)


def saldo_view(request):
    ctx = _base_context(request, page_title="Cartas - Saldo", active_nav="cartas")
    if not ctx:
        return redirect("login")
    if not has_perm(ctx["auth_payload"]["usuario_id"], "cartas", "ver_cartas_saldo"):
        return render_denied(request, active_nav="cartas")
    return render(request, "cartas/saldo.html", ctx)


def saldo_detalle_view(request):
    ctx = _base_context(request, page_title="Cartas - Saldo", active_nav="cartas")
    if not ctx:
        return JsonResponse({"detail": "No autenticado"}, status=401)
    if not has_perm(ctx["auth_payload"]["usuario_id"], "cartas", "ver_cartas_saldo"):
        return JsonResponse({"detail": "Acceso denegado"}, status=403)

    id_sn = (request.GET.get("id_sn") or "").strip()
    if not id_sn:
        return JsonResponse({"detail": "id_sn requerido"}, status=400)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP 1 NOM_SOCIO, RNC_CED, DIR_FACTURA, CONTACTO, COMENTARIO
                FROM MAESTRO_SN
                WHERE ID_SN = %s
                """,
                [id_sn],
            )
            row = cursor.fetchone()
    except Exception:
        return JsonResponse({"detail": "No se pudo consultar el cliente."}, status=500)
    if not row:
        return JsonResponse({"detail": "Cliente no encontrado"}, status=404)

    cliente = {
        "id_sn": id_sn,
        "nombre": row[0] or "",
        "rnc_ced": row[1] or "",
        "direccion": row[2] or "",
        "contacto": row[3] or "",
        "comentario": row[4] or "",
    }

    facturas = []
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP 200 ID_DOC, FECHA_DOC, TOTAL_DOC, SALDO
                FROM CAB_FACTURA
                WHERE ID_SN = %s
                  AND ABS(ISNULL(SALDO, 0)) <= 0.0001
                  AND UPPER(ISNULL(EST_DOC, '')) = 'CERRADO'
                ORDER BY FECHA_DOC DESC, ID_DOC DESC
                """,
                [id_sn],
            )
            rows = cursor.fetchall()
    except Exception:
        return JsonResponse({"detail": "No se pudo consultar las facturas."}, status=500)

    for r in rows:
        id_doc = r[0] or ""
        fecha_doc = r[1]
        fecha_str = ""
        if isinstance(fecha_doc, datetime):
            fecha_str = fecha_doc.strftime("%d/%m/%Y")
        elif fecha_doc:
            try:
                fecha_str = fecha_doc.strftime("%d/%m/%Y")
            except Exception:
                fecha_str = str(fecha_doc)

        total_doc = float(r[2]) if r[2] is not None else 0.0
        saldo_doc = float(r[3]) if r[3] is not None else 0.0
        pagado = total_doc - saldo_doc

        fecha_pago_str = ""
        try:
            with connection.cursor() as cursor2:
                cursor2.execute(
                    """
                    SELECT MAX(d.FECHA_CONT)
                    FROM CAB_RECIBO_INGRESO c
                    INNER JOIN DET_RECIBO_INGRESO d ON c.ID_RECIBO = d.ID_RECIBO
                    WHERE c.ID_SN = %s AND d.ID_DOC = %s
                    """,
                    [id_sn, id_doc],
                )
                row_pago = cursor2.fetchone()
                if row_pago and row_pago[0]:
                    fecha_pago_dt = row_pago[0]
                    if isinstance(fecha_pago_dt, datetime):
                        fecha_pago_str = fecha_pago_dt.strftime("%d/%m/%Y")
        except Exception as e:
            fecha_pago_str = f"Error: {e}"

        facturas.append(
            {
                "id_doc": id_doc,
                "fecha_doc": fecha_str,
                "total_doc": total_doc,
                "pagado": pagado,
                "saldo": saldo_doc,
                "fecha_pago": fecha_pago_str,
            }
        )

    firma_b64 = ""
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT FIRMA FROM USUARIO WHERE ID_USUARIO = %s",
                [int(ctx["auth_payload"]["usuario_id"])],
            )
            row_firma = cursor.fetchone()
            if row_firma and row_firma[0]:
                firma_b64 = base64.b64encode(row_firma[0]).decode("ascii")
    except Exception:
        firma_b64 = ""

    empresa = (ctx or {}).get("empresa") or {}

    return JsonResponse(
        {
            "cliente": cliente,
            "facturas": facturas,
            "fecha": timezone.localdate().strftime("%d/%m/%Y"),
            "hora": timezone.localtime().strftime("%I:%M:%S %p").lstrip("0"),
            "firma_b64": firma_b64,
            "empresa": {
                "nombre": empresa.get("nombre", ""),
                "direccion": empresa.get("direccion", ""),
                "tel1": empresa.get("tel1", ""),
                "tel2": empresa.get("tel2", ""),
                "email": empresa.get("email", ""),
                "rnc": empresa.get("rnc", ""),
                "logo_b64": empresa.get("logo_b64", ""),
                "logo_tipo": empresa.get("logo_tipo", ""),
                "sello_b64": empresa.get("sello_b64", ""),
            },
        }
    )
