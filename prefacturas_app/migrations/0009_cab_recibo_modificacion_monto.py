from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("prefacturas_app", "0008_empresa_logo_tipo_sello_column"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            IF COL_LENGTH('CAB_RECIBO_INGRESO', 'USUARIO_MODIF_MONTO') IS NULL
            BEGIN
                ALTER TABLE CAB_RECIBO_INGRESO ADD USUARIO_MODIF_MONTO NVARCHAR(120) NULL;
            END
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="""
            IF COL_LENGTH('CAB_RECIBO_INGRESO', 'FECHA_MODIF_MONTO') IS NULL
            BEGIN
                ALTER TABLE CAB_RECIBO_INGRESO ADD FECHA_MODIF_MONTO DATETIME2 NULL;
            END
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
