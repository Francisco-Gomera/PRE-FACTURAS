from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("prefacturas_app", "0005_empresa_logo_column"),
    ]

    operations = [
        migrations.RunSQL(
            sql="",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
