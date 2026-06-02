import base64

from django.db import connection, transaction

from .models import EmpleadoFoto


def get_employee_photo_data(id_empleado):
    try:
        id_empleado = int(id_empleado)
    except (TypeError, ValueError):
        return {"foto_b64": "", "foto_tipo": ""}

    try:
        registro = EmpleadoFoto.objects.filter(id_empleado=id_empleado).only("foto", "foto_tipo").first()
        if registro and registro.foto:
            return {
                "foto_b64": base64.b64encode(bytes(registro.foto)).decode("ascii"),
                "foto_tipo": registro.foto_tipo or "image/png",
            }
    except Exception:
        return {"foto_b64": "", "foto_tipo": ""}
    return {"foto_b64": "", "foto_tipo": ""}


def save_employee_photo(id_empleado, foto_bytes, foto_tipo):
    try:
        id_empleado = int(id_empleado)
    except (TypeError, ValueError):
        return None

    if not foto_bytes:
        return None

    foto_tipo = str(foto_tipo or "image/png").strip()[:80]
    try:
        with transaction.atomic():
            registro, _ = EmpleadoFoto.objects.update_or_create(
                id_empleado=id_empleado,
                defaults={"foto": foto_bytes, "foto_tipo": foto_tipo},
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE EMPLEADO_NOMINA SET ID_FOTO = %s WHERE ID_EMPLEADO = %s",
                    [int(registro.id_foto), id_empleado],
                )
            return registro
    except Exception:
        return None
