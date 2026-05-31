from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("empleados", "0005_empleadoexperiencialaboral"),
    ]

    operations = [
        migrations.AddField(
            model_name="empleadonomina",
            name="observaciones",
            field=models.TextField(blank=True, db_column="OBSERVACIONES"),
        ),
    ]
