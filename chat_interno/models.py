from django.db import models


class ChatSala(models.Model):
    id_sala = models.AutoField(db_column="ID_SALA", primary_key=True)
    tipo = models.CharField(db_column="TIPO", max_length=10, default="DIRECTO")
    nombre = models.CharField(db_column="NOMBRE", max_length=120, blank=True, null=True)
    direct_key = models.CharField(db_column="DIRECT_KEY", max_length=80, unique=True, blank=True, null=True)
    creada_por = models.BigIntegerField(db_column="CREADA_POR", blank=True, null=True)
    activa = models.BooleanField(db_column="ACTIVA", default=True)
    creada_en = models.DateTimeField(db_column="CREADA_EN", auto_now_add=True)
    actualizada_en = models.DateTimeField(db_column="ACTUALIZADA_EN", auto_now=True)

    class Meta:
        db_table = "CHAT_SALA"
        ordering = ["-actualizada_en", "-id_sala"]


class ChatSalaMiembro(models.Model):
    id_miembro = models.AutoField(db_column="ID_MIEMBRO", primary_key=True)
    sala = models.ForeignKey(
        ChatSala,
        db_column="ID_SALA",
        on_delete=models.CASCADE,
        related_name="miembros",
    )
    id_usuario = models.BigIntegerField(db_column="ID_USUARIO")
    usuario_nombre = models.CharField(db_column="USUARIO_NOMBRE", max_length=120, blank=True, null=True)
    activo = models.BooleanField(db_column="ACTIVO", default=True)
    unido_en = models.DateTimeField(db_column="UNIDO_EN", auto_now_add=True)

    class Meta:
        db_table = "CHAT_SALA_MIEMBRO"
        constraints = [
            models.UniqueConstraint(fields=["sala", "id_usuario"], name="uq_chat_sala_usuario"),
        ]


class ChatMensaje(models.Model):
    id_mensaje = models.AutoField(db_column="ID_MENSAJE", primary_key=True)
    sala = models.ForeignKey(
        ChatSala,
        db_column="ID_SALA",
        on_delete=models.CASCADE,
        related_name="mensajes",
    )
    id_usuario = models.BigIntegerField(db_column="ID_USUARIO")
    usuario_nombre = models.CharField(db_column="USUARIO_NOMBRE", max_length=120, blank=True, null=True)
    contenido = models.TextField(db_column="CONTENIDO")
    event_id = models.CharField(db_column="EVENT_ID", max_length=80, blank=True, null=True)
    creado_en = models.DateTimeField(db_column="CREADO_EN", auto_now_add=True)

    class Meta:
        db_table = "CHAT_MENSAJE"
        ordering = ["id_mensaje"]


class ChatMensajeLectura(models.Model):
    id_lectura = models.AutoField(db_column="ID_LECTURA", primary_key=True)
    mensaje = models.ForeignKey(
        ChatMensaje,
        db_column="ID_MENSAJE",
        on_delete=models.CASCADE,
        related_name="lecturas",
    )
    sala = models.ForeignKey(
        ChatSala,
        db_column="ID_SALA",
        on_delete=models.CASCADE,
        related_name="lecturas",
    )
    id_usuario = models.BigIntegerField(db_column="ID_USUARIO")
    leido_en = models.DateTimeField(db_column="LEIDO_EN", auto_now_add=True)

    class Meta:
        db_table = "CHAT_MENSAJE_LECTURA"
        constraints = [
            models.UniqueConstraint(fields=["mensaje", "id_usuario"], name="uq_chat_msg_user_read"),
        ]


class ChatMensajeOculto(models.Model):
    id_oculto = models.AutoField(db_column="ID_OCULTO", primary_key=True)
    mensaje = models.ForeignKey(
        ChatMensaje,
        db_column="ID_MENSAJE",
        on_delete=models.CASCADE,
        related_name="ocultamientos",
    )
    sala = models.ForeignKey(
        ChatSala,
        db_column="ID_SALA",
        on_delete=models.CASCADE,
        related_name="mensajes_ocultos",
    )
    id_usuario = models.BigIntegerField(db_column="ID_USUARIO")
    ocultado_en = models.DateTimeField(db_column="OCULTADO_EN", auto_now_add=True)

    class Meta:
        db_table = "CHAT_MENSAJE_OCULTO"
        constraints = [
            models.UniqueConstraint(fields=["mensaje", "id_usuario"], name="uq_chat_msg_user_hidden"),
        ]


class ChatSalaOculta(models.Model):
    id_oculta = models.AutoField(db_column="ID_OCULTA", primary_key=True)
    sala = models.ForeignKey(
        ChatSala,
        db_column="ID_SALA",
        on_delete=models.CASCADE,
        related_name="ocultamientos",
    )
    id_usuario = models.BigIntegerField(db_column="ID_USUARIO")
    ocultado_en = models.DateTimeField(db_column="OCULTADO_EN", auto_now_add=True)

    class Meta:
        db_table = "CHAT_SALA_OCULTA"
        constraints = [
            models.UniqueConstraint(fields=["sala", "id_usuario"], name="uq_chat_room_user_hidden"),
        ]
