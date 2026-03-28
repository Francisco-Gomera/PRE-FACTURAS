from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ajustes", "0004_drop_usuario_firma_legacy"),
    ]

    operations = [
        migrations.CreateModel(
            name="WhatsAppCloudConfig",
            fields=[
                ("id_config", models.AutoField(db_column="ID_CONFIG", primary_key=True, serialize=False)),
                ("habilitado", models.BooleanField(db_column="HABILITADO", default=False)),
                ("api_version", models.CharField(db_column="API_VERSION", default="v23.0", max_length=20)),
                ("access_token", models.TextField(blank=True, db_column="ACCESS_TOKEN", null=True)),
                ("phone_number_id", models.CharField(blank=True, db_column="PHONE_NUMBER_ID", max_length=80, null=True)),
                ("waba_id", models.CharField(blank=True, db_column="WABA_ID", max_length=80, null=True)),
                ("verify_token", models.CharField(blank=True, db_column="VERIFY_TOKEN", max_length=255, null=True)),
                ("observaciones", models.TextField(blank=True, db_column="OBSERVACIONES", null=True)),
                ("creado_en", models.DateTimeField(auto_now_add=True, db_column="CREADO_EN")),
                ("actualizado_en", models.DateTimeField(auto_now=True, db_column="ACTUALIZADO_EN")),
            ],
            options={
                "db_table": "WHATSAPP_CLOUD_CONFIG",
            },
        ),
    ]
