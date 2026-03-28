import json
import mimetypes
import uuid
from pathlib import Path
from urllib import error, request

from django.conf import settings
from django.db import OperationalError, ProgrammingError


class WhatsAppCloudError(Exception):
    def __init__(self, detail, status_code=None, payload=None):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code
        self.payload = payload or {}


def _setting(name, default=""):
    return str(getattr(settings, name, default) or "").strip()


def _get_db_config():
    try:
        from ajustes.models import WhatsAppCloudConfig

        return WhatsAppCloudConfig.objects.filter(id_config=1).first()
    except (OperationalError, ProgrammingError):
        return None
    except Exception:
        return None


def _clean_text(value, default=""):
    text = str(value or "").strip()
    return text if text else default


def get_runtime_settings():
    db_config = _get_db_config()
    if not db_config:
        return {
            "enabled": True,
            "api_version": _setting("WHATSAPP_API_VERSION", "v23.0") or "v23.0",
            "access_token": _setting("WHATSAPP_ACCESS_TOKEN"),
            "phone_number_id": _setting("WHATSAPP_PHONE_NUMBER_ID"),
            "waba_id": _setting("WHATSAPP_WABA_ID"),
            "verify_token": _setting("WHATSAPP_VERIFY_TOKEN"),
            "source": "env",
            "stored_in_db": False,
            "token_in_db": False,
        }

    env_fallback_used = False
    api_version = _clean_text(db_config.api_version, _setting("WHATSAPP_API_VERSION", "v23.0") or "v23.0")
    if not _clean_text(db_config.api_version):
        env_fallback_used = env_fallback_used or bool(_setting("WHATSAPP_API_VERSION"))
    access_token = _clean_text(db_config.access_token, _setting("WHATSAPP_ACCESS_TOKEN"))
    if not _clean_text(db_config.access_token):
        env_fallback_used = env_fallback_used or bool(_setting("WHATSAPP_ACCESS_TOKEN"))
    phone_number_id = _clean_text(db_config.phone_number_id, _setting("WHATSAPP_PHONE_NUMBER_ID"))
    if not _clean_text(db_config.phone_number_id):
        env_fallback_used = env_fallback_used or bool(_setting("WHATSAPP_PHONE_NUMBER_ID"))
    waba_id = _clean_text(db_config.waba_id, _setting("WHATSAPP_WABA_ID"))
    if not _clean_text(db_config.waba_id):
        env_fallback_used = env_fallback_used or bool(_setting("WHATSAPP_WABA_ID"))
    verify_token = _clean_text(db_config.verify_token, _setting("WHATSAPP_VERIFY_TOKEN"))
    if not _clean_text(db_config.verify_token):
        env_fallback_used = env_fallback_used or bool(_setting("WHATSAPP_VERIFY_TOKEN"))

    return {
        "enabled": bool(db_config.habilitado),
        "api_version": api_version,
        "access_token": access_token,
        "phone_number_id": phone_number_id,
        "waba_id": waba_id,
        "verify_token": verify_token,
        "source": "database+env" if env_fallback_used else "database",
        "stored_in_db": True,
        "token_in_db": bool(_clean_text(db_config.access_token)),
    }


def get_missing_settings():
    runtime = get_runtime_settings()
    missing = []
    if not runtime.get("enabled"):
        missing.append("habilitado")
    if not runtime.get("access_token"):
        missing.append("WHATSAPP_ACCESS_TOKEN")
    if not runtime.get("phone_number_id"):
        missing.append("WHATSAPP_PHONE_NUMBER_ID")
    return missing


def is_configured():
    return not get_missing_settings()


def get_verify_token():
    return get_runtime_settings().get("verify_token", "")


def _base_url():
    version = get_runtime_settings().get("api_version", "v23.0") or "v23.0"
    return f"https://graph.facebook.com/{version}"


def _auth_headers(extra=None):
    runtime = get_runtime_settings()
    headers = {
        "Authorization": f"Bearer {runtime.get('access_token', '')}",
    }
    if extra:
        headers.update(extra)
    return headers


def _parse_error(exc):
    payload = {}
    detail = "No se pudo comunicar con WhatsApp Cloud API."
    status_code = getattr(exc, "code", None)
    body = ""
    try:
        body = exc.read().decode("utf-8")
    except Exception:
        body = ""
    if body:
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {"raw": body}
    error_payload = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(error_payload, dict):
        detail = (
            error_payload.get("error_user_msg")
            or error_payload.get("message")
            or detail
        )
    elif body:
        detail = body
    return detail, status_code, payload


def _request_json(method, resource, payload):
    if not is_configured():
        raise WhatsAppCloudError("WhatsApp Cloud API no esta configurada.")

    url = f"{_base_url()}/{resource.lstrip('/')}"
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers=_auth_headers({"Content-Type": "application/json"}),
        method=method.upper(),
    )
    try:
        with request.urlopen(req, timeout=45) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw or "{}")
    except error.HTTPError as exc:
        detail, status_code, payload = _parse_error(exc)
        raise WhatsAppCloudError(detail, status_code=status_code, payload=payload) from exc
    except error.URLError as exc:
        raise WhatsAppCloudError(f"No se pudo conectar con WhatsApp Cloud API: {exc.reason}") from exc


def _build_multipart_body(fields, files):
    boundary = f"----CodexBoundary{uuid.uuid4().hex}"
    body = bytearray()

    for name, value in (fields or {}).items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode("utf-8")
        )

    for name, spec in (files or {}).items():
        filename, content, content_type = spec
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            (
                f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
                f"Content-Type: {content_type}\r\n\r\n"
            ).encode("utf-8")
        )
        body.extend(content)
        body.extend(b"\r\n")

    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    return boundary, bytes(body)


def upload_media(file_path, mime_type=""):
    if not is_configured():
        raise WhatsAppCloudError("WhatsApp Cloud API no esta configurada.")

    runtime = get_runtime_settings()
    path = Path(file_path)
    if not path.exists():
        raise WhatsAppCloudError("El documento de la carta no existe.")

    guessed_type = mime_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    boundary, body = _build_multipart_body(
        {"messaging_product": "whatsapp"},
        {"file": (path.name, path.read_bytes(), guessed_type)},
    )
    req = request.Request(
        f"{_base_url()}/{runtime.get('phone_number_id', '')}/media",
        data=body,
        headers=_auth_headers({"Content-Type": f"multipart/form-data; boundary={boundary}"}),
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw or "{}")
    except error.HTTPError as exc:
        detail, status_code, payload = _parse_error(exc)
        raise WhatsAppCloudError(detail, status_code=status_code, payload=payload) from exc
    except error.URLError as exc:
        raise WhatsAppCloudError(f"No se pudo conectar con WhatsApp Cloud API: {exc.reason}") from exc


def send_text_message(to, body):
    runtime = get_runtime_settings()
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": str(to or "").strip(),
        "type": "text",
        "text": {"body": str(body or "").strip()},
    }
    return _request_json("POST", f"{runtime.get('phone_number_id', '')}/messages", payload)


def send_document_message(to, media_id):
    runtime = get_runtime_settings()
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": str(to or "").strip(),
        "type": "document",
        "document": {"id": str(media_id or "").strip()},
    }
    return _request_json("POST", f"{runtime.get('phone_number_id', '')}/messages", payload)


def send_text_and_document(to, body, file_path, mime_type=""):
    media_response = upload_media(file_path, mime_type=mime_type)
    media_id = str((media_response or {}).get("id") or "").strip()
    if not media_id:
        raise WhatsAppCloudError("WhatsApp no devolvio un media_id valido.", payload=media_response)

    responses = {
        "media": media_response,
    }
    clean_body = str(body or "").strip()
    if clean_body:
        responses["text"] = send_text_message(to, clean_body)
    responses["document"] = send_document_message(to, media_id)
    return responses
