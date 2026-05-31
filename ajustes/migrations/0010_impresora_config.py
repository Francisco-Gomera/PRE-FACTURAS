from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ajustes", "0009_formato_impresion_a4_default"),
    ]

    operations = [
        migrations.CreateModel(
            name="ImpresoraConfig",
            fields=[
                (
                    "id_config",
                    models.AutoField(db_column="ID_CONFIG", primary_key=True, serialize=False),
                ),
                (
                    "tipo_documento",
                    models.CharField(
                        choices=[
                            ("cxc", "Cuentas por Cobrar"),
                            ("factura", "Factura"),
                            ("financiamiento", "Financiamiento"),
                        ],
                        db_column="TIPO_DOCUMENTO",
                        max_length=40,
                        unique=True,
                    ),
                ),
                (
                    "nombre_impresora",
                    models.CharField(
                        blank=True,
                        db_column="NOMBRE_IMPRESORA",
                        max_length=255,
                        null=True,
                    ),
                ),
                (
                    "predeterminada",
                    models.BooleanField(db_column="PREDETERMINADA", default=False),
                ),
                (
                    "creado_en",
                    models.DateTimeField(auto_now_add=True, db_column="CREADO_EN"),
                ),
                (
                    "actualizado_en",
                    models.DateTimeField(auto_now=True, db_column="ACTUALIZADO_EN"),
                ),
            ],
            options={
                "db_table": "AJUSTE_IMPRESORA_CONFIG",
                "ordering": ["tipo_documento"],
            },
        ),
    ]
