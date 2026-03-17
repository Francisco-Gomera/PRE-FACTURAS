from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("prefacturas_app", "0003_usuario_password_column"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            IF COL_LENGTH('USUARIO', 'FIRMA') IS NULL
            BEGIN
                ALTER TABLE USUARIO ADD FIRMA VARBINARY(MAX) NULL;
            END
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
