from django.db import migrations, models


def seed_formatos_impresion(apps, schema_editor):
    FormatoImpresionConfig = apps.get_model("ajustes", "FormatoImpresionConfig")
    for documento in ("recibo_pago", "factura"):
        FormatoImpresionConfig.objects.get_or_create(
            documento=documento,
            defaults={"formato": "80mm"},
        )


class Migration(migrations.Migration):

    dependencies = [
        ("ajustes", "0007_empresa_habilitar_fact_stock"),
    ]

    operations = [
        migrations.CreateModel(
            name="FormatoImpresionConfig",
            fields=[
                ("id_config", models.AutoField(db_column="ID_CONFIG", primary_key=True, serialize=False)),
                (
                    "documento",
                    models.CharField(
                        choices=[("recibo_pago", "Recibo de pago"), ("factura", "Factura")],
                        db_column="DOCUMENTO",
                        max_length=40,
                        unique=True,
                    ),
                ),
                (
                    "formato",
                    models.CharField(
                        choices=[("80mm", "80mm"), ("58mm", "58mm")],
                        db_column="FORMATO",
                        default="80mm",
                        max_length=10,
                    ),
                ),
                ("creado_en", models.DateTimeField(auto_now_add=True, db_column="CREADO_EN")),
                ("actualizado_en", models.DateTimeField(auto_now=True, db_column="ACTUALIZADO_EN")),
            ],
            options={
                "db_table": "AJUSTE_FORMATO_IMPRESION",
                "ordering": ["documento"],
            },
        ),
        migrations.RunPython(seed_formatos_impresion, migrations.RunPython.noop),
    ]
