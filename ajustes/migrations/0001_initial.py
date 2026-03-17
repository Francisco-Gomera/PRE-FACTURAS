from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SegModulo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("codigo", models.CharField(db_column="CODIGO", max_length=50, unique=True)),
                ("nombre", models.CharField(db_column="NOMBRE", max_length=120)),
                ("descripcion", models.CharField(blank=True, db_column="DESCRIPCION", max_length=255, null=True)),
                ("activo", models.BooleanField(db_column="ACTIVO", default=True)),
                ("creado_en", models.DateTimeField(auto_now_add=True, db_column="CREADO_EN")),
                ("actualizado_en", models.DateTimeField(auto_now=True, db_column="ACTUALIZADO_EN")),
            ],
            options={"db_table": "SEG_MODULO"},
        ),
        migrations.CreateModel(
            name="SegPermiso",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("codigo", models.CharField(db_column="CODIGO", max_length=80)),
                ("nombre", models.CharField(db_column="NOMBRE", max_length=150)),
                ("descripcion", models.CharField(blank=True, db_column="DESCRIPCION", max_length=255, null=True)),
                ("activo", models.BooleanField(db_column="ACTIVO", default=True)),
                ("creado_en", models.DateTimeField(auto_now_add=True, db_column="CREADO_EN")),
                ("actualizado_en", models.DateTimeField(auto_now=True, db_column="ACTUALIZADO_EN")),
                (
                    "modulo",
                    models.ForeignKey(
                        db_column="ID_MODULO",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="permisos",
                        to="ajustes.segmodulo",
                    ),
                ),
            ],
            options={"db_table": "SEG_PERMISO"},
        ),
        migrations.CreateModel(
            name="SegRol",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("codigo", models.CharField(db_column="CODIGO", max_length=50, unique=True)),
                ("nombre", models.CharField(db_column="NOMBRE", max_length=120)),
                ("descripcion", models.CharField(blank=True, db_column="DESCRIPCION", max_length=255, null=True)),
                ("activo", models.BooleanField(db_column="ACTIVO", default=True)),
                ("creado_en", models.DateTimeField(auto_now_add=True, db_column="CREADO_EN")),
                ("actualizado_en", models.DateTimeField(auto_now=True, db_column="ACTUALIZADO_EN")),
            ],
            options={"db_table": "SEG_ROL"},
        ),
        migrations.CreateModel(
            name="SegRolPermiso",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "rol",
                    models.ForeignKey(
                        db_column="ID_ROL",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rol_permisos",
                        to="ajustes.segrol",
                    ),
                ),
                (
                    "permiso",
                    models.ForeignKey(
                        db_column="ID_PERMISO",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="permiso_roles",
                        to="ajustes.segpermiso",
                    ),
                ),
            ],
            options={"db_table": "SEG_ROL_PERMISO"},
        ),
        migrations.CreateModel(
            name="SegUsuarioRol",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("id_usuario", models.BigIntegerField(db_column="ID_USUARIO")),
                (
                    "rol",
                    models.ForeignKey(
                        db_column="ID_ROL",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="usuario_roles",
                        to="ajustes.segrol",
                    ),
                ),
            ],
            options={"db_table": "SEG_USUARIO_ROL"},
        ),
        migrations.CreateModel(
            name="SegUsuarioPermiso",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("id_usuario", models.BigIntegerField(db_column="ID_USUARIO")),
                ("permitido", models.BooleanField(db_column="PERMITIDO", default=True)),
                (
                    "permiso",
                    models.ForeignKey(
                        db_column="ID_PERMISO",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="usuario_permisos",
                        to="ajustes.segpermiso",
                    ),
                ),
            ],
            options={"db_table": "SEG_USUARIO_PERMISO"},
        ),
        migrations.AddConstraint(
            model_name="segpermiso",
            constraint=models.UniqueConstraint(fields=("modulo", "codigo"), name="uq_permiso_modulo_codigo"),
        ),
        migrations.AddConstraint(
            model_name="segrolpermiso",
            constraint=models.UniqueConstraint(fields=("rol", "permiso"), name="uq_rol_permiso"),
        ),
        migrations.AddConstraint(
            model_name="segusuariorol",
            constraint=models.UniqueConstraint(fields=("id_usuario", "rol"), name="uq_usuario_rol"),
        ),
        migrations.AddConstraint(
            model_name="segusuariopermiso",
            constraint=models.UniqueConstraint(fields=("id_usuario", "permiso"), name="uq_usuario_permiso"),
        ),
    ]
