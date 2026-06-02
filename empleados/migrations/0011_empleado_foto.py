from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("empleados", "0010_add_cambio_anterior_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="EmpleadoFoto",
            fields=[
                ("id_foto", models.AutoField(db_column="ID_FOTO", primary_key=True, serialize=False)),
                ("id_empleado", models.BigIntegerField(db_column="ID_EMPLEADO", unique=True)),
                ("foto", models.BinaryField(blank=True, db_column="FOTO", null=True)),
                ("foto_tipo", models.CharField(blank=True, db_column="FOTO_TIPO", max_length=80)),
                ("creado_en", models.DateTimeField(auto_now_add=True, db_column="CREADO_EN")),
                ("actualizado_en", models.DateTimeField(auto_now=True, db_column="ACTUALIZADO_EN")),
            ],
            options={
                "db_table": "EMPLEADO_FOTO",
                "ordering": ["id_empleado"],
            },
        ),
        migrations.AddField(
            model_name="empleadonomina",
            name="id_foto",
            field=models.IntegerField(blank=True, db_column="ID_FOTO", null=True),
        ),
    ]
