from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cobros", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CobroCartaEnviada",
            fields=[
                ("id_carta", models.AutoField(db_column="ID_CARTA", primary_key=True, serialize=False)),
                ("id_sn", models.CharField(db_column="ID_SN", max_length=20)),
                ("cliente_nombre", models.CharField(db_column="CLIENTE_NOMBRE", max_length=200)),
                ("telefono", models.CharField(blank=True, db_column="TELEFONO", default="", max_length=50)),
                ("sector", models.CharField(blank=True, db_column="SECTOR", default="", max_length=120)),
                ("tipo", models.CharField(db_column="TIPO", default="AVISO", max_length=30)),
                ("medio_envio", models.CharField(db_column="MEDIO_ENVIO", default="IMPRESA", max_length=30)),
                ("fecha_envio", models.DateField(db_column="FECHA_ENVIO")),
                ("estado", models.CharField(db_column="ESTADO", default="ENVIADA", max_length=20)),
                ("fecha_seguimiento", models.DateField(blank=True, db_column="FECHA_SEGUIMIENTO", null=True)),
                ("nota", models.TextField(db_column="NOTA")),
                ("creado_por_id", models.BigIntegerField(db_column="CREADO_POR_ID")),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True, db_column="FECHA_CREACION")),
                ("fecha_modificacion", models.DateTimeField(auto_now=True, db_column="FECHA_MODIFICACION")),
            ],
            options={
                "db_table": "COBRO_CARTA_ENVIADA",
                "ordering": ["estado", "-fecha_envio", "-fecha_creacion"],
            },
        ),
    ]
