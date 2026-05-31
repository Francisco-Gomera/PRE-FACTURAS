from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("empleados", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="empleadonomina",
            name="pareja_nombre",
            field=models.CharField(blank=True, db_column="PAREJA_NOMBRE", max_length=140),
        ),
        migrations.AddField(
            model_name="empleadonomina",
            name="pareja_telefono",
            field=models.CharField(blank=True, db_column="PAREJA_TELEFONO", max_length=30),
        ),
        migrations.AddField(
            model_name="empleadonomina",
            name="numero_dependientes",
            field=models.CharField(blank=True, db_column="NUMERO_DEPENDIENTES", max_length=10),
        ),
        migrations.AddField(
            model_name="empleadonomina",
            name="contacto_emergencia",
            field=models.CharField(blank=True, db_column="CONTACTO_EMERGENCIA", max_length=140),
        ),
        migrations.AddField(
            model_name="empleadonomina",
            name="celular_emergencia",
            field=models.CharField(blank=True, db_column="CELULAR_EMERGENCIA", max_length=30),
        ),
        migrations.AddField(
            model_name="empleadonomina",
            name="telefono_emergencia",
            field=models.CharField(blank=True, db_column="TELEFONO_EMERGENCIA", max_length=30),
        ),
    ]
