import base64
from django.db import connection, transaction
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from ajustes.permissions import has_perm
from core.views import _base_context, render_denied
from .models import (
    SegModulo,
    SegPermiso,
    SegRol,
    SegRolPermiso,
    SegUsuarioPermiso,
    SegUsuarioRol,
)


def index(request):
    ctx = _base_context(request, page_title="Ajustes", active_nav="ajustes")
    if not ctx:
        return redirect("login")
    if not has_perm(ctx["auth_payload"]["usuario_id"], "ajustes", "ver"):
        return render_denied(request, active_nav="ajustes")
    ctx["submodules"] = {
        "parametros": has_perm(ctx["auth_payload"]["usuario_id"], "ajustes", "ver_parametros"),
        "usuarios": has_perm(ctx["auth_payload"]["usuario_id"], "ajustes", "ver_usuarios"),
        "integraciones": has_perm(ctx["auth_payload"]["usuario_id"], "ajustes", "ver_integraciones"),
    }
    return render(request, "ajustes/index.html", ctx)


def _fetch_usuarios():
    rows = []
    try:
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    SELECT ID_USUARIO, USUARIO, NOMBRE, ESTADO,
                           CASE WHEN DATALENGTH(FIRMA) > 0 THEN 1 ELSE 0 END AS TIENE_FIRMA
                    FROM USUARIO
                    ORDER BY USUARIO
                    """
                )
                for r in cursor.fetchall():
                    rows.append(
                        {
                            "id_usuario": r[0],
                            "usuario": r[1],
                            "nombre": r[2],
                            "estado": r[3],
                            "has_firma": bool(r[4]),
                        }
                    )
            except Exception:
                cursor.execute(
                    """
                    SELECT ID_USUARIO, USUARIO, NOMBRE, ESTADO
                    FROM USUARIO
                    ORDER BY USUARIO
                    """
                )
                for r in cursor.fetchall():
                    rows.append(
                        {
                            "id_usuario": r[0],
                            "usuario": r[1],
                            "nombre": r[2],
                            "estado": r[3],
                            "has_firma": False,
                        }
                    )
    except Exception:
        rows = []
    return rows


def usuarios_view(request):
    ctx = _base_context(request, page_title="Usuarios y permisos", active_nav="ajustes")
    if not ctx:
        return redirect("login")
    if not has_perm(ctx["auth_payload"]["usuario_id"], "ajustes", "ver_usuarios"):
        return render_denied(request, active_nav="ajustes")
    ctx["usuarios"] = _fetch_usuarios()
    ctx["modulos"] = SegModulo.objects.all().order_by("nombre")
    ctx["permisos"] = SegPermiso.objects.select_related("modulo").order_by("modulo__nombre", "nombre")
    admin_role, _ = SegRol.objects.get_or_create(
        codigo="admin",
        defaults={"nombre": "Administrador", "descripcion": "Acceso total"},
    )
    permisos_ids = list(ctx["permisos"].values_list("id", flat=True))
    if permisos_ids:
        existing = set(
            SegRolPermiso.objects.filter(rol=admin_role, permiso_id__in=permisos_ids)
            .values_list("permiso_id", flat=True)
        )
        missing = [
            SegRolPermiso(rol=admin_role, permiso_id=pid)
            for pid in permisos_ids
            if pid not in existing
        ]
        if missing:
            SegRolPermiso.objects.bulk_create(missing)
    ctx["roles"] = SegRol.objects.all().order_by("nombre")
    ctx["roles_permisos"] = SegRolPermiso.objects.select_related("rol", "permiso").all()
    ctx["usuarios_roles"] = SegUsuarioRol.objects.select_related("rol").all()
    ctx["usuarios_permisos"] = SegUsuarioPermiso.objects.select_related("permiso").all()
    palette = [
        ("#1b4f91", "#5b88c7", "#e6effc"),
        ("#0f6d63", "#4ea79b", "#e2f5f1"),
        ("#7a4b12", "#c08b4a", "#faefe0"),
        ("#5b2c83", "#8d62b7", "#efe5fb"),
        ("#1f5a8a", "#5c92be", "#e7f1fb"),
        ("#7b1f3a", "#b4647a", "#f8e6ec"),
        ("#3a6d1f", "#75ad57", "#eaf6e3"),
        ("#6e3b1f", "#a56f52", "#f5e6dc"),
    ]
    module_colors = {}
    for idx, mod in enumerate(ctx["modulos"]):
        dark, mid, light = palette[idx % len(palette)]
        module_colors[mod.id] = {"module": dark, "submodule": mid, "perm": light}

    permisos_by_module = {}
    for perm in ctx["permisos"]:
        codigo = (perm.codigo or "").lower()
        if codigo == "ver":
            level = "module"
        elif codigo.startswith("ver_"):
            level = "submodule"
        else:
            level = "perm"
        color = module_colors.get(perm.modulo_id, {}).get(level, "#f7faff")
        permisos_by_module.setdefault(perm.modulo_id, []).append(
            {
                "id": perm.id,
                "modulo": perm.modulo.nombre if perm.modulo else "",
                "codigo": perm.codigo,
                "nombre": perm.nombre,
                "level": level,
                "color": color,
            }
        )

    level_order = {"module": 0, "submodule": 1, "perm": 2}
    permisos_ui = []
    for mod in ctx["modulos"]:
        items = permisos_by_module.get(mod.id, [])
        items.sort(key=lambda x: (level_order.get(x["level"], 9), x["nombre"], x["codigo"]))
        permisos_ui.extend(items)

    user_perm_map = {}
    for up in ctx["usuarios_permisos"]:
        user_perm_map.setdefault(up.id_usuario, {})[up.permiso_id] = bool(up.permitido)
    ctx["user_perm_map"] = user_perm_map
    ctx["permisos_ui"] = permisos_ui
    return render(request, "ajustes/usuarios.html", ctx)


@require_http_methods(["POST"])
def crear_modulo_view(request):
    codigo = (request.POST.get("codigo") or "").strip()
    nombre = (request.POST.get("nombre") or "").strip()
    descripcion = (request.POST.get("descripcion") or "").strip()
    if codigo and nombre:
        SegModulo.objects.get_or_create(
            codigo=codigo,
            defaults={"nombre": nombre, "descripcion": descripcion or None},
        )
    return redirect("ajustes:usuarios")


@require_http_methods(["POST"])
def crear_permiso_view(request):
    modulo_id = request.POST.get("modulo_id")
    codigo = (request.POST.get("codigo") or "").strip()
    nombre = (request.POST.get("nombre") or "").strip()
    descripcion = (request.POST.get("descripcion") or "").strip()
    if modulo_id and codigo and nombre:
        try:
            modulo = SegModulo.objects.get(id=modulo_id)
            SegPermiso.objects.get_or_create(
                modulo=modulo,
                codigo=codigo,
                defaults={"nombre": nombre, "descripcion": descripcion or None},
            )
        except SegModulo.DoesNotExist:
            pass
    return redirect("ajustes:usuarios")


@require_http_methods(["POST"])
def crear_rol_view(request):
    codigo = (request.POST.get("codigo") or "").strip()
    nombre = (request.POST.get("nombre") or "").strip()
    descripcion = (request.POST.get("descripcion") or "").strip()
    if codigo and nombre:
        SegRol.objects.get_or_create(
            codigo=codigo,
            defaults={"nombre": nombre, "descripcion": descripcion or None},
        )
    return redirect("ajustes:usuarios")


@require_http_methods(["POST"])
def asignar_rol_view(request):
    id_usuario = request.POST.get("id_usuario")
    rol_id = request.POST.get("rol_id")
    if id_usuario and rol_id:
        try:
            SegUsuarioRol.objects.get_or_create(
                id_usuario=int(id_usuario),
                rol_id=int(rol_id),
            )
        except Exception:
            pass
    return redirect("ajustes:usuarios")


@require_http_methods(["POST"])
def asignar_permiso_rol_view(request):
    rol_id = request.POST.get("rol_id")
    permiso_id = request.POST.get("permiso_id")
    if rol_id and permiso_id:
        try:
            SegRolPermiso.objects.get_or_create(
                rol_id=int(rol_id),
                permiso_id=int(permiso_id),
            )
        except Exception:
            pass
    return redirect("ajustes:usuarios")


@require_http_methods(["POST"])
def asignar_permiso_usuario_view(request):
    id_usuario = request.POST.get("id_usuario")
    permiso_id = request.POST.get("permiso_id")
    permitido = request.POST.get("permitido") == "1"
    if id_usuario and permiso_id:
        with transaction.atomic():
            SegUsuarioPermiso.objects.update_or_create(
                id_usuario=int(id_usuario),
                permiso_id=int(permiso_id),
                defaults={"permitido": permitido},
            )
    return redirect("ajustes:usuarios")


@require_http_methods(["POST"])
def guardar_permisos_usuario_view(request):
    id_usuario = request.POST.get("id_usuario")
    if not id_usuario:
        return redirect("ajustes:usuarios")
    try:
        id_usuario = int(id_usuario)
    except (TypeError, ValueError):
        return redirect("ajustes:usuarios")

    selected_ids = set()
    for raw_id in request.POST.getlist("perm_ids"):
        try:
            selected_ids.add(int(raw_id))
        except (TypeError, ValueError):
            continue

    permisos_ids = list(SegPermiso.objects.values_list("id", flat=True))
    existing = {
        up.permiso_id: up
        for up in SegUsuarioPermiso.objects.filter(id_usuario=id_usuario)
    }
    to_update = []
    to_create = []
    for perm_id in permisos_ids:
        permitido = perm_id in selected_ids
        if perm_id in existing:
            up = existing[perm_id]
            if up.permitido != permitido:
                up.permitido = permitido
                to_update.append(up)
        else:
            to_create.append(
                SegUsuarioPermiso(
                    id_usuario=id_usuario,
                    permiso_id=perm_id,
                    permitido=permitido,
                )
            )
    with transaction.atomic():
        if to_update:
            SegUsuarioPermiso.objects.bulk_update(to_update, ["permitido"])
        if to_create:
            SegUsuarioPermiso.objects.bulk_create(to_create)
    return redirect("ajustes:usuarios")


@require_http_methods(["POST"])
def guardar_firma_usuario_view(request):
    ctx = _base_context(request, page_title="Usuarios y permisos", active_nav="ajustes")
    if not ctx:
        return redirect("login")
    if not has_perm(ctx["auth_payload"]["usuario_id"], "ajustes", "ver_usuarios"):
        return render_denied(request, active_nav="ajustes")
    id_usuario = request.POST.get("id_usuario")
    firma_file = request.FILES.get("firma_png")
    if not id_usuario or not firma_file:
        return redirect("ajustes:usuarios")
    try:
        id_usuario = int(id_usuario)
    except (TypeError, ValueError):
        return redirect("ajustes:usuarios")

    if (firma_file.content_type or "").lower() not in ("image/png", "image/x-png"):
        return redirect("ajustes:usuarios")
    if firma_file.size and firma_file.size > 2 * 1024 * 1024:
        return redirect("ajustes:usuarios")
    firma_bytes = firma_file.read()
    if not firma_bytes:
        return redirect("ajustes:usuarios")

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE USUARIO SET FIRMA = %s WHERE ID_USUARIO = %s",
                [firma_bytes, id_usuario],
            )
    except Exception:
        return redirect("ajustes:usuarios")
    return redirect("ajustes:usuarios")


def parametros_view(request):
    ctx = _base_context(request, page_title="Parametros", active_nav="ajustes")
    if not ctx:
        return redirect("login")
    if not has_perm(ctx["auth_payload"]["usuario_id"], "ajustes", "ver_parametros"):
        return render_denied(request, active_nav="ajustes")
    empresa = {
        "id_empresa": "",
        "nombre": "",
        "direccion": "",
        "tel1": "",
        "tel2": "",
        "email": "",
        "rnc": "",
        "logo_b64": "",
        "logo_tipo": "",
        "sello_b64": "",
    }
    try:
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    SELECT TOP 1 ID_EMPRESA, NOMBRE, DIR_EMP, TEL1, TEL2, EMAIL, RNC_CED, LOGO, LOGO_TIPO, SELLO
                    FROM EMPRESA
                    """
                )
                row = cursor.fetchone()
                if row:
                    empresa["id_empresa"] = row[0]
                    empresa["nombre"] = row[1] or ""
                    empresa["direccion"] = row[2] or ""
                    empresa["tel1"] = row[3] or ""
                    empresa["tel2"] = row[4] or ""
                    empresa["email"] = row[5] or ""
                    empresa["rnc"] = row[6] or ""
                    if row[7]:
                        empresa["logo_b64"] = base64.b64encode(row[7]).decode("ascii")
                    empresa["logo_tipo"] = row[8] or ""
                    if row[9]:
                        empresa["sello_b64"] = base64.b64encode(row[9]).decode("ascii")
            except Exception:
                cursor.execute(
                    """
                    SELECT TOP 1 ID_EMPRESA, NOMBRE, DIR_EMP, TEL1, TEL2, EMAIL, RNC_CED
                    FROM EMPRESA
                    """
                )
                row = cursor.fetchone()
                if row:
                    empresa["id_empresa"] = row[0]
                    empresa["nombre"] = row[1] or ""
                    empresa["direccion"] = row[2] or ""
                    empresa["tel1"] = row[3] or ""
                    empresa["tel2"] = row[4] or ""
                    empresa["email"] = row[5] or ""
                    empresa["rnc"] = row[6] or ""
    except Exception:
        pass
    ctx["empresa_data"] = empresa
    return render(request, "ajustes/parametros.html", ctx)


@require_http_methods(["POST"])
def guardar_parametros_view(request):
    ctx = _base_context(request, page_title="Parametros", active_nav="ajustes")
    if not ctx:
        return redirect("login")
    if not has_perm(ctx["auth_payload"]["usuario_id"], "ajustes", "ver_parametros"):
        return render_denied(request, active_nav="ajustes")

    id_empresa = (request.POST.get("id_empresa") or "").strip()
    nombre = (request.POST.get("nombre") or "").strip()
    direccion = (request.POST.get("direccion") or "").strip()
    tel1 = (request.POST.get("tel1") or "").strip()
    tel2 = (request.POST.get("tel2") or "").strip()
    email = (request.POST.get("email") or "").strip()
    rnc = (request.POST.get("rnc") or "").strip()
    logo_file = request.FILES.get("logo_img")
    sello_file = request.FILES.get("sello_png")

    if not id_empresa:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT TOP 1 ID_EMPRESA FROM EMPRESA")
                row = cursor.fetchone()
                if row:
                    id_empresa = row[0]
        except Exception:
            id_empresa = ""

    if not id_empresa:
        return redirect("ajustes:parametros")

    logo_bytes = None
    logo_mime = ""
    if logo_file:
        logo_mime = (logo_file.content_type or "").lower()
        if not logo_mime.startswith("image/"):
            return redirect("ajustes:parametros")
        if logo_file.size and logo_file.size > 2 * 1024 * 1024:
            return redirect("ajustes:parametros")
        logo_bytes = logo_file.read() or None
    sello_bytes = None
    if sello_file:
        sello_mime = (sello_file.content_type or "").lower()
        if sello_mime not in ("image/png", "image/x-png"):
            return redirect("ajustes:parametros")
        if sello_file.size and sello_file.size > 2 * 1024 * 1024:
            return redirect("ajustes:parametros")
        sello_bytes = sello_file.read() or None

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE EMPRESA
                SET NOMBRE = %s,
                    DIR_EMP = %s,
                    TEL1 = %s,
                    TEL2 = %s,
                    EMAIL = %s,
                    RNC_CED = %s
                WHERE ID_EMPRESA = %s
                """,
                [nombre, direccion, tel1, tel2, email, rnc, id_empresa],
            )
            if logo_bytes is not None:
                try:
                    cursor.execute(
                        "UPDATE EMPRESA SET LOGO = %s WHERE ID_EMPRESA = %s",
                        [logo_bytes, id_empresa],
                    )
                    cursor.execute(
                        "UPDATE EMPRESA SET LOGO_TIPO = %s WHERE ID_EMPRESA = %s",
                        [logo_mime, id_empresa],
                    )
                except Exception:
                    pass
            if sello_bytes is not None:
                try:
                    cursor.execute(
                        "UPDATE EMPRESA SET SELLO = %s WHERE ID_EMPRESA = %s",
                        [sello_bytes, id_empresa],
                    )
                except Exception:
                    pass
    except Exception:
        return redirect("ajustes:parametros")

    return redirect("ajustes:parametros")
