from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("prefacturas_app", "0002_etiqueta_formato_usuario"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            IF COL_LENGTH('USUARIO', 'PASSWORD') IS NULL
            BEGIN
                ALTER TABLE USUARIO ADD [PASSWORD] NVARCHAR(255) NULL;
            END
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
