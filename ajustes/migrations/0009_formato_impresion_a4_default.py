from django.db import migrations, models


def restore_a4_default(apps, schema_editor):
    FormatoImpresionConfig = apps.get_model("ajustes", "FormatoImpresionConfig")
    FormatoImpresionConfig.objects.filter(formato="80mm").update(formato="a4")


class Migration(migrations.Migration):

    dependencies = [
        ("ajustes", "0008_formato_impresion_config"),
    ]

    operations = [
        migrations.AlterField(
            model_name="formatoimpresionconfig",
            name="formato",
            field=models.CharField(
                choices=[("a4", "A4"), ("80mm", "80mm"), ("58mm", "58mm")],
                db_column="FORMATO",
                default="a4",
                max_length=10,
            ),
        ),
        migrations.RunPython(restore_a4_default, migrations.RunPython.noop),
    ]
