from django.db import models


class SegModulo(models.Model):
    codigo = models.CharField(db_column="CODIGO", max_length=50, unique=True)
    nombre = models.CharField(db_column="NOMBRE", max_length=120)
    descripcion = models.CharField(db_column="DESCRIPCION", max_length=255, blank=True, null=True)
    activo = models.BooleanField(db_column="ACTIVO", default=True)
    creado_en = models.DateTimeField(db_column="CREADO_EN", auto_now_add=True)
    actualizado_en = models.DateTimeField(db_column="ACTUALIZADO_EN", auto_now=True)

    class Meta:
        db_table = "SEG_MODULO"


class SegPermiso(models.Model):
    modulo = models.ForeignKey(
        SegModulo,
        db_column="ID_MODULO",
        on_delete=models.PROTECT,
        related_name="permisos",
    )
    codigo = models.CharField(db_column="CODIGO", max_length=80)
    nombre = models.CharField(db_column="NOMBRE", max_length=150)
    descripcion = models.CharField(db_column="DESCRIPCION", max_length=255, blank=True, null=True)
    activo = models.BooleanField(db_column="ACTIVO", default=True)
    creado_en = models.DateTimeField(db_column="CREADO_EN", auto_now_add=True)
    actualizado_en = models.DateTimeField(db_column="ACTUALIZADO_EN", auto_now=True)

    class Meta:
        db_table = "SEG_PERMISO"
        constraints = [
            models.UniqueConstraint(fields=["modulo", "codigo"], name="uq_permiso_modulo_codigo"),
        ]


class SegRol(models.Model):
    codigo = models.CharField(db_column="CODIGO", max_length=50, unique=True)
    nombre = models.CharField(db_column="NOMBRE", max_length=120)
    descripcion = models.CharField(db_column="DESCRIPCION", max_length=255, blank=True, null=True)
    activo = models.BooleanField(db_column="ACTIVO", default=True)
    creado_en = models.DateTimeField(db_column="CREADO_EN", auto_now_add=True)
    actualizado_en = models.DateTimeField(db_column="ACTUALIZADO_EN", auto_now=True)

    class Meta:
        db_table = "SEG_ROL"


class SegRolPermiso(models.Model):
    rol = models.ForeignKey(
        SegRol,
        db_column="ID_ROL",
        on_delete=models.CASCADE,
        related_name="rol_permisos",
    )
    permiso = models.ForeignKey(
        SegPermiso,
        db_column="ID_PERMISO",
        on_delete=models.CASCADE,
        related_name="permiso_roles",
    )

    class Meta:
        db_table = "SEG_ROL_PERMISO"
        constraints = [
            models.UniqueConstraint(fields=["rol", "permiso"], name="uq_rol_permiso"),
        ]


class SegUsuarioRol(models.Model):
    id_usuario = models.BigIntegerField(db_column="ID_USUARIO")
    rol = models.ForeignKey(
        SegRol,
        db_column="ID_ROL",
        on_delete=models.CASCADE,
        related_name="usuario_roles",
    )

    class Meta:
        db_table = "SEG_USUARIO_ROL"
        constraints = [
            models.UniqueConstraint(fields=["id_usuario", "rol"], name="uq_usuario_rol"),
        ]


class SegUsuarioPermiso(models.Model):
    id_usuario = models.BigIntegerField(db_column="ID_USUARIO")
    permiso = models.ForeignKey(
        SegPermiso,
        db_column="ID_PERMISO",
        on_delete=models.CASCADE,
        related_name="usuario_permisos",
    )
    permitido = models.BooleanField(db_column="PERMITIDO", default=True)

    class Meta:
        db_table = "SEG_USUARIO_PERMISO"
        constraints = [
            models.UniqueConstraint(fields=["id_usuario", "permiso"], name="uq_usuario_permiso"),
        ]

# Create your models here.
