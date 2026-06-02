from datetime import date

from django.db import migrations, models
import django.db.models.deletion


def seed_current_year_balances(apps, schema_editor):
    EmpleadoNomina = apps.get_model("empleados", "EmpleadoNomina")
    EmpleadoVacacionBalance = apps.get_model("empleados", "EmpleadoVacacionBalance")
    year = date.today().year
    for empleado in EmpleadoNomina.objects.all().only("id_empleado", "dias_vacaciones"):
        EmpleadoVacacionBalance.objects.get_or_create(
            empleado_id=empleado.id_empleado,
            ano=year,
            defaults={"dias_disponibles": empleado.dias_vacaciones or 0},
        )


class Migration(migrations.Migration):

    dependencies = [
        ("empleados", "0008_empleadoaccionpersonal"),
    ]

    operations = [
        migrations.CreateModel(
            name="EmpleadoVacacionBalance",
            fields=[
                ("id_balance", models.AutoField(db_column="ID_BALANCE", primary_key=True, serialize=False)),
                ("ano", models.PositiveSmallIntegerField(db_column="ANO")),
                ("dias_disponibles", models.PositiveSmallIntegerField(db_column="DIAS_DISPONIBLES", default=0)),
                ("creado_en", models.DateTimeField(auto_now_add=True, db_column="CREADO_EN")),
                ("actualizado_en", models.DateTimeField(auto_now=True, db_column="ACTUALIZADO_EN")),
                ("empleado", models.ForeignKey(db_column="ID_EMPLEADO", on_delete=django.db.models.deletion.CASCADE, related_name="balances_vacaciones", to="empleados.empleadonomina")),
            ],
            options={
                "db_table": "EMPLEADO_VACACION_BALANCE",
                "ordering": ["-ano", "empleado_id"],
            },
        ),
        migrations.AddConstraint(
            model_name="empleadovacacionbalance",
            constraint=models.UniqueConstraint(fields=("empleado", "ano"), name="uq_empleado_vacacion_balance"),
        ),
        migrations.RunPython(seed_current_year_balances, migrations.RunPython.noop),
    ]
