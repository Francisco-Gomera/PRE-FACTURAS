from datetime import datetime
from decimal import Decimal, InvalidOperation
from functools import lru_cache

from django.db import connection
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET

from ajustes.permissions import has_perm
from core.views import _base_context, render_denied
from prefacturas_app.views import _require_perm_json


def _fmt_date_input(value):
    if not value:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    text = str(value).strip()
    if not text:
        return ""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            return datetime.strptime(text[:26], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return text[:10] if len(text) >= 10 else ""


def _fmt_date_flexible(value):
    if not value:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%d/%m/%Y")
    text = str(value).strip()
    if not text:
        return ""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            return datetime.strptime(text[:26], fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return text


def _to_decimal(value, default=Decimal("0")):
    try:
        if value is None:
            return default
        text = str(value).strip().replace(",", "")
        if not text:
            return default
        return Decimal(text)
    except (InvalidOperation, TypeError, ValueError):
        return default


def _format_money(value):
    return f"{_to_decimal(value):,.2f}"


def _stringify_doc(value):
    if value is None:
        return ""
    text = str(value).strip()
    if text.endswith(".0"):
        return text[:-2]
    return text


@lru_cache(maxsize=64)
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


def _pick_existing_column(columns, *candidates):
    available = {str(column).upper(): str(column).upper() for column in (columns or [])}
    for candidate in candidates:
        if not candidate:
            continue
        found = available.get(str(candidate).upper())
        if found:
            return found
    return None


def _build_doc_lookup_where(columns, lookup_value):
    lookup_text = str(lookup_value or "").strip()
    normalized_columns = []
    seen = set()
    for column in columns or []:
        if not column:
            continue
        column_name = str(column).upper()
        if column_name in seen:
            continue
        seen.add(column_name)
        normalized_columns.append(column_name)

    if not lookup_text or not normalized_columns:
        return "1 = 0", []

    lookup_numeric = _to_decimal(lookup_text, default=None)
    where_parts = []
    params = []
    for column_name in normalized_columns:
        where_parts.append(f"CAST([{column_name}] AS NVARCHAR(255)) = %s")
        params.append(lookup_text)
        if lookup_numeric is not None:
            where_parts.append(f"TRY_CAST([{column_name}] AS DECIMAL(38, 10)) = TRY_CAST(%s AS DECIMAL(38, 10))")
            params.append(lookup_text)
    return "(" + " OR ".join(where_parts) + ")", params


def _normalize_result_row(columns, raw_row):
    return {str(columns[idx]).upper(): raw_row[idx] for idx in range(len(columns))}


def _pick_row_value(row, *candidates, default=None, allow_blank=False):
    for candidate in candidates:
        if not candidate:
            continue
        key = str(candidate).upper()
        if key not in row:
            continue
        value = row.get(key)
        if value is None:
            continue
        if isinstance(value, str) and not allow_blank and not value.strip():
            continue
        return value
    return default


def _unique_preserve(*values):
    seen = set()
    result = []
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        upper = text.upper()
        if upper in seen:
            continue
        seen.add(upper)
        result.append(text)
    return result


def _build_multi_lookup_where(columns, lookup_values):
    parts = []
    params = []
    for value in _unique_preserve(*(lookup_values or [])):
        where_sql, where_params = _build_doc_lookup_where(columns, value)
        if where_params:
            parts.append(where_sql)
            params.extend(where_params)
    if not parts:
        return "1 = 0", []
    return "(" + " OR ".join(parts) + ")", params


def _load_entrada_articulos_search_rows(*, query="", filtro="documento"):
    cab_columns = _load_table_columns("CAB_ENT_INV")
    if not cab_columns:
        return []

    doc_col = _pick_existing_column(cab_columns, "NO_DOC", "ID_DOC", "NO", "NO_ENTRADA", "ID_ENTRADA", "DOCUMENTO")
    no_col = _pick_existing_column(cab_columns, "NO", "ID_ENTRADA", "NO_ENTRADA", doc_col)
    codigo_col = _pick_existing_column(cab_columns, "CODIGO", "COD", "COD_DOC", "COD_TIPO", "TIPO_DOC")
    descripcion_col = _pick_existing_column(cab_columns, "DESCRIPCION", "DESCRIP", "DESCRIP_DOC", "DESCRIPCION_DOC")
    asunto_col = _pick_existing_column(cab_columns, "ASUNTO", "CONCEPTO", "REFERENCIA")
    proveedor_codigo_col = _pick_existing_column(cab_columns, "ID_PROV", "COD_PROV", "ID_PROVEEDOR", "PROVEEDOR", "ID_SN")
    proveedor_nombre_col = _pick_existing_column(cab_columns, "NOM_PROV", "NOMBRE_PROV", "NOM_SUPLIDOR", "NOM_SN", "NOM_SOCIO", "NOMBRE")
    estado_col = _pick_existing_column(cab_columns, "EST_DOC", "ESTATUS", "ESTADO")
    fecha_col = _pick_existing_column(cab_columns, "FECHA_DOC", "FECHA_CONT", "FECHA", "FECHA_APLIC")
    total_col = _pick_existing_column(cab_columns, "TOTAL_DOC", "TOTAL", "MONTO", "IMPORTE", "VALOR")

    select_columns = [col for col in [doc_col, no_col, codigo_col, descripcion_col, asunto_col, proveedor_codigo_col, proveedor_nombre_col, estado_col, fecha_col, total_col] if col]
    select_columns = list(dict.fromkeys(select_columns))
    if not select_columns:
        return []

    sql = "SELECT TOP 80 " + ", ".join(f"[{column}]" for column in select_columns) + " FROM CAB_ENT_INV"
    params = []
    query_text = str(query or "").strip()
    if query_text:
        filtro = str(filtro or "documento").strip().lower()
        if filtro == "documento":
            search_columns = [doc_col, no_col]
        elif filtro == "codigo":
            search_columns = [codigo_col, proveedor_codigo_col]
        elif filtro == "descripcion":
            search_columns = [descripcion_col, asunto_col]
        elif filtro == "proveedor":
            search_columns = [proveedor_codigo_col, proveedor_nombre_col]
        else:
            search_columns = [doc_col, no_col, codigo_col, descripcion_col, asunto_col, proveedor_codigo_col, proveedor_nombre_col]
        search_columns = [column for column in search_columns if column]
        if search_columns:
            sql += " WHERE (" + " OR ".join(f"CAST([{column}] AS NVARCHAR(255)) LIKE %s" for column in search_columns) + ")"
            params.extend([f"%{query_text}%"] * len(search_columns))

    if doc_col:
        sql += f" ORDER BY TRY_CAST([{doc_col}] AS BIGINT) DESC, CAST([{doc_col}] AS NVARCHAR(255)) DESC"
    elif no_col:
        sql += f" ORDER BY TRY_CAST([{no_col}] AS BIGINT) DESC, CAST([{no_col}] AS NVARCHAR(255)) DESC"

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

    results = []
    for raw_row in rows:
        row = _normalize_result_row(columns, raw_row)
        no_doc = _stringify_doc(_pick_row_value(row, doc_col, no_col, default=""))
        codigo = str(_pick_row_value(row, codigo_col, default="", allow_blank=True) or "").strip()
        descripcion = str(_pick_row_value(row, descripcion_col, asunto_col, default="", allow_blank=True) or "").strip()
        proveedor_codigo = str(_pick_row_value(row, proveedor_codigo_col, default="", allow_blank=True) or "").strip()
        proveedor_nombre = str(_pick_row_value(row, proveedor_nombre_col, default="", allow_blank=True) or "").strip()
        estado = str(_pick_row_value(row, estado_col, default="", allow_blank=True) or "").strip()
        total_doc = _to_decimal(_pick_row_value(row, total_col, default=Decimal("0")))
        results.append(
            {
                "no_doc": no_doc,
                "codigo": codigo,
                "descripcion": descripcion,
                "proveedor_codigo": proveedor_codigo,
                "proveedor_nombre": proveedor_nombre,
                "fecha_doc": _fmt_date_flexible(_pick_row_value(row, fecha_col, default="")),
                "estado": estado,
                "total_doc": float(total_doc),
                "total_doc_fmt": _format_money(total_doc),
            }
        )
    return results


def _load_entrada_articulos_record(lookup_value):
    lookup_text = str(lookup_value or "").strip()
    if not lookup_text:
        return None

    cab_columns = _load_table_columns("CAB_ENT_INV")
    det_columns = _load_table_columns("DET_ENT_INV")
    if not cab_columns:
        return None

    cab_doc_col = _pick_existing_column(cab_columns, "NO_DOC", "ID_DOC", "NO", "NO_ENTRADA", "ID_ENTRADA", "DOCUMENTO")
    cab_no_col = _pick_existing_column(cab_columns, "NO", "ID_ENTRADA", "NO_ENTRADA", cab_doc_col)
    if not cab_doc_col and not cab_no_col:
        return None

    where_sql, where_params = _build_doc_lookup_where([cab_doc_col, cab_no_col], lookup_text)
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT TOP 1 * FROM CAB_ENT_INV WHERE {where_sql}", where_params)
        raw_header = cursor.fetchone()
        if not raw_header:
            return None
        header_columns = [col[0] for col in cursor.description]
        header_row = _normalize_result_row(header_columns, raw_header)

    codigo_col = _pick_existing_column(cab_columns, "CODIGO", "COD", "COD_DOC", "COD_TIPO", "TIPO_DOC")
    descripcion_col = _pick_existing_column(cab_columns, "DESCRIPCION", "DESCRIP", "DESCRIP_DOC", "DESCRIPCION_DOC")
    asunto_col = _pick_existing_column(cab_columns, "ASUNTO", "CONCEPTO", "REFERENCIA")
    departamento_col = _pick_existing_column(cab_columns, "DEPARTAMENTO", "DEPTO", "DPTO")
    proveedor_codigo_col = _pick_existing_column(cab_columns, "ID_PROV", "COD_PROV", "ID_PROVEEDOR", "PROVEEDOR", "ID_SN")
    proveedor_nombre_col = _pick_existing_column(cab_columns, "NOM_PROV", "NOMBRE_PROV", "NOM_SUPLIDOR", "NOM_SN", "NOM_SOCIO", "NOMBRE")
    estado_col = _pick_existing_column(cab_columns, "EST_DOC", "ESTATUS", "ESTADO")
    fecha_cont_col = _pick_existing_column(cab_columns, "FECHA_CONT", "FECHA", "FECHA_APLIC", "F_CONT")
    fecha_venc_col = _pick_existing_column(cab_columns, "FECHA_VENC", "FECHA_VENCE", "VENCIMIENTO")
    fecha_doc_col = _pick_existing_column(cab_columns, "FECHA_DOC", "FECHA", "FECHA_CONT")
    comentario_col = _pick_existing_column(cab_columns, "COMENTARIO", "OBSERVACION", "NOTA")
    total_col = _pick_existing_column(cab_columns, "TOTAL_DOC", "TOTAL", "MONTO", "IMPORTE", "VALOR")

    document_values = _unique_preserve(
        _pick_row_value(header_row, cab_doc_col, default=""),
        _pick_row_value(header_row, cab_no_col, default=""),
        lookup_text,
    )

    detalles = []
    if det_columns:
        det_doc_col = _pick_existing_column(det_columns, "NO_DOC", "ID_DOC", "NO", "NO_ENTRADA", "ID_ENTRADA", "DOCUMENTO")
        det_no_col = _pick_existing_column(det_columns, "NO", "ID_ENTRADA", "NO_ENTRADA")
        det_line_col = _pick_existing_column(det_columns, "NO_LINEA", "LINEA", "NO_ITEM", "ORDEN", "ID_DETALLE")
        det_desc_col = _pick_existing_column(det_columns, "DESCRIP_ART", "DESCRIPCION", "DESCRIP", "DESCRIP_ART_SERV")
        det_art_col = _pick_existing_column(det_columns, "ID_ARTICULO", "ARTICULO", "COD_ART", "CODIGO")
        det_cant_emp_col = _pick_existing_column(det_columns, "CANT_EMP", "CANT_EMPAQUE", "CANT_UND", "CANT_UNIDADES")
        det_cantidad_col = _pick_existing_column(det_columns, "CANTIDAD", "CANT")
        det_uom_col = _pick_existing_column(det_columns, "MEDIDA", "UOM", "U_MED", "UNIDAD")
        det_alm_col = _pick_existing_column(det_columns, "ALM", "ALMACEN", "ID_ALM")
        det_pedido_col = _pick_existing_column(det_columns, "PEDIDO_CTE", "PEDIDO", "NO_PEDIDO")
        det_proyecto_col = _pick_existing_column(det_columns, "PROYECTO", "ID_PROYECTO")
        det_ceco_col = _pick_existing_column(det_columns, "CECO", "CENTRO_COSTO")
        det_costo_col = _pick_existing_column(det_columns, "COSTO_UNIT", "COSTO", "COSTO_UNITARIO", "PRECIO")
        det_valor_col = _pick_existing_column(det_columns, "VALOR", "TOTAL_LINEA", "TOTAL", "IMPORTE")
        det_cta_col = _pick_existing_column(det_columns, "CTA_MAYOR", "CUENTA_MAYOR", "CTA_LM", "CUENTA")

        if det_doc_col or det_no_col:
            where_sql, where_params = _build_multi_lookup_where([det_doc_col, det_no_col], document_values)
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM DET_ENT_INV WHERE {where_sql}", where_params)
                detail_columns = [col[0] for col in cursor.description]
                detail_rows = cursor.fetchall()
            parsed_rows = []
            for raw_row in detail_rows:
                row = _normalize_result_row(detail_columns, raw_row)
                parsed_rows.append(
                    {
                        "linea": _stringify_doc(_pick_row_value(row, det_line_col, default="")),
                        "descripcion": str(_pick_row_value(row, det_desc_col, default="", allow_blank=True) or "").strip(),
                        "articulo": str(_pick_row_value(row, det_art_col, default="", allow_blank=True) or "").strip(),
                        "cant_emp": str(_pick_row_value(row, det_cant_emp_col, default="", allow_blank=True) or "").strip(),
                        "cantidad": _format_money(_pick_row_value(row, det_cantidad_col, default=Decimal("0"))),
                        "uom": str(_pick_row_value(row, det_uom_col, default="", allow_blank=True) or "").strip(),
                        "alm": str(_pick_row_value(row, det_alm_col, default="", allow_blank=True) or "").strip(),
                        "pedido_cte": str(_pick_row_value(row, det_pedido_col, default="", allow_blank=True) or "").strip(),
                        "proyecto": str(_pick_row_value(row, det_proyecto_col, default="", allow_blank=True) or "").strip(),
                        "ceco": str(_pick_row_value(row, det_ceco_col, default="", allow_blank=True) or "").strip(),
                        "costo_unit": _format_money(_pick_row_value(row, det_costo_col, default=Decimal("0"))),
                        "valor": _format_money(_pick_row_value(row, det_valor_col, default=Decimal("0"))),
                        "cuenta_mayor": str(_pick_row_value(row, det_cta_col, default="", allow_blank=True) or "").strip(),
                    }
                )
            detalles = sorted(parsed_rows, key=lambda item: (Decimal(item["linea"]) if str(item["linea"]).replace(".", "", 1).isdigit() else Decimal("999999"), item["linea"]))

    total_doc = _to_decimal(_pick_row_value(header_row, total_col, default=Decimal("0")))
    if total_doc == Decimal("0") and detalles:
        total_doc = sum((_to_decimal(row.get("valor")) for row in detalles), Decimal("0"))

    return {
        "entry": {
            "lookup": lookup_text,
            "no": _stringify_doc(_pick_row_value(header_row, cab_no_col, cab_doc_col, default="")),
            "no_doc": _stringify_doc(_pick_row_value(header_row, cab_doc_col, cab_no_col, default="")),
            "codigo": str(_pick_row_value(header_row, codigo_col, default="", allow_blank=True) or "").strip(),
            "descripcion": str(_pick_row_value(header_row, descripcion_col, default="", allow_blank=True) or "").strip(),
            "asunto": str(_pick_row_value(header_row, asunto_col, default="", allow_blank=True) or "").strip(),
            "departamento": str(_pick_row_value(header_row, departamento_col, default="", allow_blank=True) or "").strip(),
            "proveedor_codigo": str(_pick_row_value(header_row, proveedor_codigo_col, default="", allow_blank=True) or "").strip(),
            "proveedor_nombre": str(_pick_row_value(header_row, proveedor_nombre_col, default="", allow_blank=True) or "").strip(),
            "estado": str(_pick_row_value(header_row, estado_col, default="", allow_blank=True) or "").strip(),
            "fecha_cont": _fmt_date_input(_pick_row_value(header_row, fecha_cont_col, default="")),
            "fecha_venc": _fmt_date_input(_pick_row_value(header_row, fecha_venc_col, default="")),
            "fecha_doc": _fmt_date_input(_pick_row_value(header_row, fecha_doc_col, default="")),
            "comentario": str(_pick_row_value(header_row, comentario_col, default="", allow_blank=True) or "").strip(),
            "total_doc": _format_money(total_doc),
        },
        "detalles": detalles,
    }


def index(request):
    ctx = _base_context(request, page_title="Inventario", active_nav="inventario")
    if not ctx:
        return redirect("login")
    if not has_perm(ctx["auth_payload"]["usuario_id"], "inventario", "ver"):
        return render_denied(request, active_nav="inventario")
    ctx["submodules"] = {
        "articulos": has_perm(ctx["auth_payload"]["usuario_id"], "inventario", "ver_articulos"),
        "entrada_articulos": has_perm(ctx["auth_payload"]["usuario_id"], "inventario", "ver_entrada_articulos"),
        "salida_articulos": has_perm(ctx["auth_payload"]["usuario_id"], "inventario", "ver_salida_articulos"),
        "grupos": has_perm(ctx["auth_payload"]["usuario_id"], "inventario", "ver_grupos"),
        "stock": has_perm(ctx["auth_payload"]["usuario_id"], "inventario", "ver_stock"),
    }
    return render(request, "inventario/index.html", ctx)


def articulos_view(request):
    ctx = _base_context(request, page_title="Articulos", active_nav="inventario")
    if not ctx:
        return redirect("login")
    if not has_perm(ctx["auth_payload"]["usuario_id"], "inventario", "ver_articulos"):
        return render_denied(request, active_nav="inventario")
    return render(request, "inventario/articulos.html", ctx)


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


def entrada_articulos_view(request):
    ctx = _base_context(request, page_title="Entrada de articulos", active_nav="inventario")
    if not ctx:
        return redirect("login")
    if not has_perm(ctx["auth_payload"]["usuario_id"], "inventario", "ver_entrada_articulos"):
        return render_denied(request, active_nav="inventario")
    usuario_id = ctx["auth_payload"]["usuario_id"]
    ctx["server_today_iso"] = timezone.localdate().strftime("%Y-%m-%d")
    ctx["entrada_shortcuts"] = {
        "articulos": has_perm(usuario_id, "inventario", "ver_articulos"),
        "salida_articulos": has_perm(usuario_id, "inventario", "ver_salida_articulos"),
        "facturacion": has_perm(usuario_id, "factura", "ver_documentos"),
        "cuentas_por_cobrar": has_perm(usuario_id, "caja", "ver_cuentas_por_cobrar"),
    }
    return render(request, "inventario/entrada_articulos.html", ctx)


@require_GET
def entrada_articulos_buscar_view(request):
    auth_payload = _require_perm_json(request, "inventario", "ver_entrada_articulos")
    if isinstance(auth_payload, JsonResponse):
        return auth_payload
    query = (request.GET.get("q") or "").strip()
    filtro = (request.GET.get("filtro") or "documento").strip().lower()
    try:
        return JsonResponse({"results": _load_entrada_articulos_search_rows(query=query, filtro=filtro)})
    except Exception:
        return JsonResponse({"results": []})


@require_GET
def entrada_articulos_detalle_view(request):
    auth_payload = _require_perm_json(request, "inventario", "ver_entrada_articulos")
    if isinstance(auth_payload, JsonResponse):
        return auth_payload
    no_doc = (request.GET.get("no_doc") or "").strip()
    if not no_doc:
        return JsonResponse({"detail": "Parametro no_doc requerido"}, status=400)
    try:
        record = _load_entrada_articulos_record(no_doc)
    except Exception:
        record = None
    if not record:
        return JsonResponse({"detail": "Entrada de articulos no encontrada."}, status=404)
    return JsonResponse(record)


def salida_articulos_view(request):
    ctx = _base_context(request, page_title="Salida de articulos", active_nav="inventario")
    if not ctx:
        return redirect("login")
    if not has_perm(ctx["auth_payload"]["usuario_id"], "inventario", "ver_salida_articulos"):
        return render_denied(request, active_nav="inventario")
    return render(request, "inventario/salida_articulos.html", ctx)
