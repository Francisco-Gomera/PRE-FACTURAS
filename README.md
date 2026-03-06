# PRE-FACTURAS (Django + SQL Server)

Proyecto Django listo para trabajar con una base de datos existente en SQL Server.

## 1) Activar entorno virtual

```powershell
.\.venv\Scripts\Activate.ps1
```

## 2) Completar conexión en `.env`

Edita `./.env` con los datos reales de tu servidor:

```env
SQLSERVER_HOST=TU_HOST_O_IP
SQLSERVER_PORT=1433
SQLSERVER_DB=TU_BASE_EXISTENTE
SQLSERVER_USER=TU_USUARIO
SQLSERVER_PASSWORD=TU_PASSWORD
SQLSERVER_DRIVER=ODBC Driver 18 for SQL Server
SQLSERVER_EXTRA_PARAMS=TrustServerCertificate=yes;
```

## 3) Verificar conexión Django -> SQL Server

```powershell
.\.venv\Scripts\python.exe manage.py check
```

## 4) Generar modelos desde tablas existentes

```powershell
.\.venv\Scripts\python.exe manage.py inspectdb > prefacturas_app\models_existing.py
```

Si quieres solo algunas tablas:

```powershell
.\.venv\Scripts\python.exe manage.py inspectdb tabla1 tabla2 > prefacturas_app\models_existing.py
```

## 5) Levantar servidor de desarrollo

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```
