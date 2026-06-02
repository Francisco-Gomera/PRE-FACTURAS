import json
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from ajustes.permissions import has_perm
from ajustes.models import FeriadoNacional
from core.views import _base_context, render_denied
from inventario.views import _load_departamento_rows

from .employee_photos import get_employee_photo_data, save_employee_photo
from .models import (
    EmpleadoAccionPersonal,
    EmpleadoEstudio,
    EmpleadoExperienciaLaboral,
    EmpleadoNomina,
    EmpleadoVacacionBalance,
)


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

CONTRACT_ENTRY_MOTIVES = {"CONTRATO", "CONTRATADO"}
ACTION_DETAIL_DEFAULTS = {
    "entrada_motivo": "",
    "entrada_nomina": "",
    "motivo_nombramiento": "",
    "contrato_fecha_inicio": None,
    "contrato_fecha_fin": None,
    "salario_propuesto": None,
    "salida_motivo": "",
    "cambio_motivo": "",
    "cambio_departamento": "",
    "cambio_cargo": "",
    "cambio_nomina": "",
    "cambio_departamento_anterior": "",
    "cambio_cargo_anterior": "",
    "cambio_nomina_anterior": "",
    "cambio_salario_actual": None,
    "cambio_salario_propuesto": None,
    "cambio_porcentaje": None,
    "cambio_diferencia": None,
    "fecha_desde": None,
    "fecha_hasta": None,
    "cantidad_dias": None,
}


def _employee_payload(record):
    data = {"id_empleado": record.id_empleado}
    for field in TEXT_FIELDS:
        data[field] = getattr(record, field) or ""
    data["salario_base"] = str(record.salario_base) if record.salario_base is not None else ""
    data["dias_vacaciones"] = record.dias_vacaciones or 0
    data["vacaciones_disponibles"] = _get_vacation_balance(record).dias_disponibles
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
    data.update(get_employee_photo_data(record.id_empleado))
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
    acciones = [
        _employee_action_payload(item)
        for item in record.acciones_personal.all().order_by("-fecha", "-id_accion")
    ]
    data["acciones_personal"] = acciones
    data["licencias_medicas"] = [
        item
        for item in acciones
        if item.get("tipo_accion") == EmpleadoAccionPersonal.TIPO_CAMBIO
        and str(item.get("motivo") or "").strip().upper() == "LICENCIA MEDICA"
    ]
    data["permisos"] = [
        item
        for item in acciones
        if item.get("tipo_accion") == EmpleadoAccionPersonal.TIPO_CAMBIO
        and str(item.get("motivo") or "").strip().upper() == "PERMISO"
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
    text = str(value or "").replace(",", "").strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return None


def _parse_int(value):
    try:
        return int(str(value or "").strip())
    except (TypeError, ValueError):
        return 0


def _get_vacation_balance(empleado, year=None, for_update=False):
    year = year or timezone.localdate().year
    previous_balance = (
        EmpleadoVacacionBalance.objects.filter(empleado=empleado, ano__lt=year)
        .order_by("-ano")
        .first()
    )
    default_days = (previous_balance.dias_disponibles if previous_balance else 0) + (empleado.dias_vacaciones or 0)
    queryset = EmpleadoVacacionBalance.objects
    if for_update:
        queryset = queryset.select_for_update()
    balance, _ = queryset.get_or_create(
        empleado=empleado,
        ano=year,
        defaults={"dias_disponibles": default_days},
    )
    return balance


def _count_vacation_days(fecha_desde, fecha_hasta):
    if not fecha_desde or not fecha_hasta or fecha_hasta < fecha_desde:
        return 0
    holidays = set(
        FeriadoNacional.objects.filter(
            activo=True,
            no_laborable=True,
            fecha__range=(fecha_desde, fecha_hasta),
        ).values_list("fecha", flat=True)
    )
    total = 0
    cursor = fecha_desde
    while cursor <= fecha_hasta:
        if cursor.weekday() != 6 and cursor not in holidays:
            total += 1
        cursor += timedelta(days=1)
    return total


def _discount_vacation_balance(record):
    if not (
        record.tipo_accion == EmpleadoAccionPersonal.TIPO_CAMBIO
        and record.cambio_motivo == "VACACIONES"
        and record.cantidad_dias
        and record.fecha_desde
    ):
        return
    balance = _get_vacation_balance(record.empleado, record.fecha_desde.year, for_update=True)
    requested_days = int(record.cantidad_dias or 0)
    if requested_days > (balance.dias_disponibles or 0):
        raise ValueError("Los dias solicitados superan los dias disponibles.")
    balance.dias_disponibles = (balance.dias_disponibles or 0) - requested_days
    balance.save(update_fields=["dias_disponibles", "actualizado_en"])


def _return_remaining_vacation_days(record):
    if not (
        record.tipo_accion == EmpleadoAccionPersonal.TIPO_CAMBIO
        and record.cambio_motivo == "VACACIONES"
        and record.fecha_desde
        and record.fecha_hasta
    ):
        return 0
    today = timezone.localdate()
    if today > record.fecha_hasta:
        remaining_days = 0
    else:
        remaining_from = max(today, record.fecha_desde)
        remaining_days = _count_vacation_days(remaining_from, record.fecha_hasta)
    if remaining_days > 0:
        balance = _get_vacation_balance(record.empleado, record.fecha_desde.year, for_update=True)
        balance.dias_disponibles = (balance.dias_disponibles or 0) + remaining_days
        balance.save(update_fields=["dias_disponibles", "actualizado_en"])
    return remaining_days


def _is_active_employee(record):
    return str(record.estado or "").strip().upper() == "ACTIVO"


def _fmt_date(value):
    return value.strftime("%Y-%m-%d") if value else ""


def _fmt_decimal(value):
    return str(value) if value is not None else ""


def _accion_payload(record):
    empleado = record.empleado
    return {
        "id_accion": record.id_accion,
        "id_empleado": empleado.id_empleado,
        "empleado_codigo": empleado.codigo,
        "empleado_nombre": f"{empleado.nombres} {empleado.apellidos}".strip(),
        "fecha": _fmt_date(record.fecha),
        "fecha_efectiva": _fmt_date(record.fecha_efectiva),
        "estatus": record.estatus,
        "tipo_accion": record.tipo_accion,
        "afecta_nomina": bool(record.afecta_nomina),
        "aplicado": bool(record.aplicado),
        "comentario": record.comentario or "",
        "entrada_motivo": record.entrada_motivo or "",
        "entrada_nomina": record.entrada_nomina or "",
        "motivo_nombramiento": record.motivo_nombramiento or "",
        "contrato_fecha_inicio": _fmt_date(record.contrato_fecha_inicio),
        "contrato_fecha_fin": _fmt_date(record.contrato_fecha_fin),
        "salario_propuesto": _fmt_decimal(record.salario_propuesto),
        "salida_motivo": record.salida_motivo or "",
        "cambio_motivo": record.cambio_motivo or "",
        "cambio_departamento": record.cambio_departamento or "",
        "cambio_cargo": record.cambio_cargo or "",
        "cambio_nomina": record.cambio_nomina or "",
        "cambio_salario_actual": _fmt_decimal(record.cambio_salario_actual),
        "cambio_salario_propuesto": _fmt_decimal(record.cambio_salario_propuesto),
        "cambio_porcentaje": _fmt_decimal(record.cambio_porcentaje),
        "cambio_diferencia": _fmt_decimal(record.cambio_diferencia),
        "fecha_desde": _fmt_date(record.fecha_desde),
        "fecha_hasta": _fmt_date(record.fecha_hasta),
        "cantidad_dias": record.cantidad_dias or "",
    }


def _accion_list_payload(record):
    return {
        "id_accion": record.id_accion,
        "fecha": _fmt_date(record.fecha),
        "fecha_efectiva": _fmt_date(record.fecha_efectiva),
        "estatus": record.estatus,
        "tipo_accion": record.tipo_accion,
        "motivo": record.entrada_motivo or record.salida_motivo or record.cambio_motivo or "",
        "empleado": f"{record.empleado.codigo} - {record.empleado.nombres} {record.empleado.apellidos}".strip(),
    }


def _employee_action_payload(record):
    motivo = record.entrada_motivo or record.salida_motivo or record.cambio_motivo or ""
    return {
        "id_accion": record.id_accion,
        "estatus": record.estatus or "",
        "fecha": _fmt_date(record.fecha),
        "fecha_efectiva": _fmt_date(record.fecha_efectiva),
        "tipo_accion": record.tipo_accion or "",
        "motivo": motivo,
        "fecha_desde": _fmt_date(record.fecha_desde),
        "fecha_hasta": _fmt_date(record.fecha_hasta),
    }


def _apply_personal_action(record):
    empleado = record.empleado
    if record.tipo_accion == EmpleadoAccionPersonal.TIPO_ENTRADA:
        empleado.estado = "Activo"
        if record.salario_propuesto is not None:
            empleado.salario_base = record.salario_propuesto
        if record.fecha_efectiva:
            empleado.fecha_ingreso = record.fecha_efectiva
    elif record.tipo_accion == EmpleadoAccionPersonal.TIPO_SALIDA:
        empleado.estado = "Inactivo"
    elif record.tipo_accion == EmpleadoAccionPersonal.TIPO_CAMBIO:
        if record.cambio_departamento:
            empleado.departamento = record.cambio_departamento
        if record.cambio_cargo:
            empleado.cargo = record.cambio_cargo
        if record.cambio_salario_propuesto is not None:
            empleado.salario_base = record.cambio_salario_propuesto
    empleado.save()
    _discount_vacation_balance(record)


def _reverse_change_action(record):
    """Revierte los cambios de una acción de CAMBIO cancelada"""
    empleado = record.empleado
    motivo = str(record.cambio_motivo or "").strip().upper()
    
    if motivo == "AUMENTO DE SALARIO":
        # Revertir aumento de salario
        if record.cambio_salario_actual is not None:
            empleado.salario_base = record.cambio_salario_actual
    
    elif motivo == "TRASLADO":
        # Revertir departamento y cargo
        if record.cambio_departamento_anterior:
            empleado.departamento = record.cambio_departamento_anterior
        if record.cambio_cargo_anterior:
            empleado.cargo = record.cambio_cargo_anterior
    
    elif motivo == "PROMOCION":
        # Revertir salario, departamento y cargo
        if record.cambio_salario_actual is not None:
            empleado.salario_base = record.cambio_salario_actual
        if record.cambio_departamento_anterior:
            empleado.departamento = record.cambio_departamento_anterior
        if record.cambio_cargo_anterior:
            empleado.cargo = record.cambio_cargo_anterior
    
    elif motivo == "CAMBIO DE NOMINA":
        # No se aplica reversión de nómina (el cambio se registra en la acción pero no se modifica el empleado)
        pass
    
    # SUSPENCION y LICENCIA MEDICA: solo cambian estado, no hay cambios a revertir
    # VACACIONES: ya se maneja con _return_remaining_vacation_days
    
    empleado.save()



def _clean_action_payload(payload, empleado):
    tipo_accion = str(payload.get("tipo_accion") or "").strip().upper()
    fecha = _parse_date(payload.get("fecha")) or timezone.localdate()
    fecha_efectiva = _parse_date(payload.get("fecha_efectiva"))
    if not fecha_efectiva:
        raise ValueError("Debe indicar una fecha efectiva.")
    if tipo_accion not in {
        EmpleadoAccionPersonal.TIPO_ENTRADA,
        EmpleadoAccionPersonal.TIPO_CAMBIO,
        EmpleadoAccionPersonal.TIPO_SALIDA,
    }:
        raise ValueError("Debe seleccionar un tipo de accion.")

    empleado_activo = _is_active_employee(empleado)
    if empleado_activo and tipo_accion == EmpleadoAccionPersonal.TIPO_ENTRADA:
        raise ValueError("Un empleado activo solo permite acciones de Cambio o Salida.")
    if not empleado_activo and tipo_accion != EmpleadoAccionPersonal.TIPO_ENTRADA:
        raise ValueError("Un empleado inactivo solo permite acciones de Entrada.")

    today = timezone.localdate()
    estatus = (
        EmpleadoAccionPersonal.ESTATUS_APLICADA
        if fecha_efectiva <= today
        else EmpleadoAccionPersonal.ESTATUS_PENDIENTE
    )
    data = {
        **ACTION_DETAIL_DEFAULTS,
        "fecha": fecha,
        "fecha_efectiva": fecha_efectiva,
        "estatus": estatus,
        "tipo_accion": tipo_accion,
        "afecta_nomina": bool(payload.get("afecta_nomina")),
        "aplicado": estatus == EmpleadoAccionPersonal.ESTATUS_APLICADA,
        "comentario": str(payload.get("comentario") or "").strip(),
    }

    if tipo_accion == EmpleadoAccionPersonal.TIPO_ENTRADA:
        data.update(
            {
                "entrada_motivo": str(payload.get("entrada_motivo") or "").strip(),
                "entrada_nomina": str(payload.get("entrada_nomina") or "").strip(),
                "motivo_nombramiento": str(payload.get("motivo_nombramiento") or "").strip(),
                "contrato_fecha_inicio": _parse_date(payload.get("contrato_fecha_inicio")),
                "contrato_fecha_fin": _parse_date(payload.get("contrato_fecha_fin")),
                "salario_propuesto": _parse_decimal(payload.get("salario_propuesto")),
            }
        )
        if not data["entrada_motivo"]:
            raise ValueError("Debe seleccionar el motivo de entrada.")
        if data["entrada_motivo"] in CONTRACT_ENTRY_MOTIVES and (
            not data["contrato_fecha_inicio"] or not data["contrato_fecha_fin"]
        ):
            raise ValueError("Debe indicar inicio y fin del contrato.")
        if data["contrato_fecha_fin"] and data["contrato_fecha_inicio"] and data["contrato_fecha_fin"] < data["contrato_fecha_inicio"]:
            raise ValueError("La fecha fin del contrato no puede ser menor que la fecha inicio.")
    elif tipo_accion == EmpleadoAccionPersonal.TIPO_SALIDA:
        data["salida_motivo"] = str(payload.get("salida_motivo") or "").strip()
        if not data["salida_motivo"]:
            raise ValueError("Debe seleccionar el motivo de salida.")
    else:
        motivo = str(payload.get("cambio_motivo") or "").strip()
        data["cambio_motivo"] = motivo
        if not motivo:
            raise ValueError("Debe seleccionar el motivo del cambio.")
        if motivo in {"TRASLADO", "PROMOCION"}:
            data["cambio_departamento"] = str(payload.get("cambio_departamento") or "").strip()
            data["cambio_cargo"] = str(payload.get("cambio_cargo") or "").strip()
            data["cambio_nomina"] = str(payload.get("cambio_nomina") or "").strip()
            # Guardar valores anteriores
            data["cambio_departamento_anterior"] = empleado.departamento or ""
            data["cambio_cargo_anterior"] = empleado.cargo or ""
        if motivo in {"AUMENTO DE SALARIO", "PROMOCION"}:
            proposed = _parse_decimal(payload.get("cambio_salario_propuesto"))
            current = empleado.salario_base or Decimal("0")
            if proposed is None:
                raise ValueError("Debe indicar el salario propuesto.")
            data["cambio_salario_actual"] = current
            data["cambio_salario_propuesto"] = proposed
            data["cambio_diferencia"] = proposed - current
            data["cambio_porcentaje"] = ((proposed - current) / current * Decimal("100")) if current else None
        if motivo in {"CAMBIO DE NOMINA", "SUSPENCION", "VACACIONES"}:
            data["cambio_nomina"] = str(payload.get("cambio_nomina") or "").strip()
        if motivo == "SUSPENCION":
            data["fecha_desde"] = _parse_date(payload.get("fecha_desde"))
            data["fecha_hasta"] = _parse_date(payload.get("fecha_hasta"))
            if not data["fecha_desde"] or not data["fecha_hasta"]:
                raise ValueError("Debe indicar las fechas de suspension.")
        if motivo == "VACACIONES":
            data["fecha_desde"] = _parse_date(payload.get("fecha_desde"))
            data["fecha_hasta"] = _parse_date(payload.get("fecha_hasta"))
            if not data["fecha_desde"] or not data["fecha_hasta"]:
                raise ValueError("Debe indicar las fechas de vacaciones.")
            if data["fecha_hasta"] < data["fecha_desde"]:
                raise ValueError("La fecha hasta de vacaciones no puede ser menor que desde.")
            if data["fecha_desde"].year != data["fecha_hasta"].year:
                raise ValueError("Las vacaciones deben pertenecer al mismo ano.")
            data["cantidad_dias"] = _count_vacation_days(data["fecha_desde"], data["fecha_hasta"])
            if data["cantidad_dias"] <= 0:
                raise ValueError("El rango de vacaciones no contiene dias laborables.")
            accion_id = _parse_int(payload.get("id_accion"))
            overlapping = EmpleadoAccionPersonal.objects.filter(
                empleado=empleado,
                tipo_accion=EmpleadoAccionPersonal.TIPO_CAMBIO,
                cambio_motivo="VACACIONES",
                fecha_desde__lte=data["fecha_hasta"],
                fecha_hasta__gte=data["fecha_desde"],
            ).exclude(estatus=EmpleadoAccionPersonal.ESTATUS_CANCELADA)
            if accion_id:
                overlapping = overlapping.exclude(id_accion=accion_id)
            if overlapping.exists():
                raise ValueError("El empleado ya tiene vacaciones asignadas dentro de ese rango de fechas.")
            balance = _get_vacation_balance(empleado, data["fecha_desde"].year)
            if data["cantidad_dias"] > (balance.dias_disponibles or 0):
                raise ValueError("Los dias solicitados superan los dias disponibles.")
        if motivo == "LICENCIA MEDICA":
            data["fecha_desde"] = _parse_date(payload.get("fecha_desde"))
            data["fecha_hasta"] = _parse_date(payload.get("fecha_hasta"))
            data["cantidad_dias"] = _parse_int(payload.get("cantidad_dias"))
            if not data["fecha_desde"] or not data["fecha_hasta"]:
                raise ValueError("Debe indicar las fechas de licencia medica.")
    return data


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


def acciones_personal(request):
    ctx, denied = _require_empleados_perm(request, "ver")
    if denied:
        return denied
    ctx["page_title"] = "Acciones de Personal"
    ctx["departamentos"] = _load_departamento_rows()
    holiday_dates = FeriadoNacional.objects.filter(activo=True, no_laborable=True).values_list("fecha", flat=True)
    ctx["national_holidays_json"] = json.dumps([item.strftime("%Y-%m-%d") for item in holiday_dates])
    return render(request, "empleados/acciones_personal.html", ctx)


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


@require_http_methods(["GET"])
def acciones_personal_listar(request):
    ctx, denied = _require_empleados_perm(request, "ver")
    if denied:
        return JsonResponse({"detail": "No tienes permiso para consultar acciones."}, status=403)
    estatus = str(request.GET.get("estatus") or "").strip().upper()
    query = str(request.GET.get("q") or "").strip()
    records = EmpleadoAccionPersonal.objects.select_related("empleado").all()
    if estatus in {
        EmpleadoAccionPersonal.ESTATUS_PENDIENTE,
        EmpleadoAccionPersonal.ESTATUS_APLICADA,
        EmpleadoAccionPersonal.ESTATUS_CANCELADA,
    }:
        records = records.filter(estatus=estatus)
    if query:
        records = records.filter(
            Q(empleado__codigo__icontains=query)
            | Q(empleado__nombres__icontains=query)
            | Q(empleado__apellidos__icontains=query)
            | Q(tipo_accion__icontains=query)
            | Q(entrada_motivo__icontains=query)
            | Q(salida_motivo__icontains=query)
            | Q(cambio_motivo__icontains=query)
        )
    records = records.order_by("-fecha", "-id_accion")[:200]
    return JsonResponse({"results": [_accion_list_payload(item) for item in records]})


@require_http_methods(["GET"])
def acciones_personal_detalle(request, accion_id):
    ctx, denied = _require_empleados_perm(request, "ver")
    if denied:
        return JsonResponse({"detail": "No tienes permiso para consultar acciones."}, status=403)
    record = EmpleadoAccionPersonal.objects.select_related("empleado").filter(id_accion=accion_id).first()
    if not record:
        return JsonResponse({"detail": "Accion no encontrada."}, status=404)
    return JsonResponse({"accion": _accion_payload(record), "empleado": _employee_payload(record.empleado)})


@require_http_methods(["POST"])
def acciones_personal_guardar(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "JSON invalido."}, status=400)
    accion_id = _parse_int(payload.get("id_accion"))
    ctx, denied = _require_empleados_perm(request, "editar" if accion_id else "crear")
    if denied:
        return JsonResponse({"detail": "No tienes permiso para guardar acciones."}, status=403)
    empleado_id = _parse_int(payload.get("id_empleado"))
    empleado = EmpleadoNomina.objects.filter(id_empleado=empleado_id).first()
    if not empleado:
        return JsonResponse({"detail": "Debe seleccionar un empleado."}, status=400)
    existing_record = None
    was_applied = False
    if accion_id:
        existing_record = EmpleadoAccionPersonal.objects.select_related("empleado").filter(id_accion=accion_id).first()
        if not existing_record:
            return JsonResponse({"detail": "Accion no encontrada."}, status=404)
        if existing_record.empleado_id != empleado.id_empleado:
            return JsonResponse({"detail": "La accion cargada no pertenece al empleado seleccionado."}, status=400)
        if existing_record.aplicado:
            return JsonResponse({"detail": "Una accion aplicada no puede modificarse desde esta pantalla."}, status=400)
        was_applied = bool(existing_record.aplicado)
    try:
        data = _clean_action_payload(payload, empleado)
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)
    try:
        with transaction.atomic():
            if existing_record:
                for field, value in data.items():
                    setattr(existing_record, field, value)
                existing_record.save()
                record = existing_record
            else:
                record = EmpleadoAccionPersonal.objects.create(empleado=empleado, **data)
            if record.aplicado and not was_applied:
                _apply_personal_action(record)
                record.empleado.refresh_from_db()
    except Exception as exc:
        return JsonResponse({"detail": f"No se pudo guardar la accion: {exc}"}, status=500)
    return JsonResponse({"ok": True, "accion": _accion_payload(record), "empleado": _employee_payload(record.empleado)})


@require_http_methods(["POST"])
def acciones_personal_cancelar(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "JSON invalido."}, status=400)
    ctx, denied = _require_empleados_perm(request, "editar")
    if denied:
        return JsonResponse({"detail": "No tienes permiso para cancelar acciones."}, status=403)
    accion_id = _parse_int(payload.get("id_accion"))
    if not accion_id:
        return JsonResponse({"detail": "Debe indicar la accion a cancelar."}, status=400)
    try:
        with transaction.atomic():
            record = (
                EmpleadoAccionPersonal.objects.select_for_update()
                .select_related("empleado")
                .filter(id_accion=accion_id)
                .first()
            )
            if not record:
                return JsonResponse({"detail": "Accion no encontrada."}, status=404)
            if record.estatus == EmpleadoAccionPersonal.ESTATUS_CANCELADA:
                return JsonResponse({"detail": "La accion ya esta cancelada."}, status=400)
            if record.estatus != EmpleadoAccionPersonal.ESTATUS_APLICADA:
                return JsonResponse({"detail": "Solo se pueden cancelar acciones aplicadas desde esta opcion."}, status=400)
            
            returned_days = _return_remaining_vacation_days(record)
            elapsed_days = max(0, int(record.cantidad_dias or 0) - returned_days)
            
            # Revertir cambios si es acción de CAMBIO
            if record.tipo_accion == EmpleadoAccionPersonal.TIPO_CAMBIO:
                _reverse_change_action(record)
            
            record.estatus = EmpleadoAccionPersonal.ESTATUS_CANCELADA
            record.aplicado = False
            record.save(update_fields=["estatus", "aplicado", "actualizado_en"])
            record.empleado.refresh_from_db()
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)
    except Exception as exc:
        return JsonResponse({"detail": f"No se pudo cancelar la accion: {exc}"}, status=500)
    return JsonResponse(
        {
            "ok": True,
            "accion": _accion_payload(record),
            "empleado": _employee_payload(record.empleado),
            "dias_devueltos": returned_days,
            "dias_transcurridos": elapsed_days,
            "tipo_accion": record.tipo_accion,
            "cambio_motivo": record.cambio_motivo,
        }
    )


@require_http_methods(["POST"])
def guardar(request):
    foto_file = None
    if request.content_type and request.content_type.startswith("multipart/form-data"):
        try:
            payload = json.loads(request.POST.get("payload") or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"detail": "JSON invalido."}, status=400)
        foto_file = request.FILES.get("foto")
    else:
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
        dias_vacaciones = int(payload.get("dias_vacaciones") or 0)
    except (TypeError, ValueError):
        return JsonResponse({"detail": "Los dias de vacaciones deben ser un valor numerico."}, status=400)
    if dias_vacaciones < 0 or dias_vacaciones > 120:
        return JsonResponse({"detail": "Los dias de vacaciones deben estar entre 0 y 120."}, status=400)
    try:
        estudios = _clean_estudios(payload.get("estudios"))
        experiencias = _clean_experiencias(payload.get("experiencias_laborales"))
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)

    foto_bytes = None
    foto_tipo = ""
    if foto_file:
        foto_tipo = (foto_file.content_type or "").lower()
        if not foto_tipo.startswith("image/"):
            return JsonResponse({"detail": "La foto debe ser una imagen valida."}, status=400)
        if foto_file.size and foto_file.size > 2 * 1024 * 1024:
            return JsonResponse({"detail": "La foto no puede exceder 2 MB."}, status=400)
        foto_bytes = foto_file.read() or None
        if not foto_bytes:
            return JsonResponse({"detail": "La foto seleccionada esta vacia."}, status=400)

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
    record.dias_vacaciones = dias_vacaciones
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
            if foto_bytes is not None and not save_employee_photo(record.id_empleado, foto_bytes, foto_tipo):
                raise ValueError("No se pudo guardar la foto del empleado.")
    except IntegrityError:
        return JsonResponse({"detail": "Ya existe un empleado con ese codigo."}, status=400)
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)

    return JsonResponse({"ok": True, "empleado": _employee_payload(record)})
