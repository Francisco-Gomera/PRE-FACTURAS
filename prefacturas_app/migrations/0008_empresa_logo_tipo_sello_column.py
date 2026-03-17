from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("prefacturas_app", "0007_cabpedido_detpedido_maestroarticulo_maestrosn_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            IF COL_LENGTH('EMPRESA', 'LOGO_TIPO') IS NULL
            BEGIN
                ALTER TABLE EMPRESA ADD LOGO_TIPO NVARCHAR(100) NULL;
            END
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="""
            IF COL_LENGTH('EMPRESA', 'SELLO') IS NULL
            BEGIN
                ALTER TABLE EMPRESA ADD SELLO VARBINARY(MAX) NULL;
            END
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
