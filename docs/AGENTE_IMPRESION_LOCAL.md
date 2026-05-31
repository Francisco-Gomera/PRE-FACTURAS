# Impresion local con QZ Tray

El sistema usa QZ Tray para respetar la impresora guardada por terminal y modulo. Cada equipo que imprime debe tener QZ Tray instalado y abierto en la bandeja de Windows.

## Iniciar manualmente

Abre QZ Tray desde el menu Inicio de Windows. Debe quedar ejecutandose junto al reloj del sistema.

Ya no es necesario iniciar `start_local_print_agent.bat` para la impresion normal con impresoras predeterminadas.

## Como trabaja

El navegador carga `qz-tray.js`, conecta con QZ Tray por WebSocket local y consulta las impresoras instaladas en Windows. Cuando hay una impresora guardada para el tipo de documento, el HTML se envia a QZ Tray con `qz.print`.

La conexion con QZ Tray usa firma digital propia del proyecto:

- Certificado publico: `C:\PRE-FACTURAS\private\qz\digital-certificate.txt`
- Llave privada: `C:\PRE-FACTURAS\private\qz\private-key.pem`
- Endpoint certificado: `/app/qz/certificate/`
- Endpoint firma: `/app/qz/sign/`

QZ Tray puede pedir permiso la primera vez que vea este certificado. Marca la opcion de recordar/permitir siempre para este sitio. Despues de eso, no deberia pedir permiso en cada impresion mientras el certificado no cambie.

Si QZ Tray no esta abierto, no se puede conectar o no hay impresora configurada para ese modulo, el sistema conserva el flujo de contingencia con el dialogo de impresion del navegador.

## Requisitos

- QZ Tray instalado y abierto en el equipo que imprime.
- Windows con las impresoras instaladas en ese equipo.
- Autorizar el sitio en QZ Tray la primera vez que aparezca el aviso de seguridad.

## Regenerar firma

Solo regenera estos archivos si necesitas rotar el certificado. Al regenerarlo, QZ Tray volvera a pedir autorizacion una vez.

```bat
.venv\Scripts\python.exe manage.py generate_qz_signing --force
```
