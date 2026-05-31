from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ajustes", "0010_impresora_config"),
    ]

    operations = [
        migrations.AlterField(
            model_name="impresoraconfig",
            name="tipo_documento",
            field=models.CharField(
                choices=[
                    ("cxc", "Cuentas por Cobrar"),
                    ("factura", "Factura"),
                    ("financiamiento", "Financiamiento"),
                ],
                db_column="TIPO_DOCUMENTO",
                max_length=40,
            ),
        ),
        migrations.AddField(
            model_name="impresoraconfig",
            name="nombre_terminal",
            field=models.CharField(db_column="NOMBRE_TERMINAL", default="default", max_length=100),
        ),
        migrations.AlterModelOptions(
            name="impresoraconfig",
            options={"ordering": ["nombre_terminal", "tipo_documento"]},
        ),
        migrations.AddConstraint(
            model_name="impresoraconfig",
            constraint=models.UniqueConstraint(
                fields=("nombre_terminal", "tipo_documento"),
                name="uq_impresora_terminal_tipo",
            ),
        ),
    ]
