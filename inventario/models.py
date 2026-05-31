from django.db import models


class SolicitudExistencia(models.Model):
    id_solicitud = models.AutoField(db_column="ID_SOLICITUD", primary_key=True)
    origen_modulo = models.CharField(db_column="ORIGEN_MODULO", max_length=30, default="FACTURA")
    origen_referencia = models.CharField(db_column="ORIGEN_REFERENCIA", max_length=120, blank=True, null=True)
    cliente_codigo = models.CharField(db_column="CLIENTE_CODIGO", max_length=50, blank=True, null=True)
    cliente_nombre = models.CharField(db_column="CLIENTE_NOMBRE", max_length=180, blank=True, null=True)
    comentario = models.CharField(db_column="COMENTARIO", max_length=255, blank=True, null=True)
    detalle_json = models.TextField(db_column="DETALLE_JSON")
    creada_por_id = models.BigIntegerField(db_column="CREADA_POR_ID", blank=True, null=True)
    creada_por_login = models.CharField(db_column="CREADA_POR_LOGIN", max_length=80, blank=True, null=True)
    creada_por_nombre = models.CharField(db_column="CREADA_POR_NOMBRE", max_length=150, blank=True, null=True)
    atendida = models.BooleanField(db_column="ATENDIDA", default=False)
    atendida_por_id = models.BigIntegerField(db_column="ATENDIDA_POR_ID", blank=True, null=True)
    atendida_por_nombre = models.CharField(db_column="ATENDIDA_POR_NOMBRE", max_length=150, blank=True, null=True)
    atendida_en = models.DateTimeField(db_column="ATENDIDA_EN", blank=True, null=True)
    creado_en = models.DateTimeField(db_column="CREADO_EN", auto_now_add=True)
    actualizado_en = models.DateTimeField(db_column="ACTUALIZADO_EN", auto_now=True)

    class Meta:
        db_table = "INV_SOLICITUD_EXISTENCIA"
        ordering = ["-creado_en", "-id_solicitud"]

    def __str__(self):
        referencia = str(self.origen_referencia or "").strip()
        cliente = str(self.cliente_nombre or "").strip()
        if referencia and cliente:
            return f"{referencia} - {cliente}"
        return referencia or cliente or f"Solicitud {self.id_solicitud}"
