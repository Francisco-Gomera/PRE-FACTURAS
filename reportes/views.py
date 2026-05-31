from decimal import Decimal

from django.db import connection
from django.shortcuts import redirect, render
from django.utils import timezone

from ajustes.permissions import has_perm
from caja.views import (
    _doc_sort_key,
    _fmt_date,
    _fmt_date_input,
    _load_cuadre_caja_terminales,
    _load_cuadre_caja_usuarios,
    _normalize_result_row,
    _parse_date_value,
    _pick_amount_value,
    _pick_existing_column,
    _pick_row_text,
    _pick_row_value,
    _to_float,
    _unique_columns,
)
from core.views import _base_context, render_denied


def _money(value):
    return f"{_to_float(value):,.2f}"


def _chunked(values, size=250):
    for idx in range(0, len(values), size):
        yield values[idx : idx + size]


def _load_table_columns(table_name):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
            """,
            [table_name],
        )
        return [str(row[0]).strip().upper() for row in cursor.fetchall() if row and row[0]]


def _date_key(value):
    parsed = _parse_date_value(value)
    if parsed:
        return parsed.isoformat()
    return ""


def _load_clientes_nombres(cliente_ids):
    ids = [str(value or "").strip() for value in cliente_ids if str(value or "").strip()]
    ids = list(dict.fromkeys(ids))
    if not ids:
        return {}

    columns = _load_table_columns("MAESTRO_SN")
    id_col = _pick_existing_column(columns, "ID_SN")
    nombre_col = _pick_existing_column(columns, "NOM_SOCIO", "NOM_SN", "NOMBRE", "NOM_CLIENTE")
    if not id_col or not nombre_col:
        return {}

    lookup = {}
    for ids_chunk in _chunked(ids):
        placeholders = ", ".join(["%s"] * len(ids_chunk))
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT CAST([{id_col}] AS NVARCHAR(255)), CAST([{nombre_col}] AS NVARCHAR(255))
                FROM MAESTRO_SN
                WHERE CAST([{id_col}] AS NVARCHAR(255)) IN ({placeholders})
                """,
                ids_chunk,
            )
            for raw_id, raw_name in cursor.fetchall():
                client_id = str(raw_id or "").strip()
                name = str(raw_name or "").strip()
                if client_id and name:
                    lookup[client_id] = name
    return lookup


def _load_facturacion_terminales():
    columns = _load_table_columns("CAB_FACTURA")
    terminal_col = _pick_existing_column(columns, "TERMINAL")
    if not terminal_col:
        return []

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT DISTINCT LTRIM(RTRIM(CAST([{terminal_col}] AS NVARCHAR(255)))) AS TERMINAL
                FROM CAB_FACTURA
                WHERE NULLIF(LTRIM(RTRIM(CAST([{terminal_col}] AS NVARCHAR(255)))), '') IS NOT NULL
                ORDER BY TERMINAL
                """
            )
            return [
                {"terminal": str(row[0] or "").strip(), "label": str(row[0] or "").strip()}
                for row in cursor.fetchall()
                if str(row[0] or "").strip()
            ]
    except Exception:
        return []


def _det_recibo_pago_amount(row):
    return Decimal(
        str(
            _pick_amount_value(
                row,
                "TOTAL_PAGO",
                "TOTAL_PAGO2",
                "SALDO_VENC",
                "PAGO_ABONO",
                "IMP_ABONO",
                "IMP_PAGADO",
                "ABONO",
                "PAGO",
                "COBRO",
                "MONTO",
                "IMPORTE",
                default=0,
            )
            or 0
        )
    )


def _det_recibo_discount_amount(row):
    return Decimal(
        str(
            _pick_amount_value(
                row,
                "DESCUENTO",
                "DESC_AVANCE",
                "AVANCE",
                "DESC",
                default=0,
            )
            or 0
        )
    )


def _load_caja_aplicaciones_por_recibo(recibo_refs):
    refs = [str(value or "").strip() for value in recibo_refs if str(value or "").strip()]
    refs = list(dict.fromkeys(refs))
    if not refs:
        return {}

    det_columns = _load_table_columns("DET_RECIBO_INGRESO")
    if not det_columns:
        return {}
    det_recibo_col = _pick_existing_column(det_columns, "ID_RECIBO", "NO_RECIBO", "ID_DOC", "NO_DOC")
    if not det_recibo_col:
        return {}

    lookup = {}
    for refs_chunk in _chunked(refs):
        placeholders = ", ".join(["%s"] * len(refs_chunk))
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT *
                FROM DET_RECIBO_INGRESO
                WHERE CAST([{det_recibo_col}] AS NVARCHAR(255)) IN ({placeholders})
                """,
                refs_chunk,
            )
            raw_columns = [col[0] for col in cursor.description]
            for raw_row in cursor.fetchall():
                row = _normalize_result_row(raw_columns, raw_row)
                recibo_ref = _pick_row_text(row, det_recibo_col)
                if not recibo_ref:
                    continue
                current = lookup.setdefault(recibo_ref, {"pago": Decimal("0"), "descuento": Decimal("0")})
                current["pago"] += _det_recibo_pago_amount(row)
                current["descuento"] += _det_recibo_discount_amount(row)
    return lookup


def _load_caja_report(fecha_desde, fecha_hasta, *, usuario_filtro="", terminal_filtro=""):
    cab_columns = _load_table_columns("CAB_RECIBO_INGRESO")
    if not cab_columns:
        return [], {"cantidad": 0, "total_recibos": 0, "total_aplicado": 0, "total_descuento": 0}

    fecha_col = _pick_existing_column(cab_columns, "FECHA_CONT", "F_CONT", "FECHA_DOC", "FECHA")
    id_col = _pick_existing_column(cab_columns, "ID_RECIBO", "NO_RECIBO", "ID_DOC", "NO_DOC")
    no_recibo_col = _pick_existing_column(cab_columns, "NO_RECIBO", "ID_RECIBO", "ID_DOC", "NO_DOC")
    cliente_col = _pick_existing_column(cab_columns, "NOM_SN", "NOM_SOCIO", "NOMBRE", "NOM_CLIENTE")
    id_sn_col = _pick_existing_column(cab_columns, "ID_SN", "CLIENTE", "COD_CLIENTE")
    total_col = _pick_existing_column(cab_columns, "TOTAL_COBRO", "TOTAL_DOC", "IMPORTE", "MONTO")
    descuento_col = _pick_existing_column(cab_columns, "TOTAL_DESCTO", "TOTAL_DESC", "DESCUENTO", "DESC_AVANCE")
    efectivo_col = _pick_existing_column(cab_columns, "IMP_EFECTIVO", "EFECTIVO", "MONTO_EFECTIVO", "PAGO_EFECTIVO")
    transferencia_col = _pick_existing_column(
        cab_columns,
        "IMP_TRANSF",
        "TRANSFERENCIA",
        "MONTO_TRANSFERENCIA",
        "PAGO_TRANSFERENCIA",
    )
    usuario_col = _pick_existing_column(cab_columns, "ID_USUARIO", "USUARIO_ID")
    usuario_nombre_col = _pick_existing_column(cab_columns, "USUARIO", "USUARIO_NOMBRE")
    terminal_col = _pick_existing_column(cab_columns, "TERMINAL")
    estado_col = _pick_existing_column(cab_columns, "ESTATUS", "EST_DOC", "ESTADO")
    cancelado_col = _pick_existing_column(cab_columns, "CANCELADO")
    if not fecha_col or not id_col:
        return [], {"cantidad": 0, "total_recibos": 0, "total_aplicado": 0, "total_descuento": 0}

    selected_columns = _unique_columns(
        fecha_col,
        id_col,
        no_recibo_col,
        cliente_col,
        id_sn_col,
        total_col,
        descuento_col,
        efectivo_col,
        transferencia_col,
        usuario_col,
        usuario_nombre_col,
        terminal_col,
        estado_col,
        cancelado_col,
    )
    where_parts = [f"CONVERT(date, [{fecha_col}]) BETWEEN %s AND %s"]
    params = [fecha_desde, fecha_hasta]
    if usuario_filtro and usuario_col:
        where_parts.append(f"CAST([{usuario_col}] AS NVARCHAR(255)) = %s")
        params.append(usuario_filtro)
    if terminal_filtro and terminal_col:
        where_parts.append(f"LTRIM(RTRIM(CAST([{terminal_col}] AS NVARCHAR(255)))) = %s")
        params.append(terminal_filtro)
    if estado_col:
        where_parts.append(f"UPPER(LTRIM(RTRIM(ISNULL(CAST([{estado_col}] AS NVARCHAR(255)), '')))) <> 'CANCELADO'")
    if cancelado_col:
        where_parts.append(f"UPPER(LTRIM(RTRIM(ISNULL(CAST([{cancelado_col}] AS NVARCHAR(255)), 'N')))) NOT IN ('Y', 'S', 'SI', '1', 'TRUE')")

    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT {", ".join(f"[{column}]" for column in selected_columns)}
            FROM CAB_RECIBO_INGRESO
            WHERE {" AND ".join(where_parts)}
            ORDER BY [{fecha_col}], TRY_CAST([{id_col}] AS BIGINT), [{id_col}]
            """,
            params,
        )
        raw_columns = [col[0] for col in cursor.description]
        rows = []
        for raw_row in cursor.fetchall():
            row = _normalize_result_row(raw_columns, raw_row)
            no_recibo = _pick_row_text(row, no_recibo_col, id_col)
            recibo_key = _pick_row_text(row, id_col, no_recibo_col)
            efectivo = _pick_amount_value(row, efectivo_col, default=0)
            transferencia = _pick_amount_value(row, transferencia_col, default=0)
            total_header = _pick_amount_value(row, total_col, default=0)
            descuento_header = _pick_amount_value(row, descuento_col, default=0)
            total_recibo = total_header if abs(_to_float(total_header)) > 0.0001 else efectivo + transferencia
            rows.append(
                {
                    "fecha": _fmt_date(_pick_row_value(row, fecha_col)),
                    "no_recibo": no_recibo,
                    "recibo_key": recibo_key,
                    "no_recibo_sort": _doc_sort_key(no_recibo),
                    "cliente_id": _pick_row_text(row, id_sn_col),
                    "cliente": _pick_row_text(row, cliente_col) or "Sin cliente",
                    "usuario_id": _pick_row_text(row, usuario_col),
                    "usuario_label": _pick_row_text(row, usuario_nombre_col) or _pick_row_text(row, usuario_col) or "Sin usuario",
                    "terminal": _pick_row_text(row, terminal_col) or "Sin terminal",
                    "efectivo": efectivo,
                    "efectivo_fmt": _money(efectivo),
                    "transferencia": transferencia,
                    "transferencia_fmt": _money(transferencia),
                    "total_recibo": total_recibo,
                    "total_recibo_fmt": _money(total_recibo),
                    "descuento_aplicado": descuento_header,
                    "descuento_aplicado_fmt": _money(descuento_header),
                    "total_aplicado": total_recibo + descuento_header,
                    "total_aplicado_fmt": _money(total_recibo + descuento_header),
                }
            )

    aplicaciones = _load_caja_aplicaciones_por_recibo(
        [item.get("recibo_key") for item in rows] + [item.get("no_recibo") for item in rows]
    )
    clientes_lookup = _load_clientes_nombres([item.get("cliente_id") for item in rows])
    for item in rows:
        for ref in _unique_columns(item.get("recibo_key"), item.get("no_recibo")):
            applied = aplicaciones.get(str(ref or "").strip())
            if applied:
                pago = applied.get("pago", Decimal("0"))
                descuento = applied.get("descuento", Decimal("0"))
                item["descuento_aplicado"] = descuento
                item["descuento_aplicado_fmt"] = _money(descuento)
                item["total_aplicado"] = pago + descuento
                item["total_aplicado_fmt"] = _money(pago + descuento)
                break
        cliente_id = item.get("cliente_id") or ""
        if item.get("cliente") == "Sin cliente" and cliente_id:
            item["cliente"] = clientes_lookup.get(cliente_id) or item["cliente"]

    totales = {
        "cantidad": len(rows),
        "total_recibos": sum(_to_float(item["total_recibo"]) for item in rows),
        "total_aplicado": sum(_to_float(item["total_aplicado"]) for item in rows),
        "total_descuento": sum(_to_float(item["descuento_aplicado"]) for item in rows),
    }
    totales.update(
        {
            "total_recibos_fmt": _money(totales["total_recibos"]),
            "total_aplicado_fmt": _money(totales["total_aplicado"]),
            "total_descuento_fmt": _money(totales["total_descuento"]),
        }
    )
    return rows, totales


def _det_recibo_payment_amount(row):
    return _det_recibo_pago_amount(row) + _det_recibo_discount_amount(row)


def _load_pagos_facturas_en_fecha(facturas):
    if not facturas:
        return {}

    det_columns = _load_table_columns("DET_RECIBO_INGRESO")
    cab_columns = _load_table_columns("CAB_RECIBO_INGRESO")
    if not det_columns or not cab_columns:
        return {}

    det_doc_col = _pick_existing_column(det_columns, "NO_DOC", "ID_DOC", "DOCUMENTO", "FACTURA")
    det_recibo_col = _pick_existing_column(det_columns, "ID_RECIBO", "NO_RECIBO", "ID_DOC", "NO_DOC")
    cab_key_col = _pick_existing_column(cab_columns, "ID_RECIBO", "NO_RECIBO", "ID_DOC", "NO_DOC")
    cab_no_col = _pick_existing_column(cab_columns, "NO_RECIBO", "ID_RECIBO", "ID_DOC", "NO_DOC")
    cab_fecha_col = _pick_existing_column(cab_columns, "FECHA_CONT", "F_CONT", "FECHA_DOC", "FECHA")
    cab_estado_col = _pick_existing_column(cab_columns, "ESTATUS", "EST_DOC", "ESTADO")
    cab_cancelado_col = _pick_existing_column(cab_columns, "CANCELADO")
    if not det_doc_col or not det_recibo_col or not cab_key_col or not cab_fecha_col:
        return {}

    factura_fecha = {item["no_factura"]: item["fecha_key"] for item in facturas if item.get("no_factura")}
    docs = list(dict.fromkeys(factura_fecha.keys()))
    detail_rows = []
    recibo_refs = set()

    for docs_chunk in _chunked(docs):
        placeholders = ", ".join(["%s"] * len(docs_chunk))
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT *
                FROM DET_RECIBO_INGRESO
                WHERE CAST([{det_doc_col}] AS NVARCHAR(255)) IN ({placeholders})
                """,
                docs_chunk,
            )
            raw_columns = [col[0] for col in cursor.description]
            for raw_row in cursor.fetchall():
                row = _normalize_result_row(raw_columns, raw_row)
                detail_rows.append(row)
                recibo_ref = _pick_row_text(row, det_recibo_col, "ID_RECIBO", "NO_RECIBO")
                if recibo_ref:
                    recibo_refs.add(recibo_ref)

    if not detail_rows or not recibo_refs:
        return {}

    recibos = {}
    refs = list(dict.fromkeys(recibo_refs))
    for refs_chunk in _chunked(refs):
        params = []
        where_parts = []
        placeholders = ", ".join(["%s"] * len(refs_chunk))
        for column in _unique_columns(cab_key_col, cab_no_col):
            where_parts.append(f"CAST([{column}] AS NVARCHAR(255)) IN ({placeholders})")
            params.extend(refs_chunk)
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM CAB_RECIBO_INGRESO WHERE {' OR '.join(f'({part})' for part in where_parts)}",
                params,
            )
            raw_columns = [col[0] for col in cursor.description]
            for raw_row in cursor.fetchall():
                row = _normalize_result_row(raw_columns, raw_row)
                estado = _pick_row_text(row, cab_estado_col).upper()
                cancelado = _pick_row_text(row, cab_cancelado_col).upper()
                if estado == "CANCELADO" or cancelado in {"Y", "S", "SI", "1", "TRUE"}:
                    continue
                recibo_date = _date_key(_pick_row_value(row, cab_fecha_col))
                for column in _unique_columns(cab_key_col, cab_no_col):
                    ref = _pick_row_text(row, column)
                    if ref:
                        recibos[ref] = recibo_date

    pagos = {}
    for row in detail_rows:
        no_factura = _pick_row_text(row, det_doc_col, "NO_DOC", "ID_DOC", "DOCUMENTO", "FACTURA")
        recibo_ref = _pick_row_text(row, det_recibo_col, "ID_RECIBO", "NO_RECIBO")
        if not no_factura or not recibo_ref:
            continue
        if recibos.get(recibo_ref) != factura_fecha.get(no_factura):
            continue
        monto = _det_recibo_payment_amount(row)
        if monto <= 0:
            continue
        pagos[no_factura] = pagos.get(no_factura, Decimal("0")) + monto
    return pagos


def _load_facturacion_report(fecha_desde, fecha_hasta, *, usuario_filtro="", terminal_filtro=""):
    columns = _load_table_columns("CAB_FACTURA")
    if not columns:
        return [], {"cantidad": 0, "total_facturado": 0, "total_pagado_fecha": 0}

    id_col = _pick_existing_column(columns, "ID_DOC", "NO_DOC", "DOCUMENTO")
    fecha_col = _pick_existing_column(columns, "FECHA_CONT", "F_CONT", "FECHA_DOC", "FECHA")
    cliente_col = _pick_existing_column(columns, "NOM_SOCIO", "NOM_SN", "NOMBRE", "NOM_CLIENTE")
    id_sn_col = _pick_existing_column(columns, "ID_SN", "CLIENTE", "COD_CLIENTE")
    total_col = _pick_existing_column(columns, "TOTAL_DOC", "MONTO", "IMPORTE")
    usuario_col = _pick_existing_column(columns, "ID_USUARIO", "USUARIO_ID")
    terminal_col = _pick_existing_column(columns, "TERMINAL")
    estado_col = _pick_existing_column(columns, "EST_DOC", "ESTATUS", "ESTADO")
    cancelado_col = _pick_existing_column(columns, "CANCELADO")
    if not id_col or not fecha_col or not total_col:
        return [], {"cantidad": 0, "total_facturado": 0, "total_pagado_fecha": 0}

    selected_columns = _unique_columns(
        id_col,
        fecha_col,
        cliente_col,
        id_sn_col,
        total_col,
        usuario_col,
        terminal_col,
        estado_col,
        cancelado_col,
    )
    where_parts = [f"CONVERT(date, [{fecha_col}]) BETWEEN %s AND %s"]
    params = [fecha_desde, fecha_hasta]
    if usuario_filtro and usuario_col:
        where_parts.append(f"CAST([{usuario_col}] AS NVARCHAR(255)) = %s")
        params.append(usuario_filtro)
    if terminal_filtro and terminal_col:
        where_parts.append(f"LTRIM(RTRIM(CAST([{terminal_col}] AS NVARCHAR(255)))) = %s")
        params.append(terminal_filtro)
    if estado_col:
        where_parts.append(f"UPPER(LTRIM(RTRIM(ISNULL(CAST([{estado_col}] AS NVARCHAR(255)), '')))) <> 'CANCELADO'")
    if cancelado_col:
        where_parts.append(f"UPPER(LTRIM(RTRIM(ISNULL(CAST([{cancelado_col}] AS NVARCHAR(255)), 'N')))) NOT IN ('Y', 'S', 'SI', '1', 'TRUE')")

    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT {", ".join(f"[{column}]" for column in selected_columns)}
            FROM CAB_FACTURA
            WHERE {" AND ".join(where_parts)}
            ORDER BY [{fecha_col}], TRY_CAST([{id_col}] AS BIGINT), [{id_col}]
            """,
            params,
        )
        raw_columns = [col[0] for col in cursor.description]
        facturas = []
        for raw_row in cursor.fetchall():
            row = _normalize_result_row(raw_columns, raw_row)
            no_factura = _pick_row_text(row, id_col)
            total_factura = _pick_amount_value(row, total_col, default=0)
            fecha = _pick_row_value(row, fecha_col)
            facturas.append(
                {
                    "fecha": _fmt_date(fecha),
                    "fecha_key": _date_key(fecha),
                    "no_factura": no_factura,
                    "no_factura_sort": _doc_sort_key(no_factura),
                    "cliente_id": _pick_row_text(row, id_sn_col),
                    "cliente": _pick_row_text(row, cliente_col) or "Sin cliente",
                    "usuario_id": _pick_row_text(row, usuario_col),
                    "terminal": _pick_row_text(row, terminal_col) or "Sin terminal",
                    "total_facturado": total_factura,
                    "total_facturado_fmt": _money(total_factura),
                    "pago_fecha": 0,
                    "pago_fecha_fmt": _money(0),
                }
            )

    pagos = _load_pagos_facturas_en_fecha(facturas)
    for item in facturas:
        pago_fecha = pagos.get(item["no_factura"], Decimal("0"))
        item["pago_fecha"] = pago_fecha
        item["pago_fecha_fmt"] = _money(pago_fecha)

    totales = {
        "cantidad": len(facturas),
        "total_facturado": sum(_to_float(item["total_facturado"]) for item in facturas),
        "total_pagado_fecha": sum(_to_float(item["pago_fecha"]) for item in facturas),
    }
    totales.update(
        {
            "total_facturado_fmt": _money(totales["total_facturado"]),
            "total_pagado_fecha_fmt": _money(totales["total_pagado_fecha"]),
        }
    )
    return facturas, totales


def index(request):
    ctx = _base_context(request, page_title="Reportes", active_nav="reportes")
    if not ctx:
        return redirect("login")
    if not has_perm(ctx["auth_payload"]["usuario_id"], "reportes", "ver"):
        return render_denied(request, active_nav="reportes")
    can_ventas = has_perm(ctx["auth_payload"]["usuario_id"], "reportes", "ver_ventas")
    can_caja = has_perm(ctx["auth_payload"]["usuario_id"], "caja", "ver_cuadre_caja") or can_ventas
    ctx["submodules"] = {
        "ventas": can_ventas,
        "caja": can_caja,
        "clientes": has_perm(ctx["auth_payload"]["usuario_id"], "reportes", "ver_clientes"),
        "inventario": has_perm(ctx["auth_payload"]["usuario_id"], "reportes", "ver_inventario"),
    }
    reporte_activo = str(request.GET.get("reporte") or "facturacion").strip().lower()
    if reporte_activo not in {"facturacion", "caja"}:
        reporte_activo = "facturacion"
    if reporte_activo == "caja" and not can_caja:
        reporte_activo = "facturacion"
    today = timezone.localdate()
    fecha_desde = _parse_date_value(request.GET.get("fecha_desde")) or today
    fecha_hasta = _parse_date_value(request.GET.get("fecha_hasta")) or today
    if fecha_hasta < fecha_desde:
        fecha_desde, fecha_hasta = fecha_hasta, fecha_desde

    usuario_filtro = str(request.GET.get("usuario") or "").strip()
    terminal_filtro = str(request.GET.get("terminal") or "").strip()
    usuarios = _load_cuadre_caja_usuarios()
    terminales_facturacion = _load_facturacion_terminales()
    terminales_caja = _load_cuadre_caja_terminales()
    terminales = terminales_caja if reporte_activo == "caja" else terminales_facturacion
    usuarios_lookup = {item["id"]: item["label"] for item in usuarios if item.get("id")}

    facturas = []
    recibos = []
    totales = {"cantidad": 0, "total_facturado_fmt": _money(0), "total_pagado_fecha_fmt": _money(0)}
    caja_totales = {
        "cantidad": 0,
        "total_recibos_fmt": _money(0),
        "total_aplicado_fmt": _money(0),
        "total_descuento_fmt": _money(0),
    }
    if can_ventas and reporte_activo == "facturacion":
        try:
            facturas, totales = _load_facturacion_report(
                fecha_desde,
                fecha_hasta,
                usuario_filtro=usuario_filtro,
                terminal_filtro=terminal_filtro,
            )
            for row in facturas:
                row["usuario_label"] = usuarios_lookup.get(row.get("usuario_id")) or row.get("usuario_id") or "Sin usuario"
        except Exception:
            ctx["reportes_error"] = "No se pudo cargar el reporte de facturacion."
    if can_caja and reporte_activo == "caja":
        try:
            recibos, caja_totales = _load_caja_report(
                fecha_desde,
                fecha_hasta,
                usuario_filtro=usuario_filtro,
                terminal_filtro=terminal_filtro,
            )
            for row in recibos:
                row["usuario_label"] = usuarios_lookup.get(row.get("usuario_id")) or row.get("usuario_label") or "Sin usuario"
        except Exception:
            ctx["reportes_error"] = "No se pudo cargar el reporte de caja."

    ctx.update(
        {
            "reporte_activo": reporte_activo,
            "usuarios_reporte": usuarios,
            "terminales_reporte": terminales,
            "terminales_facturacion": terminales_facturacion,
            "terminales_caja": terminales_caja,
            "facturacion_rows": facturas,
            "facturacion_totales": totales,
            "caja_rows": recibos,
            "caja_totales": caja_totales,
            "facturacion_filters": {
                "fecha_desde": _fmt_date_input(fecha_desde),
                "fecha_hasta": _fmt_date_input(fecha_hasta),
                "fecha_desde_fmt": _fmt_date(fecha_desde),
                "fecha_hasta_fmt": _fmt_date(fecha_hasta),
                "usuario": usuario_filtro,
                "terminal": terminal_filtro,
            },
            "caja_filters": {
                "fecha_desde": _fmt_date_input(fecha_desde),
                "fecha_hasta": _fmt_date_input(fecha_hasta),
                "fecha_desde_fmt": _fmt_date(fecha_desde),
                "fecha_hasta_fmt": _fmt_date(fecha_hasta),
                "usuario": usuario_filtro,
                "terminal": terminal_filtro,
            },
        }
    )
    return render(request, "reportes/index.html", ctx)
