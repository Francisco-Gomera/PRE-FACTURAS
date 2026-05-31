import json
from datetime import datetime

from django.db import connection, transaction

from .realtime import (
    broadcast_cxc_document_status,
    broadcast_factura_document_status,
    broadcast_financiamiento_document_status,
    broadcast_inventario_solicitudes_refresh,
    broadcast_notification_refresh,
    broadcast_prefactura_document_status,
    broadcast_prefacturas_refresh,
)


REALTIME_DB_QUEUE_TABLE = "WS_EVENT_QUEUE"


def _table_exists(table_name):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 1
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME = %s
            """,
            [str(table_name or "").strip()],
        )
        return bool(cursor.fetchone())


def realtime_db_queue_exists():
    try:
        return _table_exists(REALTIME_DB_QUEUE_TABLE)
    except Exception:
        return False


def claim_realtime_db_events(batch_size=50, worker_name="django"):
    safe_batch_size = max(1, min(int(batch_size or 50), 500))
    worker_label = str(worker_name or "django").strip() or "django"
    if not realtime_db_queue_exists():
        return []

    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                ;WITH next_events AS (
                    SELECT TOP ({safe_batch_size}) ID_EVENTO
                    FROM {REALTIME_DB_QUEUE_TABLE} WITH (ROWLOCK, READPAST, UPDLOCK)
                    WHERE ESTADO = 'PENDIENTE'
                    ORDER BY FECHA_EVENTO, ID_EVENTO
                )
                UPDATE q
                SET
                    ESTADO = 'PROCESANDO',
                    TOMADO_EN = GETDATE(),
                    WORKER = %s
                OUTPUT
                    inserted.ID_EVENTO,
                    inserted.CANAL,
                    inserted.TIPO_EVENTO,
                    inserted.DOCUMENT_ID,
                    inserted.ESTADO_DOC,
                    inserted.RAZON,
                    inserted.EVENT_ID,
                    inserted.PAYLOAD_JSON,
                    inserted.FECHA_EVENTO
                FROM {REALTIME_DB_QUEUE_TABLE} q
                INNER JOIN next_events n
                    ON n.ID_EVENTO = q.ID_EVENTO
                """,
                [worker_label],
            )
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]

    results = []
    for raw_row in rows:
        item = dict(zip(columns, raw_row))
        payload = {}
        payload_raw = item.get("PAYLOAD_JSON")
        if payload_raw:
            try:
                payload = json.loads(str(payload_raw))
            except Exception:
                payload = {}
        results.append(
            {
                "id_evento": int(item.get("ID_EVENTO") or 0),
                "canal": str(item.get("CANAL") or "").strip().lower(),
                "tipo_evento": str(item.get("TIPO_EVENTO") or "").strip().lower(),
                "document_id": str(item.get("DOCUMENT_ID") or "").strip(),
                "estado_doc": str(item.get("ESTADO_DOC") or "").strip(),
                "razon": str(item.get("RAZON") or "").strip(),
                "event_id": str(item.get("EVENT_ID") or "").strip(),
                "payload": payload,
                "fecha_evento": item.get("FECHA_EVENTO"),
            }
        )
    return results


def complete_realtime_db_event(event_id):
    if int(event_id or 0) <= 0 or not realtime_db_queue_exists():
        return
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE {REALTIME_DB_QUEUE_TABLE}
            SET
                ESTADO = 'COMPLETADO',
                PROCESADO_EN = GETDATE(),
                ERROR_MSG = NULL
            WHERE ID_EVENTO = %s
            """,
            [int(event_id)],
        )


def fail_realtime_db_event(event_id, error_message):
    if int(event_id or 0) <= 0 or not realtime_db_queue_exists():
        return
    error_text = str(error_message or "").strip()
    if len(error_text) > 1000:
        error_text = error_text[:1000]
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE {REALTIME_DB_QUEUE_TABLE}
            SET
                ESTADO = 'ERROR',
                ERROR_MSG = %s
            WHERE ID_EVENTO = %s
            """,
            [error_text, int(event_id)],
        )


def _payload_text(payload, *keys):
    for key in keys:
        value = payload.get(key)
        text = str(value or "").strip()
        if text:
            return text
    return ""


def dispatch_realtime_db_event(event):
    event = event or {}
    payload = event.get("payload") or {}
    canal = str(event.get("canal") or "").strip().lower()
    reason = str(event.get("razon") or "").strip() or str(event.get("tipo_evento") or "").strip() or "updated"
    event_id = str(event.get("event_id") or "").strip()
    document_id = str(event.get("document_id") or "").strip() or _payload_text(payload, "document_id", "id_doc", "id_solicitud", "id_evento")
    estado_doc = str(event.get("estado_doc") or "").strip() or _payload_text(payload, "estado", "est_doc", "estado_doc")

    if canal == "prefacturas":
        if document_id:
            broadcast_prefactura_document_status(
                document_id=document_id,
                estado=estado_doc,
                reason=reason,
                event_id=event_id,
            )
        broadcast_prefacturas_refresh(reason=reason, event_id=event_id)
        return True

    if canal == "facturas":
        if not document_id:
            return False
        broadcast_factura_document_status(
            document_id=document_id,
            estado=estado_doc,
            reason=reason,
            event_id=event_id,
        )
        return True

    if canal == "cxc":
        if not document_id:
            return False
        broadcast_cxc_document_status(
            document_id=document_id,
            no_recibo=_payload_text(payload, "no_recibo", "no_doc", "id_recibo"),
            estado=estado_doc,
            reason=reason,
            event_id=event_id,
        )
        return True

    if canal == "financiamiento":
        if not document_id:
            return False
        broadcast_financiamiento_document_status(
            document_id=document_id,
            factura_no=_payload_text(payload, "factura_no", "no_doc", "document_id"),
            estado=estado_doc,
            reason=reason,
            event_id=event_id,
        )
        return True

    if canal == "inventario_solicitudes":
        broadcast_inventario_solicitudes_refresh(reason=reason)
        broadcast_notification_refresh(reason=reason)
        return True

    if canal == "notifications":
        broadcast_notification_refresh(reason=reason)
        return True

    return False


def format_realtime_db_event_log(event):
    event = event or {}
    timestamp = event.get("fecha_evento")
    if isinstance(timestamp, datetime):
        stamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    else:
        stamp = str(timestamp or "").strip()
    return " | ".join(
        [
            f"id={event.get('id_evento')}",
            f"canal={event.get('canal')}",
            f"tipo={event.get('tipo_evento')}",
            f"doc={event.get('document_id') or '-'}",
            f"estado={event.get('estado_doc') or '-'}",
            f"fecha={stamp or '-'}",
        ]
    )
