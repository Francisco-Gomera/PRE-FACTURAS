from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("empleados", "0006_empleadonomina_observaciones"),
    ]

    operations = [
        migrations.AddField(
            model_name="empleadonomina",
            name="dias_vacaciones",
            field=models.PositiveSmallIntegerField(db_column="DIAS_VACACIONES", default=0),
        ),
    ]
