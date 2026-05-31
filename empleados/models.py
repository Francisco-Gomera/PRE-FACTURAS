from django.db import models


class EmpleadoNomina(models.Model):
    id_empleado = models.AutoField(db_column="ID_EMPLEADO", primary_key=True)
    codigo = models.CharField(db_column="CODIGO", max_length=30, unique=True)
    nombres = models.CharField(db_column="NOMBRES", max_length=100)
    apellidos = models.CharField(db_column="APELLIDOS", max_length=100)
    apodo = models.CharField(db_column="APODO", max_length=60, blank=True)
    cedula = models.CharField(db_column="CEDULA", max_length=20, blank=True)
    estado_civil = models.CharField(db_column="ESTADO_CIVIL", max_length=30, blank=True)
    direccion = models.CharField(db_column="DIRECCION", max_length=250, blank=True)
    telefono = models.CharField(db_column="TELEFONO", max_length=30, blank=True)
    celular = models.CharField(db_column="CELULAR", max_length=30, blank=True)
    tipo_sangre = models.CharField(db_column="TIPO_SANGRE", max_length=5, blank=True)
    fecha_nacimiento = models.DateField(db_column="FECHA_NACIMIENTO", blank=True, null=True)
    nacionalidad = models.CharField(db_column="NACIONALIDAD", max_length=80, blank=True)
    genero = models.CharField(db_column="GENERO", max_length=30, blank=True)
    lugar_nacimiento = models.CharField(db_column="LUGAR_NACIMIENTO", max_length=120, blank=True)
    nivel_academico = models.CharField(db_column="NIVEL_ACADEMICO", max_length=80, blank=True)
    email = models.EmailField(db_column="EMAIL", max_length=120, blank=True)
    carnet = models.CharField(db_column="CARNET", max_length=40, blank=True)
    fecha_ingreso = models.DateField(db_column="FECHA_INGRESO", blank=True, null=True)
    salario_base = models.DecimalField(db_column="SALARIO_BASE", max_digits=12, decimal_places=2, blank=True, null=True)
    forma_pago = models.CharField(db_column="FORMA_PAGO", max_length=30, blank=True)
    banco = models.CharField(db_column="BANCO", max_length=100, blank=True)
    cuenta_bancaria = models.CharField(db_column="CUENTA_BANCARIA", max_length=60, blank=True)
    tipo_cuenta = models.CharField(db_column="TIPO_CUENTA", max_length=30, blank=True)
    frecuencia_pago = models.CharField(db_column="FRECUENCIA_PAGO", max_length=30, blank=True)
    clase_empleado = models.CharField(db_column="CLASE_EMPLEADO", max_length=30, blank=True)
    departamento = models.CharField(db_column="DEPARTAMENTO", max_length=100, blank=True)
    cargo = models.CharField(db_column="CARGO", max_length=80, blank=True)
    supervisor = models.CharField(db_column="SUPERVISOR", max_length=120, blank=True)
    sucursal = models.CharField(db_column="SUCURSAL", max_length=100, blank=True)
    tipo_empleado = models.CharField(db_column="TIPO_EMPLEADO", max_length=30, blank=True)
    poncha = models.BooleanField(db_column="PONCHA", default=False)
    horarios_json = models.TextField(db_column="HORARIOS_JSON", blank=True)
    ars = models.CharField(db_column="ARS", max_length=80, blank=True)
    numero_afiliado = models.CharField(db_column="NUMERO_AFILIADO", max_length=60, blank=True)
    numero_ss = models.CharField(db_column="NUMERO_SS", max_length=60, blank=True)
    pareja_nombre = models.CharField(db_column="PAREJA_NOMBRE", max_length=140, blank=True)
    pareja_telefono = models.CharField(db_column="PAREJA_TELEFONO", max_length=30, blank=True)
    numero_dependientes = models.CharField(db_column="NUMERO_DEPENDIENTES", max_length=10, blank=True)
    contacto_emergencia = models.CharField(db_column="CONTACTO_EMERGENCIA", max_length=140, blank=True)
    celular_emergencia = models.CharField(db_column="CELULAR_EMERGENCIA", max_length=30, blank=True)
    telefono_emergencia = models.CharField(db_column="TELEFONO_EMERGENCIA", max_length=30, blank=True)
    estado = models.CharField(db_column="ESTADO", max_length=30, default="Inactivo")
    observaciones = models.TextField(db_column="OBSERVACIONES", blank=True)
    fecha_creacion = models.DateTimeField(db_column="FECHA_CREACION", auto_now_add=True)
    fecha_modificacion = models.DateTimeField(db_column="FECHA_MODIFICACION", auto_now=True)

    class Meta:
        db_table = "EMPLEADO_NOMINA"
        ordering = ["codigo"]


class EmpleadoEstudio(models.Model):
    id_estudio = models.AutoField(db_column="ID_ESTUDIO", primary_key=True)
    empleado = models.ForeignKey(
        EmpleadoNomina,
        db_column="ID_EMPLEADO",
        on_delete=models.CASCADE,
        related_name="estudios",
    )
    estudio_realizado = models.CharField(db_column="ESTUDIO_REALIZADO", max_length=160)
    desde = models.DateField(db_column="DESDE", blank=True, null=True)
    hasta = models.DateField(db_column="HASTA", blank=True, null=True)
    lugar_estudio = models.CharField(db_column="LUGAR_ESTUDIO", max_length=160, blank=True)
    telefono = models.CharField(db_column="TELEFONO", max_length=30, blank=True)
    contacto = models.CharField(db_column="CONTACTO", max_length=120, blank=True)

    class Meta:
        db_table = "EMPLEADO_ESTUDIO"
        ordering = ["desde", "id_estudio"]


class EmpleadoExperienciaLaboral(models.Model):
    id_experiencia = models.AutoField(db_column="ID_EXPERIENCIA", primary_key=True)
    empleado = models.ForeignKey(
        EmpleadoNomina,
        db_column="ID_EMPLEADO",
        on_delete=models.CASCADE,
        related_name="experiencias_laborales",
    )
    lugar_trabajo = models.CharField(db_column="LUGAR_TRABAJO", max_length=160)
    desde = models.DateField(db_column="DESDE", blank=True, null=True)
    hasta = models.DateField(db_column="HASTA", blank=True, null=True)
    cargo = models.CharField(db_column="CARGO", max_length=120, blank=True)
    supervisor = models.CharField(db_column="SUPERVISOR", max_length=120, blank=True)
    telefono = models.CharField(db_column="TELEFONO", max_length=30, blank=True)

    class Meta:
        db_table = "EMPLEADO_EXPERIENCIA_LABORAL"
        ordering = ["desde", "id_experiencia"]
