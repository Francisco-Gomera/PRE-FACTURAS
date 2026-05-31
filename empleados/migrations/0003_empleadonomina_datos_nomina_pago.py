from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("empleados", "0002_empleadonomina_pareja_emergencia"),
    ]

    operations = [
        migrations.AddField(
            model_name="empleadonomina",
            name="salario_base",
            field=models.DecimalField(blank=True, db_column="SALARIO_BASE", decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name="empleadonomina",
            name="forma_pago",
            field=models.CharField(blank=True, db_column="FORMA_PAGO", max_length=30),
        ),
        migrations.AddField(
            model_name="empleadonomina",
            name="banco",
            field=models.CharField(blank=True, db_column="BANCO", max_length=100),
        ),
        migrations.AddField(
            model_name="empleadonomina",
            name="cuenta_bancaria",
            field=models.CharField(blank=True, db_column="CUENTA_BANCARIA", max_length=60),
        ),
        migrations.AddField(
            model_name="empleadonomina",
            name="tipo_cuenta",
            field=models.CharField(blank=True, db_column="TIPO_CUENTA", max_length=30),
        ),
        migrations.AddField(
            model_name="empleadonomina",
            name="frecuencia_pago",
            field=models.CharField(blank=True, db_column="FRECUENCIA_PAGO", max_length=30),
        ),
    ]
