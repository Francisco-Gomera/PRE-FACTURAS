from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


NOTIFICATION_GROUP_NAME = "ca_erp.notifications"
PREFACTURA_GROUP_NAME = "ca_erp.prefacturas"
CXC_GROUP_NAME = "ca_erp.cxc"
FINANCIAMIENTO_GROUP_NAME = "ca_erp.financiamiento"
INVENTARIO_SOLICITUDES_GROUP_NAME = "ca_erp.inventario.solicitudes"
CHAT_USER_GROUP_PREFIX = "ca_erp.chat.user"


def broadcast_notification_refresh(*, reason="updated"):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return False
    async_to_sync(channel_layer.group_send)(
        NOTIFICATION_GROUP_NAME,
        {
            "type": "notification.refresh",
            "reason": str(reason or "updated").strip() or "updated",
        },
    )
    return True


def broadcast_inventario_solicitudes_refresh(*, reason="updated"):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return False
    async_to_sync(channel_layer.group_send)(
        INVENTARIO_SOLICITUDES_GROUP_NAME,
        {
            "type": "inventario.solicitudes_refresh",
            "reason": str(reason or "updated").strip() or "updated",
        },
    )
    return True


def broadcast_prefacturas_refresh(*, reason="updated", event_id=""):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return False
    async_to_sync(channel_layer.group_send)(
        PREFACTURA_GROUP_NAME,
        {
            "type": "prefactura.refresh",
            "reason": str(reason or "updated").strip() or "updated",
            "event_id": str(event_id or "").strip(),
        },
    )
    return True


def broadcast_prefactura_document_status(*, document_id, estado="", reason="updated", event_id=""):
    document_key = str(document_id or "").strip()
    if not document_key:
        return False
    channel_layer = get_channel_layer()
    if not channel_layer:
        return False
    async_to_sync(channel_layer.group_send)(
        PREFACTURA_GROUP_NAME,
        {
            "type": "prefactura.document_status",
            "document_id": document_key,
            "estado": str(estado or "").strip(),
            "reason": str(reason or "updated").strip() or "updated",
            "event_id": str(event_id or "").strip(),
        },
    )
    return True


def broadcast_factura_document_status(*, document_id, estado="", reason="updated", event_id=""):
    document_key = str(document_id or "").strip()
    if not document_key:
        return False
    channel_layer = get_channel_layer()
    if not channel_layer:
        return False
    async_to_sync(channel_layer.group_send)(
        PREFACTURA_GROUP_NAME,
        {
            "type": "factura.document_status",
            "document_id": document_key,
            "estado": str(estado or "").strip(),
            "reason": str(reason or "updated").strip() or "updated",
            "event_id": str(event_id or "").strip(),
        },
    )
    return True


def broadcast_cxc_document_status(*, document_id, no_recibo="", estado="", reason="updated", event_id=""):
    document_key = str(document_id or "").strip()
    if not document_key:
        return False
    channel_layer = get_channel_layer()
    if not channel_layer:
        return False
    async_to_sync(channel_layer.group_send)(
        CXC_GROUP_NAME,
        {
            "type": "cxc.document_status",
            "document_id": document_key,
            "no_recibo": str(no_recibo or "").strip(),
            "estado": str(estado or "").strip(),
            "reason": str(reason or "updated").strip() or "updated",
            "event_id": str(event_id or "").strip(),
        },
    )
    return True


def broadcast_financiamiento_document_status(*, document_id, factura_no="", estado="", reason="updated", event_id=""):
    document_key = str(document_id or "").strip()
    if not document_key:
        return False
    channel_layer = get_channel_layer()
    if not channel_layer:
        return False
    async_to_sync(channel_layer.group_send)(
        FINANCIAMIENTO_GROUP_NAME,
        {
            "type": "financiamiento.document_status",
            "document_id": document_key,
            "factura_no": str(factura_no or "").strip(),
            "estado": str(estado or "").strip(),
            "reason": str(reason or "updated").strip() or "updated",
            "event_id": str(event_id or "").strip(),
        },
    )
    return True


def chat_user_group_name(user_id):
    user_key = str(user_id or "").strip()
    if not user_key:
        return ""
    return f"{CHAT_USER_GROUP_PREFIX}.{user_key}"


def broadcast_chat_message(*, user_id, message, room):
    group_name = chat_user_group_name(user_id)
    if not group_name:
        return False
    channel_layer = get_channel_layer()
    if not channel_layer:
        return False
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "chat.message",
            "message": message or {},
            "room": room or {},
        },
    )
    return True


def broadcast_chat_room_update(*, user_id, room):
    group_name = chat_user_group_name(user_id)
    if not group_name:
        return False
    channel_layer = get_channel_layer()
    if not channel_layer:
        return False
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "chat.room",
            "room": room or {},
        },
    )
    return True
