from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("prefacturas_app", "0004_usuario_firma_column"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            IF COL_LENGTH('EMPRESA', 'LOGO') IS NULL
            BEGIN
                ALTER TABLE EMPRESA ADD LOGO VARBINARY(MAX) NULL;
            END
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
