from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("empleados", "0004_empleadoestudio"),
    ]

    operations = [
        migrations.CreateModel(
            name="EmpleadoExperienciaLaboral",
            fields=[
                ("id_experiencia", models.AutoField(db_column="ID_EXPERIENCIA", primary_key=True, serialize=False)),
                ("lugar_trabajo", models.CharField(db_column="LUGAR_TRABAJO", max_length=160)),
                ("desde", models.DateField(blank=True, db_column="DESDE", null=True)),
                ("hasta", models.DateField(blank=True, db_column="HASTA", null=True)),
                ("cargo", models.CharField(blank=True, db_column="CARGO", max_length=120)),
                ("supervisor", models.CharField(blank=True, db_column="SUPERVISOR", max_length=120)),
                ("telefono", models.CharField(blank=True, db_column="TELEFONO", max_length=30)),
                (
                    "empleado",
                    models.ForeignKey(
                        db_column="ID_EMPLEADO",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="experiencias_laborales",
                        to="empleados.empleadonomina",
                    ),
                ),
            ],
            options={
                "db_table": "EMPLEADO_EXPERIENCIA_LABORAL",
                "ordering": ["desde", "id_experiencia"],
            },
        ),
    ]
