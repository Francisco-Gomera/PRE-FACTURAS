from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SolicitudExistencia",
            fields=[
                ("id_solicitud", models.AutoField(db_column="ID_SOLICITUD", primary_key=True, serialize=False)),
                ("origen_modulo", models.CharField(db_column="ORIGEN_MODULO", default="FACTURA", max_length=30)),
                ("origen_referencia", models.CharField(blank=True, db_column="ORIGEN_REFERENCIA", max_length=120, null=True)),
                ("cliente_codigo", models.CharField(blank=True, db_column="CLIENTE_CODIGO", max_length=50, null=True)),
                ("cliente_nombre", models.CharField(blank=True, db_column="CLIENTE_NOMBRE", max_length=180, null=True)),
                ("comentario", models.CharField(blank=True, db_column="COMENTARIO", max_length=255, null=True)),
                ("detalle_json", models.TextField(db_column="DETALLE_JSON")),
                ("creada_por_id", models.BigIntegerField(blank=True, db_column="CREADA_POR_ID", null=True)),
                ("creada_por_login", models.CharField(blank=True, db_column="CREADA_POR_LOGIN", max_length=80, null=True)),
                ("creada_por_nombre", models.CharField(blank=True, db_column="CREADA_POR_NOMBRE", max_length=150, null=True)),
                ("atendida", models.BooleanField(db_column="ATENDIDA", default=False)),
                ("atendida_por_id", models.BigIntegerField(blank=True, db_column="ATENDIDA_POR_ID", null=True)),
                ("atendida_por_nombre", models.CharField(blank=True, db_column="ATENDIDA_POR_NOMBRE", max_length=150, null=True)),
                ("atendida_en", models.DateTimeField(blank=True, db_column="ATENDIDA_EN", null=True)),
                ("creado_en", models.DateTimeField(auto_now_add=True, db_column="CREADO_EN")),
                ("actualizado_en", models.DateTimeField(auto_now=True, db_column="ACTUALIZADO_EN")),
            ],
            options={
                "db_table": "INV_SOLICITUD_EXISTENCIA",
                "ordering": ["-creado_en", "-id_solicitud"],
            },
        ),
    ]
