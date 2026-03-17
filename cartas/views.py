import base64
from datetime import datetime

from django.db import connection
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import CartaPlantilla
from ajustes.permissions import has_perm
from core.views import _base_context, render_denied


def _fmt_date(value):
    if not value:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%d/%m/%Y")
    return str(value)


def _to_float(value):
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _days_overdue(value):
    if not value:
        return 0
    try:
        d = value.date() if hasattr(value, "date") else value
        return max((timezone.localdate() - d).days, 0)
    except Exception:
        return 0


def _load_cliente_carta(id_sn):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT TOP 1
                m.NOM_SOCIO,
                m.RNC_CED,
                m.DIR_FACTURA,
                m.CONTACTO,
                m.COMENTARIO,
                m.TEL1,
                m.MORA,
                m.TARIFA_INT,
                m.ID_SECTOR,
                ISNULL(t.DESCRIPCION, '')
            FROM MAESTRO_SN m
            LEFT JOIN Territorio t ON t.ID_CODIGO = m.ID_SECTOR
            WHERE m.ID_SN = %s
            """,
            [id_sn],
        )
        row = cursor.fetchone()
    if not row:
        return None
    return {
        "id_sn": id_sn,
        "nombre": row[0] or "",
        "rnc_ced": row[1] or "",
        "direccion": row[2] or "",
        "contacto": row[3] or "",
        "comentario": row[4] or "",
        "telefono": row[5] or "",
        "mora": _to_float(row[6]),
        "tarifa_int": _to_float(row[7]),
        "id_sector": row[8],
        "sector": row[9] or "",
    }


def _load_firma_b64(usuario_id):
    firma_b64 = ""
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT FIRMA FROM USUARIO WHERE ID_USUARIO = %s",
                [int(usuario_id)],
            )
            row_firma = cursor.fetchone()
            if row_firma and row_firma[0]:
                firma_b64 = base64.b64encode(row_firma[0]).decode("ascii")
    except Exception:
        firma_b64 = ""
    return firma_b64


def _build_empresa_payload(ctx):
    empresa = (ctx or {}).get("empresa") or {}
    return {
        "nombre": empresa.get("nombre", ""),
        "direccion": empresa.get("direccion", ""),
        "tel1": empresa.get("tel1", ""),
        "tel2": empresa.get("tel2", ""),
        "email": empresa.get("email", ""),
        "rnc": empresa.get("rnc", ""),
        "logo_b64": empresa.get("logo_b64", ""),
        "logo_tipo": empresa.get("logo_tipo", ""),
        "sello_b64": empresa.get("sello_b64", ""),
    }


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


from .models import CartaPlantilla


def aviso_view(request):
    ctx = _base_context(request, page_title="Cartas - Aviso", active_nav="cartas")
    if not ctx:
        return redirect("login")
    if not has_perm(ctx["auth_payload"]["usuario_id"], "cartas", "ver_cartas_aviso"):
        return render_denied(request, active_nav="cartas")
    return render(request, "cartas/aviso.html", ctx)


def plantillas_view(request):
    ctx = _base_context(request, page_title="Cartas - Plantillas", active_nav="cartas")
    if not ctx:
        return redirect("login")
    if not has_perm(ctx["auth_payload"]["usuario_id"], "cartas", "ver_plantillas"):
        return render_denied(request, active_nav="cartas")

    plantillas = CartaPlantilla.objects.all()
    ctx["plantillas"] = plantillas
    return render(request, "cartas/plantillas.html", ctx)




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
        cliente = _load_cliente_carta(id_sn)
    except Exception:
        return JsonResponse({"detail": "No se pudo consultar el cliente."}, status=500)
    if not cliente:
        return JsonResponse({"detail": "Cliente no encontrado"}, status=404)

    facturas = []
    cuotas_meta_by_doc = {}
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

        docs = [row[0] for row in rows if row and row[0]]
        if docs:
            placeholders = ", ".join(["%s"] * len(docs))
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT NO_DOC, COUNT(*), MAX(NO_CUOTA)
                    FROM DET_PRESTAMO
                    WHERE NO_DOC IN ({placeholders})
                    GROUP BY NO_DOC
                    """,
                    docs,
                )
                for no_doc, total_cuotas, max_no_cuota in cursor.fetchall():
                    cuotas_meta_by_doc[no_doc] = {
                        "total_cuotas": int(total_cuotas or 0),
                        "no_cuota": max_no_cuota,
                    }
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

        total_doc = _to_float(r[2])
        saldo_doc = _to_float(r[3])
        pagado = total_doc - saldo_doc

        fecha_pago_str = ""
        try:
            with connection.cursor() as cursor2:
                cursor2.execute(
                    """
                    SELECT MAX(d.FECHA_CONT)
                    FROM CAB_RECIBO_INGRESO c
                    INNER JOIN DET_RECIBO_INGRESO d ON c.ID_RECIBO = d.ID_RECIBO
                    WHERE c.ID_SN = %s AND d.NO_DOC = %s
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
                "no_cuota": str(cuotas_meta_by_doc.get(id_doc, {}).get("no_cuota") or "Abierto"),
                "fecha_doc": fecha_str,
                "total_doc": total_doc,
                "pagado": pagado,
                "saldo": saldo_doc,
                "fecha_pago": fecha_pago_str,
            }
        )

    firma_b64 = _load_firma_b64(ctx["auth_payload"]["usuario_id"])

    return JsonResponse(
        {
            "cliente": cliente,
            "facturas": facturas,
            "fecha": timezone.localdate().strftime("%d/%m/%Y"),
            "hora": timezone.localtime().strftime("%I:%M:%S %p").lstrip("0"),
            "firma_b64": firma_b64,
            "empresa": _build_empresa_payload(ctx),
        }
    )


def aviso_detalle_view(request):
    ctx = _base_context(request, page_title="Cartas - Aviso", active_nav="cartas")
    if not ctx:
        return JsonResponse({"detail": "No autenticado"}, status=401)
    if not has_perm(ctx["auth_payload"]["usuario_id"], "cartas", "ver_cartas_aviso"):
        return JsonResponse({"detail": "Acceso denegado"}, status=403)

    id_sn = (request.GET.get("id_sn") or "").strip()
    if not id_sn:
        return JsonResponse({"detail": "id_sn requerido"}, status=400)

    try:
        cliente = _load_cliente_carta(id_sn)
    except Exception:
        return JsonResponse({"detail": "No se pudo consultar el cliente."}, status=500)
    if not cliente:
        return JsonResponse({"detail": "Cliente no encontrado"}, status=404)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT FECHA_DOC, ID_DOC, TOTAL_DOC, SALDO, FECHA_VENC
                FROM CAB_FACTURA
                WHERE ID_SN = %s
                  AND UPPER(ISNULL(EST_DOC, '')) = 'ABIERTO'
                ORDER BY FECHA_DOC, ID_DOC
                """,
                [id_sn],
            )
            rows = cursor.fetchall()
    except Exception:
        return JsonResponse({"detail": "No se pudo consultar los balances pendientes."}, status=500)

    docs = [row[1] for row in rows if row[1] is not None]
    cuotas_by_doc = {}
    if docs:
        try:
            placeholders = ", ".join(["%s"] * len(docs))
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT NO_DOC, NO_CUOTA, FECHA, FECHA_VENC, CUOTA, BALANCE, SALDO_INSOLUTO
                    FROM DET_PRESTAMO
                    WHERE NO_DOC IN ({placeholders})
                    ORDER BY NO_DOC, NO_CUOTA
                    """,
                    docs,
                )
                cuotas_rows = cursor.fetchall()
            for c in cuotas_rows:
                no_doc = c[0]
                cuotas_by_doc.setdefault(no_doc, []).append(
                    {
                        "no_cuota": c[1],
                        "fecha": c[2],
                        "fecha_venc": c[3],
                        "cuota": c[4],
                        "balance": c[5],
                        "saldo_insoluto": c[6],
                    }
                )
        except Exception:
            cuotas_by_doc = {}

    facturas = []
    total_saldo = 0.0
    total_mora = 0.0
    tarifa_int = cliente.get("tarifa_int") or 0.0

    for row in rows:
        fecha_doc, id_doc, total_doc, saldo_doc, fecha_venc = row
        cuotas = cuotas_by_doc.get(id_doc, [])
        if cuotas:
            for cuota in cuotas:
                saldo_cuota = cuota.get("balance")
                if saldo_cuota is None:
                    saldo_cuota = cuota.get("saldo_insoluto")
                saldo_val = _to_float(saldo_cuota)
                if saldo_val <= 0:
                    continue
                fecha_venc_cuota = cuota.get("fecha_venc") or fecha_venc
                dias = _days_overdue(fecha_venc_cuota)
                if dias <= 0:
                    continue
                monto = _to_float(cuota.get("cuota"))
                pagado = max(monto - saldo_val, 0.0)
                mora = (saldo_val * tarifa_int / 100.0) * dias if tarifa_int > 0 else 0.0
                facturas.append(
                    {
                        "id_doc": id_doc or "",
                        "no_cuota": cuota.get("no_cuota") or "Abierto",
                        "fecha_doc": _fmt_date(cuota.get("fecha") or fecha_doc),
                        "fecha_venc": _fmt_date(fecha_venc_cuota),
                        "monto": monto,
                        "pagado": pagado,
                        "saldo": saldo_val,
                        "dias": dias,
                        "mora": mora,
                    }
                )
                total_saldo += saldo_val
                total_mora += mora
        else:
            saldo_val = _to_float(saldo_doc)
            if saldo_val <= 0:
                continue
            dias = _days_overdue(fecha_venc)
            if dias <= 0:
                continue
            total_doc_val = _to_float(total_doc)
            pagado = max(total_doc_val - saldo_val, 0.0)
            mora = (saldo_val * tarifa_int / 100.0) * dias if tarifa_int > 0 else 0.0
            facturas.append(
                {
                    "id_doc": id_doc or "",
                    "no_cuota": "Abierto",
                    "fecha_doc": _fmt_date(fecha_doc),
                    "fecha_venc": _fmt_date(fecha_venc),
                    "monto": total_doc_val,
                    "pagado": pagado,
                    "saldo": saldo_val,
                    "dias": dias,
                    "mora": mora,
                }
            )
            total_saldo += saldo_val
            total_mora += mora

    firma_b64 = _load_firma_b64(ctx["auth_payload"]["usuario_id"])

    return JsonResponse(
        {
            "cliente": cliente,
            "facturas": facturas,
            "fecha": timezone.localdate().strftime("%d/%m/%Y"),
            "hora": timezone.localtime().strftime("%I:%M:%S %p").lstrip("0"),
            "firma_b64": firma_b64,
            "empresa": _build_empresa_payload(ctx),
            "totales": {
                "saldo": total_saldo,
                "mora": total_mora,
            },
        }
    )
