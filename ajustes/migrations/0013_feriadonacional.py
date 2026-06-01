from datetime import date

from django.db import migrations, models


FERIADOS_2026 = [
    (date(2026, 1, 1), "Ano Nuevo"),
    (date(2026, 1, 5), "Dia de los Santos Reyes"),
    (date(2026, 1, 21), "Nuestra Senora de la Altagracia"),
    (date(2026, 1, 26), "Natalicio de Juan Pablo Duarte"),
    (date(2026, 2, 27), "Independencia Nacional"),
    (date(2026, 4, 3), "Viernes Santo"),
    (date(2026, 5, 4), "Dia del Trabajo"),
    (date(2026, 6, 4), "Corpus Christi"),
    (date(2026, 8, 16), "Restauracion de la Republica Dominicana"),
    (date(2026, 9, 24), "Nuestra Senora de las Mercedes"),
    (date(2026, 11, 9), "Dia de la Constitucion"),
    (date(2026, 12, 25), "Navidad"),
]


def seed_feriados_2026(apps, schema_editor):
    FeriadoNacional = apps.get_model("ajustes", "FeriadoNacional")
    for fecha, descripcion in FERIADOS_2026:
        FeriadoNacional.objects.get_or_create(
            fecha=fecha,
            defaults={
                "descripcion": descripcion,
                "no_laborable": True,
                "activo": True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("ajustes", "0012_drop_impresora_tipo_documento_unique"),
    ]

    operations = [
        migrations.CreateModel(
            name="FeriadoNacional",
            fields=[
                ("id_feriado", models.AutoField(db_column="ID_FERIADO", primary_key=True, serialize=False)),
                ("fecha", models.DateField(db_column="FECHA", unique=True)),
                ("descripcion", models.CharField(db_column="DESCRIPCION", max_length=160)),
                ("no_laborable", models.BooleanField(db_column="NO_LABORABLE", default=True)),
                ("activo", models.BooleanField(db_column="ACTIVO", default=True)),
                ("creado_en", models.DateTimeField(auto_now_add=True, db_column="CREADO_EN")),
                ("actualizado_en", models.DateTimeField(auto_now=True, db_column="ACTUALIZADO_EN")),
            ],
            options={
                "db_table": "AJUSTE_FERIADO_NACIONAL",
                "ordering": ["fecha"],
            },
        ),
        migrations.RunPython(seed_feriados_2026, migrations.RunPython.noop),
    ]
