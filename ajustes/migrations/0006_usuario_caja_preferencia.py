from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ajustes", "0005_whatsapp_cloud_config"),
    ]

    operations = [
        migrations.CreateModel(
            name="UsuarioCajaPreferencia",
            fields=[
                ("id_preferencia", models.AutoField(db_column="ID_PREFERENCIA", primary_key=True, serialize=False)),
                ("id_usuario", models.BigIntegerField(db_column="ID_USUARIO", unique=True)),
                ("metodo_pago_default", models.CharField(blank=True, db_column="METODO_PAGO_DEFAULT", max_length=20, null=True)),
                ("creado_en", models.DateTimeField(auto_now_add=True, db_column="CREADO_EN")),
                ("actualizado_en", models.DateTimeField(auto_now=True, db_column="ACTUALIZADO_EN")),
            ],
            options={
                "db_table": "CAJA_USUARIO_PREFERENCIA",
                "ordering": ["id_usuario"],
            },
        ),
    ]
