from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("chat_interno", "0002_chatmensajelectura"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChatMensajeOculto",
            fields=[
                ("id_oculto", models.AutoField(db_column="ID_OCULTO", primary_key=True, serialize=False)),
                ("id_usuario", models.BigIntegerField(db_column="ID_USUARIO")),
                ("ocultado_en", models.DateTimeField(auto_now_add=True, db_column="OCULTADO_EN")),
                ("mensaje", models.ForeignKey(db_column="ID_MENSAJE", on_delete=models.deletion.CASCADE, related_name="ocultamientos", to="chat_interno.chatmensaje")),
                ("sala", models.ForeignKey(db_column="ID_SALA", on_delete=models.deletion.CASCADE, related_name="mensajes_ocultos", to="chat_interno.chatsala")),
            ],
            options={
                "db_table": "CHAT_MENSAJE_OCULTO",
            },
        ),
        migrations.CreateModel(
            name="ChatSalaOculta",
            fields=[
                ("id_oculta", models.AutoField(db_column="ID_OCULTA", primary_key=True, serialize=False)),
                ("id_usuario", models.BigIntegerField(db_column="ID_USUARIO")),
                ("ocultado_en", models.DateTimeField(auto_now_add=True, db_column="OCULTADO_EN")),
                ("sala", models.ForeignKey(db_column="ID_SALA", on_delete=models.deletion.CASCADE, related_name="ocultamientos", to="chat_interno.chatsala")),
            ],
            options={
                "db_table": "CHAT_SALA_OCULTA",
            },
        ),
        migrations.AddConstraint(
            model_name="chatmensajeoculto",
            constraint=models.UniqueConstraint(fields=("mensaje", "id_usuario"), name="uq_chat_msg_user_hidden"),
        ),
        migrations.AddConstraint(
            model_name="chatsalaoculta",
            constraint=models.UniqueConstraint(fields=("sala", "id_usuario"), name="uq_chat_room_user_hidden"),
        ),
    ]
