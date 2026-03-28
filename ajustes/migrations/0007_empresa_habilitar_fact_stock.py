from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("ajustes", "0006_usuario_caja_preferencia"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            IF COL_LENGTH('EMPRESA', 'HABILITAR_FACT_STOCK') IS NULL
            BEGIN
                ALTER TABLE EMPRESA
                ADD HABILITAR_FACT_STOCK BIT NOT NULL
                    CONSTRAINT DF_EMPRESA_HABILITAR_FACT_STOCK DEFAULT ((0));
            END
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
