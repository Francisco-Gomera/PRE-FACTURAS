import json
import os
import uuid

from django.conf import settings
from django.db import connection, transaction
from django.db.models import Q
from django.db.utils import DatabaseError
from django.http import JsonResponse
from django.urls import reverse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from ajustes.permissions import has_perm
from caja.views import _load_cxc_recibos_busqueda, _load_financiamiento_search_rows
from core.chat_presence import is_user_online
from core.realtime import broadcast_chat_message, broadcast_chat_room_update
from core.views import _base_context, render_denied
from prefacturas_app.models_existing import MaestroSn
from prefacturas_app.views import _require_perm_json

from .models import (
    ChatMensaje,
    ChatMensajeLectura,
    ChatMensajeOculto,
    ChatSala,
    ChatSalaMiembro,
    ChatSalaOculta,
)


VOICE_NOTE_PREFIX = "__VOICE_NOTE__:"
ATTACHMENTS_PREFIX = "__ATTACHMENTS__:"
SHARED_RECORD_PREFIX = "__SHARED_RECORD__:"
MAX_ATTACHMENTS_TOTAL_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a", ".aac", ".webm"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".mkv", ".mpeg"}
ALLOWED_DOCUMENT_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".txt", ".ppt", ".pptx", ".zip", ".rar"
}


def _to_int(value, default=0):
    try:
        return int(str(value or "").strip())
    except Exception:
        return default


def _chat_perm(id_usuario, permiso):
    return has_perm(id_usuario, "chat_interno", permiso)


def _chat_storage_ready():
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_NAME IN ('CHAT_SALA', 'CHAT_SALA_MIEMBRO', 'CHAT_MENSAJE', 'CHAT_MENSAJE_LECTURA')
                """
            )
            row = cursor.fetchone()
        return int((row or [0])[0] or 0) >= 4
    except Exception:
        return False


def _chat_hide_storage_ready():
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_NAME IN ('CHAT_MENSAJE_OCULTO', 'CHAT_SALA_OCULTA')
                """
            )
            row = cursor.fetchone()
        return int((row or [0])[0] or 0) >= 2
    except Exception:
        return False


def _chat_storage_error_response():
    return JsonResponse(
        {
            "detail": "Chat Interno aun no esta inicializado en la base de datos. Ejecuta migrate chat_interno y seed_permisos.",
        },
        status=503,
    )


def _chat_hide_storage_error_response():
    return JsonResponse(
        {
            "detail": "La funcion de ocultar mensajes/chats aun no esta inicializada. Ejecuta migrate chat_interno.",
        },
        status=503,
    )


def _build_voice_note_content(*, file_url, duration_seconds=0, mime_type="", original_name=""):
    payload = {
        "file_url": str(file_url or "").strip(),
        "duration_seconds": max(0, _to_int(duration_seconds, 0)),
        "mime_type": str(mime_type or "").strip(),
        "original_name": str(original_name or "").strip(),
    }
    return VOICE_NOTE_PREFIX + json.dumps(payload, ensure_ascii=True)


def _media_url_exists(file_url):
    url = str(file_url or "").strip()
    if not url:
        return False
    media_prefix = str(settings.MEDIA_URL or "").strip()
    if not media_prefix or not url.startswith(media_prefix):
        return True
    relative_path = url[len(media_prefix):].lstrip("/").replace("/", os.sep)
    if not relative_path:
        return False
    candidates = []
    try:
        candidates.append(settings.MEDIA_ROOT / relative_path)
    except Exception:
        pass
    try:
        candidates.append(settings.MEDIA_ROOT.parent.parent / "media" / relative_path)
    except Exception:
        pass
    for candidate in candidates:
        try:
            if candidate.exists():
                return True
        except Exception:
            continue
    return False


def _parse_voice_note_content(value):
    text = str(value or "")
    if not text.startswith(VOICE_NOTE_PREFIX):
        return None
    try:
        payload = json.loads(text[len(VOICE_NOTE_PREFIX):] or "{}")
    except Exception:
        return None
    file_url = str((payload or {}).get("file_url") or "").strip()
    if not file_url:
        return None
    return {
        "file_url": file_url,
        "duration_seconds": max(0, _to_int((payload or {}).get("duration_seconds"), 0)),
        "mime_type": str((payload or {}).get("mime_type") or "").strip(),
        "original_name": str((payload or {}).get("original_name") or "").strip(),
        "file_exists": _media_url_exists(file_url),
    }


def _attachment_category_for_upload(upload):
    content_type = str(getattr(upload, "content_type", "") or "").strip().lower()
    suffix = os.path.splitext(str(getattr(upload, "name", "") or "").strip())[1].lower()
    if content_type.startswith("image/") or suffix in ALLOWED_IMAGE_EXTENSIONS:
        return "image"
    if content_type.startswith("audio/") or suffix in ALLOWED_AUDIO_EXTENSIONS:
        return "audio"
    if content_type.startswith("video/") or suffix in ALLOWED_VIDEO_EXTENSIONS:
        return "video"
    if suffix in ALLOWED_DOCUMENT_EXTENSIONS:
        return "document"
    return ""


def _build_attachments_content(*, category, items):
    payload = {
        "category": str(category or "").strip().lower(),
        "items": items or [],
    }
    return ATTACHMENTS_PREFIX + json.dumps(payload, ensure_ascii=True)


def _parse_attachments_content(value):
    text = str(value or "")
    if not text.startswith(ATTACHMENTS_PREFIX):
        return None
    try:
        payload = json.loads(text[len(ATTACHMENTS_PREFIX):] or "{}")
    except Exception:
        return None
    category = str((payload or {}).get("category") or "").strip().lower()
    raw_items = (payload or {}).get("items") or []
    items = []
    for item in raw_items:
        file_url = str((item or {}).get("file_url") or "").strip()
        if not file_url:
            continue
        items.append(
            {
                "file_url": file_url,
                "mime_type": str((item or {}).get("mime_type") or "").strip(),
                "original_name": str((item or {}).get("original_name") or "").strip(),
                "size_bytes": max(0, _to_int((item or {}).get("size_bytes"), 0)),
                "file_exists": _media_url_exists(file_url),
            }
        )
    if not items or category not in {"image", "audio", "video", "document"}:
        return None
    return {"category": category, "items": items}


def _build_shared_record_content(payload):
    return SHARED_RECORD_PREFIX + json.dumps(payload or {}, ensure_ascii=True)


def _parse_shared_record_content(value):
    text = str(value or "")
    if not text.startswith(SHARED_RECORD_PREFIX):
        return None
    try:
        payload = json.loads(text[len(SHARED_RECORD_PREFIX):] or "{}")
    except Exception:
        return None
    record_type = str((payload or {}).get("record_type") or "").strip().lower()
    title = str((payload or {}).get("title") or "").strip()
    target_url = str((payload or {}).get("target_url") or "").strip()
    if record_type not in {"cliente", "cuenta_por_cobrar", "factura", "financiamiento"}:
        return None
    if not title or not target_url:
        return None
    return {
        "record_type": record_type,
        "record_id": str((payload or {}).get("record_id") or "").strip(),
        "module_label": str((payload or {}).get("module_label") or "").strip(),
        "title": title,
        "subtitle": str((payload or {}).get("subtitle") or "").strip(),
        "description": str((payload or {}).get("description") or "").strip(),
        "target_url": target_url,
        "cta_label": str((payload or {}).get("cta_label") or "").strip() or "Abrir registro",
    }


def _attachments_preview_text(category, count):
    qty = max(1, _to_int(count, 1))
    if category == "image":
        return "Imagen" if qty == 1 else f"{qty} imagenes"
    if category == "audio":
        return "Audio" if qty == 1 else f"{qty} audios"
    if category == "video":
        return "Video" if qty == 1 else f"{qty} videos"
    return "Documento" if qty == 1 else f"{qty} documentos"


def _message_preview_text(msg):
    voice_note = _parse_voice_note_content(getattr(msg, "contenido", ""))
    if voice_note:
        return "Nota de voz"
    attachments = _parse_attachments_content(getattr(msg, "contenido", ""))
    if attachments:
        return _attachments_preview_text(attachments.get("category"), len(attachments.get("items") or []))
    shared_record = _parse_shared_record_content(getattr(msg, "contenido", ""))
    if shared_record:
        module_label = str(shared_record.get("module_label") or "Registro").strip()
        title = str(shared_record.get("title") or "").strip()
        return f"{module_label}: {title}" if title else module_label
    return str(getattr(msg, "contenido", "") or "").strip()


def _serialize_mensaje(msg):
    voice_note = _parse_voice_note_content(msg.contenido)
    attachments = _parse_attachments_content(msg.contenido)
    shared_record = _parse_shared_record_content(msg.contenido)
    if voice_note:
        message_type = "voice_note"
    elif attachments:
        message_type = f"{attachments.get('category')}_attachments"
    elif shared_record:
        message_type = "shared_record"
    else:
        message_type = "text"
    return {
        "id_mensaje": int(msg.id_mensaje),
        "id_sala": int(msg.sala_id),
        "id_usuario": int(msg.id_usuario or 0),
        "usuario_nombre": str(msg.usuario_nombre or "").strip(),
        "contenido": "" if (voice_note or attachments or shared_record) else str(msg.contenido or ""),
        "creado_en": timezone.localtime(msg.creado_en).strftime("%Y-%m-%d %H:%M:%S") if msg.creado_en else "",
        "event_id": str(msg.event_id or "").strip(),
        "read_by_other": False,
        "delivered_to_other": False,
        "message_type": message_type,
        "voice_note": voice_note,
        "attachments": attachments,
        "shared_record": shared_record,
    }


def _get_direct_partner_label(sala, current_user_id):
    member = (
        ChatSalaMiembro.objects.filter(sala=sala, activo=True)
        .exclude(id_usuario=current_user_id)
        .order_by("id_miembro")
        .first()
    )
    if not member:
        return "Chat directo"
    return str(member.usuario_nombre or member.id_usuario).strip() or "Chat directo"


def _get_direct_partner_member(sala, current_user_id):
    return (
        ChatSalaMiembro.objects.filter(sala=sala, activo=True)
        .exclude(id_usuario=current_user_id)
        .order_by("id_miembro")
        .first()
    )


def _serialize_sala(sala, current_user_id, last_msg=None):
    if last_msg is None:
        last_msg = sala.mensajes.order_by("-id_mensaje").first()
    tipo = str(sala.tipo or "").strip().upper()
    nombre = str(sala.nombre or "").strip()
    direct_partner = None
    if tipo == "DIRECTO" and not nombre:
        direct_partner = _get_direct_partner_member(sala, current_user_id)
        nombre = str(getattr(direct_partner, "usuario_nombre", "") or getattr(direct_partner, "id_usuario", "")).strip() or "Chat directo"
    elif tipo == "DIRECTO":
        direct_partner = _get_direct_partner_member(sala, current_user_id)
    miembros_count = sala.miembros.filter(activo=True).count()
    partner_id = _to_int(getattr(direct_partner, "id_usuario", 0), 0)
    return {
        "id_sala": int(sala.id_sala),
        "tipo": tipo,
        "nombre": nombre or f"Sala {sala.id_sala}",
        "miembros_count": miembros_count,
        "direct_partner_id": partner_id,
        "direct_partner_online": bool(partner_id and is_user_online(partner_id)),
        "actualizada_en": timezone.localtime(sala.actualizada_en).strftime("%Y-%m-%d %H:%M:%S") if sala.actualizada_en else "",
        "ultimo_mensaje": _message_preview_text(last_msg),
        "ultimo_usuario": str(getattr(last_msg, "usuario_nombre", "") or "").strip(),
        "ultimo_en": timezone.localtime(last_msg.creado_en).strftime("%Y-%m-%d %H:%M:%S") if last_msg and last_msg.creado_en else "",
    }


def _visible_messages_for_room(sala, hidden_message_ids):
    rows = list(getattr(sala, "_prefetched_objects_cache", {}).get("mensajes", []) or sala.mensajes.all())
    return [msg for msg in rows if int(msg.id_mensaje) not in hidden_message_ids]


def _save_voice_note_file(upload):
    base_dir = settings.MEDIA_ROOT / "chat_voice_notes"
    os.makedirs(base_dir, exist_ok=True)
    suffix = os.path.splitext(str(getattr(upload, "name", "") or "").strip())[1].lower() or ".webm"
    filename = f"voice_{timezone.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:10]}{suffix}"
    file_path = base_dir / filename
    with open(file_path, "wb+") as destination:
        for chunk in upload.chunks():
            destination.write(chunk)
    return f"{settings.MEDIA_URL.rstrip('/')}/chat_voice_notes/{filename}"


def _save_attachment_file(upload):
    base_dir = settings.MEDIA_ROOT / "chat_attachments"
    os.makedirs(base_dir, exist_ok=True)
    suffix = os.path.splitext(str(getattr(upload, "name", "") or "").strip())[1].lower() or ".bin"
    filename = f"attachment_{timezone.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:10]}{suffix}"
    file_path = base_dir / filename
    with open(file_path, "wb+") as destination:
        for chunk in upload.chunks():
            destination.write(chunk)
    return f"{settings.MEDIA_URL.rstrip('/')}/chat_attachments/{filename}"


def _ensure_member(sala, user_id, user_name):
    member, created = ChatSalaMiembro.objects.get_or_create(
        sala=sala,
        id_usuario=int(user_id),
        defaults={
            "usuario_nombre": str(user_name or "").strip()[:120],
            "activo": True,
        },
    )
    changed = False
    if not member.activo:
        member.activo = True
        changed = True
    safe_name = str(user_name or "").strip()[:120]
    if safe_name and member.usuario_nombre != safe_name:
        member.usuario_nombre = safe_name
        changed = True
    if changed and not created:
        member.save(update_fields=["activo", "usuario_nombre"])
    return member


def _load_active_users(exclude_user_id=0, query=""):
    where_parts = ["UPPER(ISNULL(ESTADO, '')) = 'ACTIVO'"]
    params = []
    if exclude_user_id:
        where_parts.append("TRY_CAST(ID_USUARIO AS BIGINT) <> %s")
        params.append(int(exclude_user_id))
    q = str(query or "").strip()
    if q:
        like = f"%{q}%"
        where_parts.append("(USUARIO LIKE %s OR NOMBRE LIKE %s OR CAST(ID_USUARIO AS NVARCHAR(32)) LIKE %s)")
        params.extend([like, like, like])

    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT TOP 200 ID_USUARIO, ISNULL(USUARIO, ''), ISNULL(NOMBRE, USUARIO)
            FROM USUARIO
            WHERE {' AND '.join(where_parts)}
            ORDER BY NOMBRE, USUARIO
            """,
            params,
        )
        return [
            {
                "id_usuario": _to_int(row[0], 0),
                "usuario_login": str(row[1] or "").strip(),
                "usuario_nombre": str(row[2] or "").strip(),
            }
            for row in cursor.fetchall()
            if row and _to_int(row[0], 0) > 0
        ]


def _build_shared_record_item(*, record_type, record_id, module_label, title, subtitle="", description="", target_url="", cta_label="Abrir registro"):
    return {
        "record_type": record_type,
        "record_id": str(record_id or "").strip(),
        "module_label": str(module_label or "").strip(),
        "title": str(title or "").strip(),
        "subtitle": str(subtitle or "").strip(),
        "description": str(description or "").strip(),
        "target_url": str(target_url or "").strip(),
        "cta_label": str(cta_label or "").strip() or "Abrir registro",
    }


def _format_date_label(value):
    if not value:
        return ""
    try:
        if hasattr(value, "tzinfo") and value.tzinfo is not None:
            value = timezone.localtime(value)
        return value.strftime("%d/%m/%Y")
    except Exception:
        return str(value).strip()


def _search_client_records(query):
    q = str(query or "").strip()
    qs = MaestroSn.objects.all()
    if q:
        qs = qs.filter(
            Q(id_sn__icontains=q)
            | Q(nom_socio__icontains=q)
            | Q(contacto__icontains=q)
            | Q(rnc_ced__icontains=q)
            | Q(tel1__icontains=q)
        )
    rows = list(
        qs.order_by("nom_socio", "id_sn")
        .values("id_sn", "nom_socio", "contacto", "rnc_ced", "tel1", "dir_factura")[:25]
    )
    results = []
    for row in rows:
        id_sn = str(row.get("id_sn") or "").strip()
        if not id_sn:
            continue
        target_url = reverse("clientes_mod:index") + f"?shared_record=cliente&id_sn={id_sn}"
        subtitle = " / ".join(
            part for part in [str(row.get("contacto") or "").strip(), str(row.get("rnc_ced") or "").strip()] if part
        )
        description = " / ".join(
            part for part in [str(row.get("dir_factura") or "").strip(), str(row.get("tel1") or "").strip()] if part
        )
        results.append(
            _build_shared_record_item(
                record_type="cliente",
                record_id=id_sn,
                module_label="Clientes",
                title=str(row.get("nom_socio") or id_sn).strip(),
                subtitle=subtitle or id_sn,
                description=description,
                target_url=target_url,
                cta_label="Abrir cliente",
            )
        )
    return results


def _search_cxc_records(query):
    merged = []
    seen = set()
    # Buscar siempre por cliente y recibo para que el nombre del cliente
    # encuentre pagos aunque el usuario no conozca el numero del documento.
    for filtro in ["cliente", "recibo"]:
        for row in _load_cxc_recibos_busqueda(query=query, filtro=filtro, limit=20):
            key = str(row.get("recibo_id") or row.get("no_recibo") or "").strip()
            if not key or key in seen:
                continue
            seen.add(key)
            merged.append(row)
    results = []
    for row in merged[:25]:
        recibo_id = str(row.get("recibo_id") or row.get("no_recibo") or "").strip()
        if not recibo_id:
            continue
        no_recibo = str(row.get("no_recibo") or recibo_id).strip()
        subtitle = " / ".join(
            part
            for part in [
                str(row.get("cliente_codigo") or "").strip(),
                str(row.get("cliente_nombre") or row.get("cliente") or "").strip(),
            ]
            if part
        )
        description = " / ".join(
            part
            for part in [
                str(row.get("fecha_cont") or "").strip(),
                f"Total RD$ {float(row.get('total_cobro') or 0):,.2f}",
            ]
            if part
        )
        results.append(
            _build_shared_record_item(
                record_type="cuenta_por_cobrar",
                record_id=recibo_id,
                module_label="Cuentas por cobrar",
                title=f"Recibo {no_recibo}",
                subtitle=subtitle,
                description=description,
                target_url=reverse("caja:cuentas_por_cobrar") + f"?shared_record=cxc&recibo_id={recibo_id}",
                cta_label="Abrir recibo",
            )
        )
    return results


def _search_factura_records(query):
    q = str(query or "").strip()
    sql = """
        SELECT TOP 25
            ID_DOC,
            ID_SN,
            NOM_SOCIO,
            FECHA_DOC,
            TOTAL_DOC,
            ISNULL(NCF, '')
        FROM CAB_FACTURA
        WHERE (TRY_CAST(ID_NCF AS BIGINT) IS NULL OR TRY_CAST(ID_NCF AS BIGINT) <> 34)
    """
    params = []
    if q:
        like = f"%{q}%"
        sql += """
          AND (
                CAST(ID_DOC AS VARCHAR(50)) LIKE %s
             OR ID_SN LIKE %s
             OR NOM_SOCIO LIKE %s
             OR ISNULL(NCF, '') LIKE %s
          )
        """
        params.extend([like, like, like, like])
    sql += " ORDER BY TRY_CAST(ID_DOC AS BIGINT) DESC, ID_DOC DESC"
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()
    results = []
    for row in rows:
        id_doc = str(row[0] or "").strip()
        if not id_doc:
            continue
        description = " / ".join(
            part
            for part in [
                _format_date_label(row[3]),
                f"Total RD$ {float(row[4] or 0):,.2f}",
                str(row[5] or "").strip(),
            ]
            if part
        )
        results.append(
            _build_shared_record_item(
                record_type="factura",
                record_id=id_doc,
                module_label="Facturas",
                title=f"Factura {id_doc}",
                subtitle=" / ".join(part for part in [str(row[1] or "").strip(), str(row[2] or "").strip()] if part),
                description=description,
                target_url=reverse("factura:facturacion") + f"?shared_record=factura&id_doc={id_doc}",
                cta_label="Abrir factura",
            )
        )
    return results


def _search_financiamiento_records(query):
    merged = []
    seen = set()
    # Iniciar por nombre para que el nombre del cliente sea la via principal
    # de busqueda, sin perder documento ni codigo.
    for filtro in ["nombre", "codigo", "documento"]:
        for row in _load_financiamiento_search_rows(query=query, filtro=filtro, limit=20):
            key = str(row.get("no_doc") or row.get("no") or "").strip()
            if not key or key in seen:
                continue
            seen.add(key)
            merged.append(row)
    results = []
    for row in merged[:25]:
        no_doc = str(row.get("no_doc") or row.get("no") or "").strip()
        if not no_doc:
            continue
        results.append(
            _build_shared_record_item(
                record_type="financiamiento",
                record_id=no_doc,
                module_label="Financiamiento",
                title=f"Financiamiento {str(row.get('no') or no_doc).strip()}",
                subtitle=" / ".join(
                    part for part in [str(row.get("codigo") or "").strip(), str(row.get("nombre") or "").strip()] if part
                ),
                description=" / ".join(
                    part
                    for part in [
                        str(row.get("fecha") or "").strip(),
                        f"Balance RD$ {float(row.get('saldo') or 0):,.2f}",
                    ]
                    if part
                ),
                target_url=reverse("caja:financiamiento") + f"?shared_record=financiamiento&no_doc={no_doc}",
                cta_label="Abrir financiamiento",
            )
        )
    return results


def index(request):
    ctx = _base_context(request, page_title="Chat Interno", active_nav="chat_interno")
    if not ctx:
        return redirect("login")
    usuario_id = ctx["auth_payload"]["usuario_id"]
    if not _chat_perm(usuario_id, "ver"):
        return render_denied(request, active_nav="chat_interno")
    ctx["chat_permissions"] = {
        "crear_grupos": _chat_perm(usuario_id, "crear_grupos"),
        "enviar_mensajes": _chat_perm(usuario_id, "enviar_mensajes"),
        "ver_usuarios": _chat_perm(usuario_id, "ver_usuarios"),
    }
    ctx["chat_share_permissions"] = {
        "cliente": has_perm(usuario_id, "clientes", "ver"),
        "cuenta_por_cobrar": has_perm(usuario_id, "caja", "ver_cuentas_por_cobrar"),
        "factura": has_perm(usuario_id, "factura", "ver_documentos"),
        "financiamiento": has_perm(usuario_id, "caja", "ver_financiamiento"),
    }
    return render(request, "chat_interno/index.html", ctx)


@require_GET
def usuarios_view(request):
    auth_payload = _require_perm_json(request, "chat_interno", "ver")
    if isinstance(auth_payload, JsonResponse):
        return auth_payload
    if not _chat_perm(auth_payload.get("usuario_id"), "ver_usuarios"):
        return JsonResponse({"detail": "No tienes permiso para ver usuarios del chat."}, status=403)
    q = (request.GET.get("q") or "").strip()
    results = _load_active_users(exclude_user_id=auth_payload.get("usuario_id"), query=q)
    return JsonResponse({"results": results})


@require_GET
def registros_compartibles_view(request):
    auth_payload = _require_perm_json(request, "chat_interno", "ver")
    if isinstance(auth_payload, JsonResponse):
        return auth_payload
    user_id = _to_int(auth_payload.get("usuario_id"), 0)
    record_type = str(request.GET.get("tipo") or "").strip().lower()
    query = (request.GET.get("q") or "").strip()
    if record_type not in {"cliente", "cuenta_por_cobrar", "factura", "financiamiento"}:
        return JsonResponse({"detail": "Tipo de registro no valido."}, status=400)

    allowed = {
        "cliente": has_perm(user_id, "clientes", "ver"),
        "cuenta_por_cobrar": has_perm(user_id, "caja", "ver_cuentas_por_cobrar"),
        "factura": has_perm(user_id, "factura", "ver_documentos"),
        "financiamiento": has_perm(user_id, "caja", "ver_financiamiento"),
    }
    if not allowed.get(record_type):
        return JsonResponse({"detail": "No tienes permiso para compartir este tipo de registro."}, status=403)

    try:
        if record_type == "cliente":
            results = _search_client_records(query)
        elif record_type == "cuenta_por_cobrar":
            results = _search_cxc_records(query)
        elif record_type == "factura":
            results = _search_factura_records(query)
        else:
            results = _search_financiamiento_records(query)
    except Exception:
        return JsonResponse({"detail": "No se pudieron cargar los registros para compartir."}, status=500)
    return JsonResponse({"results": results})


@require_GET
def salas_view(request):
    auth_payload = _require_perm_json(request, "chat_interno", "ver")
    if isinstance(auth_payload, JsonResponse):
        return auth_payload
    if not _chat_storage_ready():
        return _chat_storage_error_response()
    user_id = _to_int(auth_payload.get("usuario_id"), 0)
    try:
        sala_ids = list(
            ChatSalaMiembro.objects.filter(id_usuario=user_id, activo=True)
            .values_list("sala_id", flat=True)
        )
        salas = (
            ChatSala.objects.filter(id_sala__in=sala_ids, activa=True)
            .prefetch_related("miembros", "mensajes")
            .order_by("-actualizada_en", "-id_sala")
        )
        hidden_message_ids_by_room = {}
        hidden_rooms = {}
        if _chat_hide_storage_ready():
            hidden_rows = ChatMensajeOculto.objects.filter(id_usuario=user_id, sala_id__in=sala_ids).values_list("sala_id", "mensaje_id")
            for room_id, message_id in hidden_rows:
                hidden_message_ids_by_room.setdefault(int(room_id), set()).add(int(message_id))
            hidden_rooms = {
                int(row.sala_id): row.ocultado_en
                for row in ChatSalaOculta.objects.filter(id_usuario=user_id, sala_id__in=sala_ids)
            }
        results = []
        for sala in salas:
            room_hidden_message_ids = hidden_message_ids_by_room.get(int(sala.id_sala), set())
            visible_messages = _visible_messages_for_room(sala, room_hidden_message_ids)
            last_visible_msg = visible_messages[-1] if visible_messages else None
            hidden_at = hidden_rooms.get(int(sala.id_sala))
            latest_any_msg = visible_messages[-1] if visible_messages else None
            if hidden_at and (not latest_any_msg or latest_any_msg.creado_en <= hidden_at):
                continue
            results.append(_serialize_sala(sala, user_id, last_msg=last_visible_msg))
        return JsonResponse({"results": results})
    except DatabaseError:
        return _chat_storage_error_response()


@require_GET
def mensajes_view(request):
    auth_payload = _require_perm_json(request, "chat_interno", "ver")
    if isinstance(auth_payload, JsonResponse):
        return auth_payload
    if not _chat_storage_ready():
        return _chat_storage_error_response()
    user_id = _to_int(auth_payload.get("usuario_id"), 0)
    sala_id = _to_int(request.GET.get("sala_id"), 0)
    if sala_id <= 0:
        return JsonResponse({"detail": "Parametro sala_id requerido"}, status=400)
    try:
        is_member = ChatSalaMiembro.objects.filter(sala_id=sala_id, id_usuario=user_id, activo=True).exists()
        if not is_member:
            return JsonResponse({"detail": "No tienes acceso a esta sala."}, status=403)
        sala = ChatSala.objects.filter(id_sala=sala_id).first()
        sala_is_direct = bool(sala and str(sala.tipo or "").strip().upper() == "DIRECTO")
        direct_partner = _get_direct_partner_member(sala, user_id) if sala_is_direct else None
        direct_partner_id = _to_int(getattr(direct_partner, "id_usuario", 0), 0)
        partner_online = bool(direct_partner_id and is_user_online(direct_partner_id))
        mensajes = list(ChatMensaje.objects.filter(sala_id=sala_id).order_by("id_mensaje")[:400])
        hidden_message_ids = set()
        if _chat_hide_storage_ready():
            hidden_message_ids = set(
                ChatMensajeOculto.objects.filter(sala_id=sala_id, id_usuario=user_id).values_list("mensaje_id", flat=True)
            )
            mensajes = [msg for msg in mensajes if int(msg.id_mensaje) not in hidden_message_ids]
        my_msg_ids = [int(msg.id_mensaje) for msg in mensajes if _to_int(msg.id_usuario, 0) == user_id]
        read_msg_ids = set()
        if my_msg_ids:
            read_msg_ids = set(
                ChatMensajeLectura.objects.filter(
                    mensaje_id__in=my_msg_ids,
                    sala_id=sala_id,
                )
                .exclude(id_usuario=user_id)
                .values_list("mensaje_id", flat=True)
            )
        results = []
        for msg in mensajes:
            item = _serialize_mensaje(msg)
            if _to_int(msg.id_usuario, 0) == user_id:
                item["read_by_other"] = _to_int(msg.id_mensaje, 0) in read_msg_ids
                if sala_is_direct and not item["read_by_other"]:
                    item["delivered_to_other"] = partner_online
            results.append(item)
        return JsonResponse({"results": results})
    except DatabaseError:
        return _chat_storage_error_response()


@require_http_methods(["POST"])
def iniciar_directo_view(request):
    auth_payload = _require_perm_json(request, "chat_interno", "ver")
    if isinstance(auth_payload, JsonResponse):
        return auth_payload
    sender_id = _to_int(auth_payload.get("usuario_id"), 0)
    sender_name = str(auth_payload.get("usuario_nombre") or "").strip()
    if not _chat_perm(sender_id, "enviar_mensajes"):
        return JsonResponse({"detail": "No tienes permiso para iniciar chats."}, status=403)
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"detail": "JSON invalido"}, status=400)
    target_id = _to_int(payload.get("id_usuario"), 0)
    if target_id <= 0 or target_id == sender_id:
        return JsonResponse({"detail": "Usuario destino invalido."}, status=400)

    target_row = next((u for u in _load_active_users(exclude_user_id=0) if _to_int(u.get("id_usuario"), 0) == target_id), None)
    if not target_row:
        return JsonResponse({"detail": "Usuario destino no encontrado o inactivo."}, status=404)
    target_name = str(target_row.get("usuario_nombre") or target_row.get("usuario_login") or target_id).strip()

    pair = sorted([str(sender_id), str(target_id)])
    direct_key = ":".join(pair)
    try:
        with transaction.atomic():
            sala, _ = ChatSala.objects.get_or_create(
                direct_key=direct_key,
                defaults={
                    "tipo": "DIRECTO",
                    "nombre": "",
                    "creada_por": sender_id,
                    "activa": True,
                },
            )
            _ensure_member(sala, sender_id, sender_name)
            _ensure_member(sala, target_id, target_name)
            room_sender = _serialize_sala(sala, sender_id)
            room_target = _serialize_sala(sala, target_id)
            transaction.on_commit(
                lambda sid=sender_id, room=room_sender: broadcast_chat_room_update(user_id=sid, room=room)
            )
            transaction.on_commit(
                lambda tid=target_id, room=room_target: broadcast_chat_room_update(user_id=tid, room=room)
            )
        return JsonResponse({"sala": _serialize_sala(sala, sender_id)})
    except DatabaseError:
        return _chat_storage_error_response()


@require_http_methods(["POST"])
def crear_grupo_view(request):
    auth_payload = _require_perm_json(request, "chat_interno", "ver")
    if isinstance(auth_payload, JsonResponse):
        return auth_payload
    creator_id = _to_int(auth_payload.get("usuario_id"), 0)
    creator_name = str(auth_payload.get("usuario_nombre") or "").strip()
    if not _chat_perm(creator_id, "crear_grupos"):
        return JsonResponse({"detail": "No tienes permiso para crear grupos."}, status=403)
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"detail": "JSON invalido"}, status=400)
    nombre = str(payload.get("nombre") or "").strip()
    if not nombre:
        return JsonResponse({"detail": "El nombre del grupo es obligatorio."}, status=400)
    member_ids_raw = payload.get("miembros") or []
    if not isinstance(member_ids_raw, list):
        return JsonResponse({"detail": "miembros invalido."}, status=400)
    selected_member_ids = {_to_int(item, 0) for item in member_ids_raw}
    selected_member_ids.discard(0)
    selected_member_ids.add(creator_id)

    active_users = { _to_int(u.get("id_usuario"), 0): u for u in _load_active_users(exclude_user_id=0) }
    invalid_ids = [uid for uid in selected_member_ids if uid not in active_users and uid != creator_id]
    if invalid_ids:
        return JsonResponse({"detail": "Hay usuarios invalidos en la lista del grupo."}, status=400)

    try:
        with transaction.atomic():
            sala = ChatSala.objects.create(
                tipo="GRUPO",
                nombre=nombre[:120],
                creada_por=creator_id,
                activa=True,
            )
            _ensure_member(sala, creator_id, creator_name)
            member_ids_for_notify = [creator_id]
            for uid in sorted(selected_member_ids):
                if uid == creator_id:
                    continue
                user_row = active_users.get(uid) or {}
                user_name = str(user_row.get("usuario_nombre") or user_row.get("usuario_login") or uid).strip()
                _ensure_member(sala, uid, user_name)
                member_ids_for_notify.append(uid)
            for uid in member_ids_for_notify:
                room_payload = _serialize_sala(sala, uid)
                transaction.on_commit(
                    lambda target_id=uid, room=room_payload: broadcast_chat_room_update(user_id=target_id, room=room)
                )
        return JsonResponse({"sala": _serialize_sala(sala, creator_id)})
    except DatabaseError:
        return _chat_storage_error_response()


@require_http_methods(["POST"])
def enviar_mensaje_view(request):
    auth_payload = _require_perm_json(request, "chat_interno", "ver")
    if isinstance(auth_payload, JsonResponse):
        return auth_payload
    sender_id = _to_int(auth_payload.get("usuario_id"), 0)
    sender_name = str(auth_payload.get("usuario_nombre") or "").strip()
    if not _chat_perm(sender_id, "enviar_mensajes"):
        return JsonResponse({"detail": "No tienes permiso para enviar mensajes."}, status=403)
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"detail": "JSON invalido"}, status=400)
    sala_id = _to_int(payload.get("sala_id"), 0)
    contenido = str(payload.get("contenido") or "").strip()
    event_id = str(payload.get("event_id") or "").strip()
    if sala_id <= 0:
        return JsonResponse({"detail": "Parametro sala_id requerido"}, status=400)
    if not contenido:
        return JsonResponse({"detail": "El mensaje no puede estar vacio."}, status=400)

    try:
        is_member = ChatSalaMiembro.objects.filter(sala_id=sala_id, id_usuario=sender_id, activo=True).exists()
        if not is_member:
            return JsonResponse({"detail": "No tienes acceso a esta sala."}, status=403)

        with transaction.atomic():
            msg = ChatMensaje.objects.create(
                sala_id=sala_id,
                id_usuario=sender_id,
                usuario_nombre=sender_name[:120],
                contenido=contenido,
                event_id=event_id[:80] if event_id else None,
            )
            ChatSala.objects.filter(id_sala=sala_id).update(actualizada_en=timezone.now())
            sala = ChatSala.objects.filter(id_sala=sala_id).first()
            member_ids = list(
                ChatSalaMiembro.objects.filter(sala_id=sala_id, activo=True)
                .values_list("id_usuario", flat=True)
            )
            msg_payload = _serialize_mensaje(msg)
            if sala and str(sala.tipo or "").strip().upper() == "DIRECTO":
                partner = _get_direct_partner_member(sala, sender_id)
                partner_id = _to_int(getattr(partner, "id_usuario", 0), 0)
                msg_payload["delivered_to_other"] = bool(partner_id and is_user_online(partner_id))
            for member_id in member_ids:
                room_payload = _serialize_sala(sala, member_id) if sala else {
                    "id_sala": sala_id,
                    "tipo": "",
                    "nombre": "",
                    "miembros_count": len(member_ids),
                    "direct_partner_id": 0,
                    "direct_partner_online": False,
                    "actualizada_en": "",
                    "ultimo_mensaje": contenido,
                    "ultimo_usuario": sender_name,
                    "ultimo_en": msg_payload.get("creado_en", ""),
                }
                transaction.on_commit(
                    lambda uid=member_id, mp=msg_payload, rp=room_payload: broadcast_chat_message(
                        user_id=uid,
                        message=mp,
                        room=rp,
                    )
                )
        message_payload = _serialize_mensaje(msg)
        message_payload["read_by_other"] = False
        message_payload["delivered_to_other"] = bool(msg_payload.get("delivered_to_other"))
        return JsonResponse({"ok": True, "message": message_payload})
    except DatabaseError:
        return _chat_storage_error_response()


@require_http_methods(["POST"])
def enviar_nota_voz_view(request):
    auth_payload = _require_perm_json(request, "chat_interno", "ver")
    if isinstance(auth_payload, JsonResponse):
        return auth_payload
    sender_id = _to_int(auth_payload.get("usuario_id"), 0)
    sender_name = str(auth_payload.get("usuario_nombre") or "").strip()
    if not _chat_perm(sender_id, "enviar_mensajes"):
        return JsonResponse({"detail": "No tienes permiso para enviar mensajes."}, status=403)

    sala_id = _to_int(request.POST.get("sala_id"), 0)
    duration_seconds = _to_int(request.POST.get("duration_seconds"), 0)
    event_id = str(request.POST.get("event_id") or "").strip()
    audio_file = request.FILES.get("audio")
    if sala_id <= 0:
        return JsonResponse({"detail": "Parametro sala_id requerido"}, status=400)
    if not audio_file:
        return JsonResponse({"detail": "No se recibio el audio."}, status=400)

    try:
        is_member = ChatSalaMiembro.objects.filter(sala_id=sala_id, id_usuario=sender_id, activo=True).exists()
        if not is_member:
            return JsonResponse({"detail": "No tienes acceso a esta sala."}, status=403)

        file_url = _save_voice_note_file(audio_file)
        mime_type = str(getattr(audio_file, "content_type", "") or "").strip()
        content = _build_voice_note_content(
            file_url=file_url,
            duration_seconds=duration_seconds,
            mime_type=mime_type,
            original_name=str(getattr(audio_file, "name", "") or "").strip(),
        )

        with transaction.atomic():
            msg = ChatMensaje.objects.create(
                sala_id=sala_id,
                id_usuario=sender_id,
                usuario_nombre=sender_name[:120],
                contenido=content,
                event_id=event_id[:80] if event_id else None,
            )
            ChatSala.objects.filter(id_sala=sala_id).update(actualizada_en=timezone.now())
            sala = ChatSala.objects.filter(id_sala=sala_id).first()
            member_ids = list(
                ChatSalaMiembro.objects.filter(sala_id=sala_id, activo=True)
                .values_list("id_usuario", flat=True)
            )
            msg_payload = _serialize_mensaje(msg)
            if sala and str(sala.tipo or "").strip().upper() == "DIRECTO":
                partner = _get_direct_partner_member(sala, sender_id)
                partner_id = _to_int(getattr(partner, "id_usuario", 0), 0)
                msg_payload["delivered_to_other"] = bool(partner_id and is_user_online(partner_id))
            for member_id in member_ids:
                room_payload = _serialize_sala(sala, member_id) if sala else {
                    "id_sala": sala_id,
                    "tipo": "",
                    "nombre": "",
                    "miembros_count": len(member_ids),
                    "direct_partner_id": 0,
                    "direct_partner_online": False,
                    "actualizada_en": "",
                    "ultimo_mensaje": "Nota de voz",
                    "ultimo_usuario": sender_name,
                    "ultimo_en": msg_payload.get("creado_en", ""),
                }
                transaction.on_commit(
                    lambda uid=member_id, mp=msg_payload, rp=room_payload: broadcast_chat_message(
                        user_id=uid,
                        message=mp,
                        room=rp,
                    )
                )
        message_payload = _serialize_mensaje(msg)
        message_payload["read_by_other"] = False
        message_payload["delivered_to_other"] = bool(msg_payload.get("delivered_to_other"))
        return JsonResponse({"ok": True, "message": message_payload})
    except DatabaseError:
        return _chat_storage_error_response()


@require_http_methods(["POST"])
def enviar_adjuntos_view(request):
    auth_payload = _require_perm_json(request, "chat_interno", "ver")
    if isinstance(auth_payload, JsonResponse):
        return auth_payload
    sender_id = _to_int(auth_payload.get("usuario_id"), 0)
    sender_name = str(auth_payload.get("usuario_nombre") or "").strip()
    if not _chat_perm(sender_id, "enviar_mensajes"):
        return JsonResponse({"detail": "No tienes permiso para enviar mensajes."}, status=403)

    sala_id = _to_int(request.POST.get("sala_id"), 0)
    event_id = str(request.POST.get("event_id") or "").strip()
    uploads = list(request.FILES.getlist("files"))
    if sala_id <= 0:
        return JsonResponse({"detail": "Parametro sala_id requerido"}, status=400)
    if not uploads:
        return JsonResponse({"detail": "No se recibieron archivos."}, status=400)

    total_bytes = 0
    category = ""
    validated_uploads = []
    for upload in uploads:
        file_size = max(0, _to_int(getattr(upload, "size", 0), 0))
        total_bytes += file_size
        if total_bytes > MAX_ATTACHMENTS_TOTAL_BYTES:
            return JsonResponse({"detail": "Los adjuntos no pueden superar 10 MB en total."}, status=400)
        item_category = _attachment_category_for_upload(upload)
        if not item_category:
            return JsonResponse({"detail": f"Archivo no permitido: {getattr(upload, 'name', 'archivo')}"}, status=400)
        if category and item_category != category:
            return JsonResponse({"detail": "Solo puedes enviar varios archivos del mismo tipo en un mismo mensaje."}, status=400)
        category = item_category
        validated_uploads.append((upload, file_size))

    try:
        is_member = ChatSalaMiembro.objects.filter(sala_id=sala_id, id_usuario=sender_id, activo=True).exists()
        if not is_member:
            return JsonResponse({"detail": "No tienes acceso a esta sala."}, status=403)

        attachment_items = []
        for upload, file_size in validated_uploads:
            file_url = _save_attachment_file(upload)
            attachment_items.append(
                {
                    "file_url": file_url,
                    "mime_type": str(getattr(upload, "content_type", "") or "").strip(),
                    "original_name": str(getattr(upload, "name", "") or "").strip(),
                    "size_bytes": file_size,
                }
            )

        content = _build_attachments_content(category=category, items=attachment_items)

        with transaction.atomic():
            msg = ChatMensaje.objects.create(
                sala_id=sala_id,
                id_usuario=sender_id,
                usuario_nombre=sender_name[:120],
                contenido=content,
                event_id=event_id[:80] if event_id else None,
            )
            ChatSala.objects.filter(id_sala=sala_id).update(actualizada_en=timezone.now())
            sala = ChatSala.objects.filter(id_sala=sala_id).first()
            member_ids = list(
                ChatSalaMiembro.objects.filter(sala_id=sala_id, activo=True)
                .values_list("id_usuario", flat=True)
            )
            msg_payload = _serialize_mensaje(msg)
            if sala and str(sala.tipo or "").strip().upper() == "DIRECTO":
                partner = _get_direct_partner_member(sala, sender_id)
                partner_id = _to_int(getattr(partner, "id_usuario", 0), 0)
                msg_payload["delivered_to_other"] = bool(partner_id and is_user_online(partner_id))
            preview_text = _attachments_preview_text(category, len(attachment_items))
            for member_id in member_ids:
                room_payload = _serialize_sala(sala, member_id) if sala else {
                    "id_sala": sala_id,
                    "tipo": "",
                    "nombre": "",
                    "miembros_count": len(member_ids),
                    "direct_partner_id": 0,
                    "direct_partner_online": False,
                    "actualizada_en": "",
                    "ultimo_mensaje": preview_text,
                    "ultimo_usuario": sender_name,
                    "ultimo_en": msg_payload.get("creado_en", ""),
                }
                transaction.on_commit(
                    lambda uid=member_id, mp=msg_payload, rp=room_payload: broadcast_chat_message(
                        user_id=uid,
                        message=mp,
                        room=rp,
                    )
                )
        message_payload = _serialize_mensaje(msg)
        message_payload["read_by_other"] = False
        message_payload["delivered_to_other"] = bool(msg_payload.get("delivered_to_other"))
        return JsonResponse({"ok": True, "message": message_payload})
    except DatabaseError:
        return _chat_storage_error_response()


@require_http_methods(["POST"])
def ocultar_mensaje_view(request):
    auth_payload = _require_perm_json(request, "chat_interno", "ver")
    if isinstance(auth_payload, JsonResponse):
        return auth_payload
    if not _chat_hide_storage_ready():
        return _chat_hide_storage_error_response()
    user_id = _to_int(auth_payload.get("usuario_id"), 0)
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"detail": "JSON invalido"}, status=400)
    message_id = _to_int(payload.get("message_id"), 0)
    if message_id <= 0:
        return JsonResponse({"detail": "Parametro message_id requerido"}, status=400)
    try:
        mensaje = ChatMensaje.objects.filter(id_mensaje=message_id).first()
        if not mensaje:
            return JsonResponse({"detail": "Mensaje no encontrado."}, status=404)
        is_member = ChatSalaMiembro.objects.filter(sala_id=mensaje.sala_id, id_usuario=user_id, activo=True).exists()
        if not is_member:
            return JsonResponse({"detail": "No tienes acceso a esta sala."}, status=403)
        ChatMensajeOculto.objects.get_or_create(
            mensaje_id=message_id,
            sala_id=mensaje.sala_id,
            id_usuario=user_id,
        )
        return JsonResponse({"ok": True, "message_id": int(message_id), "room_id": int(mensaje.sala_id)})
    except DatabaseError:
        return _chat_storage_error_response()


@require_http_methods(["POST"])
def ocultar_sala_view(request):
    auth_payload = _require_perm_json(request, "chat_interno", "ver")
    if isinstance(auth_payload, JsonResponse):
        return auth_payload
    if not _chat_hide_storage_ready():
        return _chat_hide_storage_error_response()
    user_id = _to_int(auth_payload.get("usuario_id"), 0)
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"detail": "JSON invalido"}, status=400)
    sala_id = _to_int(payload.get("sala_id"), 0)
    if sala_id <= 0:
        return JsonResponse({"detail": "Parametro sala_id requerido"}, status=400)
    try:
        is_member = ChatSalaMiembro.objects.filter(sala_id=sala_id, id_usuario=user_id, activo=True).exists()
        if not is_member:
            return JsonResponse({"detail": "No tienes acceso a esta sala."}, status=403)
        ChatSalaOculta.objects.update_or_create(
            sala_id=sala_id,
            id_usuario=user_id,
            defaults={"ocultado_en": timezone.now()},
        )
        return JsonResponse({"ok": True, "room_id": int(sala_id)})
    except DatabaseError:
        return _chat_storage_error_response()
