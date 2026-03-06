from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="GrupoArticuloCab",
            fields=[
                ("id_grupo", models.AutoField(db_column="ID_GRUPO", primary_key=True, serialize=False)),
                ("codigo", models.CharField(db_column="CODIGO", max_length=20, unique=True)),
                ("descripcion", models.CharField(db_column="DESCRIPCION", max_length=200)),
                ("activo", models.CharField(db_column="ACTIVO", default="Y", max_length=1)),
                ("fecha_creacion", models.DateTimeField(blank=True, db_column="FECHA_CREACION", null=True)),
                ("fecha_act", models.DateTimeField(blank=True, db_column="FECHA_ACT", null=True)),
                ("id_usuario", models.BigIntegerField(blank=True, db_column="ID_USUARIO", null=True)),
            ],
            options={"db_table": "GRUPO_ARTICULO_CAB"},
        ),
        migrations.CreateModel(
            name="GrupoArticuloDet",
            fields=[
                ("id_det", models.AutoField(db_column="ID_DET", primary_key=True, serialize=False)),
                ("id_articulo", models.CharField(db_column="ID_ARTICULO", max_length=20)),
                ("cantidad", models.DecimalField(db_column="CANTIDAD", decimal_places=4, default=1, max_digits=19)),
                ("orden", models.IntegerField(db_column="ORDEN", default=0)),
                (
                    "id_grupo",
                    models.ForeignKey(
                        db_column="ID_GRUPO",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="detalles",
                        to="prefacturas_app.grupoarticulocab",
                    ),
                ),
            ],
            options={"db_table": "GRUPO_ARTICULO_DET"},
        ),
        migrations.AddIndex(
            model_name="grupoarticulodet",
            index=models.Index(fields=["id_grupo", "orden", "id_det"], name="IX_GRUPO_ART_DET_GRP"),
        ),
    ]
