import json
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from ajustes.permissions import has_perm
from core.views import _base_context, render_denied
from inventario.views import _load_departamento_rows

from .models import EmpleadoEstudio, EmpleadoExperienciaLaboral, EmpleadoNomina


DATE_FIELDS = {"fecha_nacimiento"}
REQUIRED_FIELDS = [
    ("nombres", "Los nombres son obligatorios."),
    ("apellidos", "Los apellidos son obligatorios."),
    ("cedula", "La cedula es obligatoria."),
    ("estado_civil", "El estado civil es obligatorio."),
    ("direccion", "La direccion es obligatoria."),
    ("telefono", "El telefono es obligatorio."),
    ("fecha_nacimiento", "La fecha de nacimiento es obligatoria."),
    ("nacionalidad", "La nacionalidad es obligatoria."),
    ("genero", "El genero es obligatorio."),
    ("clase_empleado", "La clase de empleado es obligatoria."),
    ("cargo", "El cargo es obligatorio."),
    ("departamento", "El departamento es obligatorio."),
    ("tipo_empleado", "El tipo de empleado es obligatorio."),
]
TEXT_FIELDS = [
    "codigo",
    "nombres",
    "apellidos",
    "apodo",
    "cedula",
    "estado_civil",
    "direccion",
    "telefono",
    "celular",
    "tipo_sangre",
    "nacionalidad",
    "genero",
    "lugar_nacimiento",
    "nivel_academico",
    "email",
    "carnet",
    "forma_pago",
    "banco",
    "cuenta_bancaria",
    "tipo_cuenta",
    "frecuencia_pago",
    "clase_empleado",
    "departamento",
    "cargo",
    "supervisor",
    "sucursal",
    "tipo_empleado",
    "ars",
    "numero_afiliado",
    "numero_ss",
    "pareja_nombre",
    "pareja_telefono",
    "numero_dependientes",
    "contacto_emergencia",
    "celular_emergencia",
    "telefono_emergencia",
    "observaciones",
]


def _employee_payload(record):
    data = {"id_empleado": record.id_empleado}
    for field in TEXT_FIELDS:
        data[field] = getattr(record, field) or ""
    data["salario_base"] = str(record.salario_base) if record.salario_base is not None else ""
    data["estado"] = record.estado or ""
    for field in DATE_FIELDS:
        value = getattr(record, field)
        data[field] = value.strftime("%Y-%m-%d") if value else ""
    data["fecha_ingreso"] = record.fecha_ingreso.strftime("%Y-%m-%d") if record.fecha_ingreso else ""
    data["poncha"] = bool(record.poncha)
    try:
        data["horarios"] = json.loads(record.horarios_json or "{}")
    except json.JSONDecodeError:
        data["horarios"] = {}
    data["estudios"] = [
        {
            "estudio_realizado": item.estudio_realizado or "",
            "desde": item.desde.strftime("%Y-%m-%d") if item.desde else "",
            "hasta": item.hasta.strftime("%Y-%m-%d") if item.hasta else "",
            "lugar_estudio": item.lugar_estudio or "",
            "telefono": item.telefono or "",
            "contacto": item.contacto or "",
        }
        for item in record.estudios.all()
    ]
    data["experiencias_laborales"] = [
        {
            "lugar_trabajo": item.lugar_trabajo or "",
            "desde": item.desde.strftime("%Y-%m-%d") if item.desde else "",
            "hasta": item.hasta.strftime("%Y-%m-%d") if item.hasta else "",
            "cargo": item.cargo or "",
            "supervisor": item.supervisor or "",
            "telefono": item.telefono or "",
        }
        for item in record.experiencias_laborales.all()
    ]
    return data


def _parse_date(value):
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def _parse_decimal(value):
    text = str(value or "").strip().replace(",", "")
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def _clean_estudios(raw_items):
    if not isinstance(raw_items, list):
        return []
    cleaned = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        estudio = str(item.get("estudio_realizado") or "").strip()
        desde = _parse_date(item.get("desde"))
        hasta = _parse_date(item.get("hasta"))
        lugar = str(item.get("lugar_estudio") or "").strip()
        telefono = str(item.get("telefono") or "").strip()
        contacto = str(item.get("contacto") or "").strip()
        if not any([estudio, desde, hasta, lugar, telefono, contacto]):
            continue
        if not estudio:
            raise ValueError("El estudio realizado es obligatorio en cada fila de estudios.")
        cleaned.append(
            {
                "estudio_realizado": estudio,
                "desde": desde,
                "hasta": hasta,
                "lugar_estudio": lugar,
                "telefono": telefono,
                "contacto": contacto,
            }
        )
    return cleaned


def _clean_experiencias(raw_items):
    if not isinstance(raw_items, list):
        return []
    cleaned = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        lugar = str(item.get("lugar_trabajo") or "").strip()
        desde = _parse_date(item.get("desde"))
        hasta = _parse_date(item.get("hasta"))
        cargo = str(item.get("cargo") or "").strip()
        supervisor = str(item.get("supervisor") or "").strip()
        telefono = str(item.get("telefono") or "").strip()
        if not any([lugar, desde, hasta, cargo, supervisor, telefono]):
            continue
        if not lugar:
            raise ValueError("El lugar de trabajo es obligatorio en cada fila de experiencia laboral.")
        cleaned.append(
            {
                "lugar_trabajo": lugar,
                "desde": desde,
                "hasta": hasta,
                "cargo": cargo,
                "supervisor": supervisor,
                "telefono": telefono,
            }
        )
    return cleaned


def _has_any_schedule(horarios):
    if not isinstance(horarios, dict):
        return False
    for item in horarios.values():
        if not isinstance(item, dict):
            continue
        if item.get("activo") or item.get("entrada") or item.get("salida"):
            return True
    return False


def _require_empleados_perm(request, permiso):
    ctx = _base_context(request, page_title="Empleados y Nominas", active_nav="empleados")
    if not ctx:
        return None, redirect("login")
    if not has_perm(ctx["auth_payload"]["usuario_id"], "empleados", permiso):
        return ctx, render_denied(request, active_nav="empleados")
    return ctx, None


def index(request):
    ctx, denied = _require_empleados_perm(request, "ver")
    if denied:
        return denied
    return render(request, "empleados/menu.html", ctx)


def maestro(request):
    ctx, denied = _require_empleados_perm(request, "ver")
    if denied:
        return denied
    ctx["page_title"] = "Maestro de Empleados"
    ctx["departamentos"] = _load_departamento_rows()
    return render(request, "empleados/index.html", ctx)


@require_http_methods(["GET"])
def buscar(request):
    ctx, denied = _require_empleados_perm(request, "ver")
    if denied:
        return JsonResponse({"detail": "No tienes permiso para consultar empleados."}, status=403)

    query = str(request.GET.get("q") or "").strip()
    records = EmpleadoNomina.objects.all()
    if query:
        records = records.filter(
            Q(codigo__icontains=query)
            | Q(nombres__icontains=query)
            | Q(apellidos__icontains=query)
            | Q(cedula__icontains=query)
            | Q(cargo__icontains=query)
        )
    records = records.order_by("codigo")[:100]
    return JsonResponse(
        {
            "results": [
                {
                    "id_empleado": item.id_empleado,
                    "codigo": item.codigo,
                    "nombre": f"{item.nombres} {item.apellidos}".strip(),
                    "cedula": item.cedula,
                    "cargo": item.cargo,
                    "estado": item.estado,
                }
                for item in records
            ]
        }
    )


@require_http_methods(["GET"])
def detalle(request, empleado_id):
    ctx, denied = _require_empleados_perm(request, "ver")
    if denied:
        return JsonResponse({"detail": "No tienes permiso para consultar empleados."}, status=403)
    record = EmpleadoNomina.objects.filter(id_empleado=empleado_id).first()
    if not record:
        return JsonResponse({"detail": "Empleado no encontrado."}, status=404)
    return JsonResponse({"empleado": _employee_payload(record)})


@require_http_methods(["POST"])
def guardar(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "JSON invalido."}, status=400)

    empleado_id = str(payload.get("id_empleado") or "").strip()
    creating = not bool(empleado_id)
    ctx, denied = _require_empleados_perm(request, "crear" if creating else "editar")
    if denied:
        return JsonResponse({"detail": "No tienes permiso para guardar empleados."}, status=403)

    codigo = str(payload.get("codigo") or "").strip()
    if not codigo:
        return JsonResponse({"detail": "El codigo es obligatorio."}, status=400)
    for field, message in REQUIRED_FIELDS:
        if not str(payload.get(field) or "").strip():
            return JsonResponse({"detail": message}, status=400)
    if _parse_date(payload.get("fecha_nacimiento")) is None:
        return JsonResponse({"detail": "La fecha de nacimiento no es valida."}, status=400)
    cuenta_bancaria = str(payload.get("cuenta_bancaria") or "").strip()
    if cuenta_bancaria and not cuenta_bancaria.isdigit():
        return JsonResponse({"detail": "La cuenta bancaria solo acepta valores numericos."}, status=400)
    try:
        estudios = _clean_estudios(payload.get("estudios"))
        experiencias = _clean_experiencias(payload.get("experiencias_laborales"))
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)

    record = None
    if empleado_id:
        record = EmpleadoNomina.objects.filter(id_empleado=empleado_id).first()
        if not record:
            return JsonResponse({"detail": "Empleado no encontrado."}, status=404)
    else:
        record = EmpleadoNomina(estado="Inactivo")

    for field in TEXT_FIELDS:
        value = str(payload.get(field) or "").strip()
        setattr(record, field, value)
    for field in DATE_FIELDS:
        setattr(record, field, _parse_date(payload.get(field)))
    salario_text = str(payload.get("salario_base") or "").strip()
    salario_base = _parse_decimal(salario_text)
    if salario_text and salario_base is None:
        return JsonResponse({"detail": "El salario base debe ser un numero valido."}, status=400)
    if salario_base is not None and salario_base < 0:
        return JsonResponse({"detail": "El salario base no puede ser negativo."}, status=400)
    record.salario_base = salario_base
    record.poncha = bool(payload.get("poncha"))
    horarios = payload.get("horarios") if isinstance(payload.get("horarios"), dict) else {}
    if record.poncha and not _has_any_schedule(horarios):
        return JsonResponse({"detail": "Debe registrar por lo menos un horario si el empleado poncha."}, status=400)
    record.horarios_json = json.dumps(horarios if record.poncha else {}, ensure_ascii=False)

    try:
        with transaction.atomic():
            record.save()
            record.estudios.all().delete()
            EmpleadoEstudio.objects.bulk_create(
                [EmpleadoEstudio(empleado=record, **item) for item in estudios]
            )
            record.experiencias_laborales.all().delete()
            EmpleadoExperienciaLaboral.objects.bulk_create(
                [EmpleadoExperienciaLaboral(empleado=record, **item) for item in experiencias]
            )
    except IntegrityError:
        return JsonResponse({"detail": "Ya existe un empleado con ese codigo."}, status=400)

    return JsonResponse({"ok": True, "empleado": _employee_payload(record)})
