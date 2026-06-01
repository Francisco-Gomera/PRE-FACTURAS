from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("empleados", "0007_empleadonomina_dias_vacaciones"),
    ]

    operations = [
        migrations.CreateModel(
            name="EmpleadoAccionPersonal",
            fields=[
                ("id_accion", models.AutoField(db_column="ID_ACCION", primary_key=True, serialize=False)),
                ("fecha", models.DateField(db_column="FECHA")),
                ("fecha_efectiva", models.DateField(db_column="FECHA_EFECTIVA")),
                ("estatus", models.CharField(db_column="ESTATUS", default="PENDIENTE", max_length=20)),
                ("tipo_accion", models.CharField(db_column="TIPO_ACCION", max_length=20)),
                ("afecta_nomina", models.BooleanField(db_column="AFECTA_NOMINA", default=False)),
                ("aplicado", models.BooleanField(db_column="APLICADO", default=False)),
                ("comentario", models.TextField(db_column="COMENTARIO", blank=True)),
                ("entrada_motivo", models.CharField(db_column="ENTRADA_MOTIVO", blank=True, max_length=80)),
                ("entrada_nomina", models.CharField(db_column="ENTRADA_NOMINA", blank=True, max_length=80)),
                ("motivo_nombramiento", models.CharField(db_column="MOTIVO_NOMBRAMIENTO", blank=True, max_length=80)),
                ("contrato_fecha_inicio", models.DateField(blank=True, db_column="CONTRATO_FECHA_INICIO", null=True)),
                ("contrato_fecha_fin", models.DateField(blank=True, db_column="CONTRATO_FECHA_FIN", null=True)),
                ("salario_propuesto", models.DecimalField(blank=True, db_column="SALARIO_PROPUESTO", decimal_places=2, max_digits=12, null=True)),
                ("salida_motivo", models.CharField(db_column="SALIDA_MOTIVO", blank=True, max_length=80)),
                ("cambio_motivo", models.CharField(db_column="CAMBIO_MOTIVO", blank=True, max_length=80)),
                ("cambio_departamento", models.CharField(db_column="CAMBIO_DEPARTAMENTO", blank=True, max_length=100)),
                ("cambio_cargo", models.CharField(db_column="CAMBIO_CARGO", blank=True, max_length=80)),
                ("cambio_nomina", models.CharField(db_column="CAMBIO_NOMINA", blank=True, max_length=80)),
                ("cambio_salario_actual", models.DecimalField(blank=True, db_column="CAMBIO_SALARIO_ACTUAL", decimal_places=2, max_digits=12, null=True)),
                ("cambio_salario_propuesto", models.DecimalField(blank=True, db_column="CAMBIO_SALARIO_PROPUESTO", decimal_places=2, max_digits=12, null=True)),
                ("cambio_porcentaje", models.DecimalField(blank=True, db_column="CAMBIO_PORCENTAJE", decimal_places=2, max_digits=8, null=True)),
                ("cambio_diferencia", models.DecimalField(blank=True, db_column="CAMBIO_DIFERENCIA", decimal_places=2, max_digits=12, null=True)),
                ("fecha_desde", models.DateField(blank=True, db_column="FECHA_DESDE", null=True)),
                ("fecha_hasta", models.DateField(blank=True, db_column="FECHA_HASTA", null=True)),
                ("cantidad_dias", models.PositiveSmallIntegerField(blank=True, db_column="CANTIDAD_DIAS", null=True)),
                ("creado_en", models.DateTimeField(auto_now_add=True, db_column="CREADO_EN")),
                ("actualizado_en", models.DateTimeField(auto_now=True, db_column="ACTUALIZADO_EN")),
                ("empleado", models.ForeignKey(db_column="ID_EMPLEADO", on_delete=django.db.models.deletion.PROTECT, related_name="acciones_personal", to="empleados.empleadonomina")),
            ],
            options={
                "db_table": "EMPLEADO_ACCION_PERSONAL",
                "ordering": ["-fecha", "-id_accion"],
            },
        ),
    ]
