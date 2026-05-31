from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("empleados", "0003_empleadonomina_datos_nomina_pago"),
    ]

    operations = [
        migrations.CreateModel(
            name="EmpleadoEstudio",
            fields=[
                ("id_estudio", models.AutoField(db_column="ID_ESTUDIO", primary_key=True, serialize=False)),
                ("estudio_realizado", models.CharField(db_column="ESTUDIO_REALIZADO", max_length=160)),
                ("desde", models.DateField(blank=True, db_column="DESDE", null=True)),
                ("hasta", models.DateField(blank=True, db_column="HASTA", null=True)),
                ("lugar_estudio", models.CharField(blank=True, db_column="LUGAR_ESTUDIO", max_length=160)),
                ("telefono", models.CharField(blank=True, db_column="TELEFONO", max_length=30)),
                ("contacto", models.CharField(blank=True, db_column="CONTACTO", max_length=120)),
                (
                    "empleado",
                    models.ForeignKey(
                        db_column="ID_EMPLEADO",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="estudios",
                        to="empleados.empleadonomina",
                    ),
                ),
            ],
            options={
                "db_table": "EMPLEADO_ESTUDIO",
                "ordering": ["desde", "id_estudio"],
            },
        ),
    ]
