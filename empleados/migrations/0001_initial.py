from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="EmpleadoNomina",
            fields=[
                ("id_empleado", models.AutoField(db_column="ID_EMPLEADO", primary_key=True, serialize=False)),
                ("codigo", models.CharField(db_column="CODIGO", max_length=30, unique=True)),
                ("nombres", models.CharField(db_column="NOMBRES", max_length=100)),
                ("apellidos", models.CharField(db_column="APELLIDOS", max_length=100)),
                ("apodo", models.CharField(blank=True, db_column="APODO", max_length=60)),
                ("cedula", models.CharField(blank=True, db_column="CEDULA", max_length=20)),
                ("estado_civil", models.CharField(blank=True, db_column="ESTADO_CIVIL", max_length=30)),
                ("direccion", models.CharField(blank=True, db_column="DIRECCION", max_length=250)),
                ("telefono", models.CharField(blank=True, db_column="TELEFONO", max_length=30)),
                ("celular", models.CharField(blank=True, db_column="CELULAR", max_length=30)),
                ("tipo_sangre", models.CharField(blank=True, db_column="TIPO_SANGRE", max_length=5)),
                ("fecha_nacimiento", models.DateField(blank=True, db_column="FECHA_NACIMIENTO", null=True)),
                ("nacionalidad", models.CharField(blank=True, db_column="NACIONALIDAD", max_length=80)),
                ("genero", models.CharField(blank=True, db_column="GENERO", max_length=30)),
                ("lugar_nacimiento", models.CharField(blank=True, db_column="LUGAR_NACIMIENTO", max_length=120)),
                ("nivel_academico", models.CharField(blank=True, db_column="NIVEL_ACADEMICO", max_length=80)),
                ("email", models.EmailField(blank=True, db_column="EMAIL", max_length=120)),
                ("carnet", models.CharField(blank=True, db_column="CARNET", max_length=40)),
                ("fecha_ingreso", models.DateField(blank=True, db_column="FECHA_INGRESO", null=True)),
                ("clase_empleado", models.CharField(blank=True, db_column="CLASE_EMPLEADO", max_length=30)),
                ("departamento", models.CharField(blank=True, db_column="DEPARTAMENTO", max_length=100)),
                ("cargo", models.CharField(blank=True, db_column="CARGO", max_length=80)),
                ("supervisor", models.CharField(blank=True, db_column="SUPERVISOR", max_length=120)),
                ("sucursal", models.CharField(blank=True, db_column="SUCURSAL", max_length=100)),
                ("tipo_empleado", models.CharField(blank=True, db_column="TIPO_EMPLEADO", max_length=30)),
                ("poncha", models.BooleanField(db_column="PONCHA", default=False)),
                ("horarios_json", models.TextField(blank=True, db_column="HORARIOS_JSON")),
                ("ars", models.CharField(blank=True, db_column="ARS", max_length=80)),
                ("numero_afiliado", models.CharField(blank=True, db_column="NUMERO_AFILIADO", max_length=60)),
                ("numero_ss", models.CharField(blank=True, db_column="NUMERO_SS", max_length=60)),
                ("estado", models.CharField(db_column="ESTADO", default="Inactivo", max_length=30)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True, db_column="FECHA_CREACION")),
                ("fecha_modificacion", models.DateTimeField(auto_now=True, db_column="FECHA_MODIFICACION")),
            ],
            options={
                "db_table": "EMPLEADO_NOMINA",
                "ordering": ["codigo"],
            },
        ),
    ]
