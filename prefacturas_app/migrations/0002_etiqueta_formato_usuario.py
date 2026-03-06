from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("prefacturas_app", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="EtiquetaFormatoUsuario",
            fields=[
                ("id_config", models.AutoField(db_column="ID_CONFIG", primary_key=True, serialize=False)),
                ("id_usuario", models.BigIntegerField(db_column="ID_USUARIO", unique=True)),
                ("formato_json", models.TextField(db_column="FORMATO_JSON", default="{}")),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True, db_column="FECHA_CREACION")),
                ("fecha_act", models.DateTimeField(auto_now=True, db_column="FECHA_ACT")),
            ],
            options={
                "db_table": "ETIQUETA_FORMATO_USUARIO",
            },
        ),
    ]
