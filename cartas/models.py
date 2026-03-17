from django.db import models


class CartaPlantilla(models.Model):
    id_plantilla = models.AutoField(db_column="ID_PLANTILLA", primary_key=True)
    nombre = models.CharField(db_column="NOMBRE", max_length=100, unique=True)
    asunto = models.CharField(db_column="ASUNTO", max_length=255)
    cuerpo = models.TextField(db_column="CUERPO")
    activa = models.BooleanField(db_column="ACTIVA", default=True)
    creado_por_id = models.BigIntegerField(db_column="CREADO_POR_ID")
    fecha_creacion = models.DateTimeField(db_column="FECHA_CREACION", auto_now_add=True)
    fecha_modificacion = models.DateTimeField(db_column="FECHA_MODIFICACION", auto_now=True)

    class Meta:
        db_table = "CARTA_PLANTILLA"
