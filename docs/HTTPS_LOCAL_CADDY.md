# HTTPS local con Caddy para CA ERP

Esta configuracion permite usar la app por `HTTPS` en la red local para que las notificaciones del sistema y el acceso directo movil funcionen mejor.

## Arquitectura recomendada

- Django + Daphne escuchando solo en `127.0.0.1:8000`
- Caddy exponiendo `https://caerp.local`
- Moviles y PCs entrando siempre por `https://caerp.local`

## 1. Ajustar `.env`

Usa estas variables como base:

```env
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,caerp.local
DJANGO_CSRF_TRUSTED_ORIGINS=https://caerp.local
DAPHNE_HOST=127.0.0.1
DAPHNE_PORT=8000
REALTIME_DB_FORCE_INLINE=1
```

Si prefieres otro nombre interno, reemplaza `caerp.local` por el que vayas a usar en toda la red.

## 2. Hacer que el nombre resuelva a la IP del servidor

Debes lograr que `caerp.local` apunte a la IP del servidor Windows.

Opciones:

- DNS interno del router o servidor
- archivo `hosts` en cada equipo

Ejemplo en `hosts` de Windows:

```text
10.0.0.10 caerp.local
```

Ejemplo en iPhone:

- lo ideal es usar DNS interno para no editar dispositivo por dispositivo

## 3. Instalar Caddy en el servidor

Descarga Caddy para Windows y colocalo, por ejemplo, en:

```text
C:\caddy\caddy.exe
```

Guarda el archivo [Caddyfile.example](/c:/Users/franc/Desktop/PRE-FACTURAS/Caddyfile.example) como:

```text
C:\caddy\Caddyfile
```

Si cambias el dominio, actualizalo ahi tambien.

## 4. Levantar Daphne

Desde el proyecto:

```powershell
.\.venv\Scripts\python.exe run_server.py
```

Con la configuracion actual, Daphne escuchara en:

```text
127.0.0.1:8000
```

## 5. Probar Caddy

Desde PowerShell:

```powershell
C:\caddy\caddy.exe run --config C:\caddy\Caddyfile
```

Luego abre:

```text
https://caerp.local
```

## 6. Confiar el certificado local de Caddy en Windows

Como usaremos `tls internal`, Caddy genera su propia CA local.

En el servidor Windows, normalmente Caddy instala o expone esa CA. Si hace falta exportarla:

```powershell
C:\caddy\caddy.exe trust
```

Si en otro equipo Windows el navegador no confia en el certificado:

1. Exporta la CA raiz de Caddy
2. Importala en `Trusted Root Certification Authorities`

## 7. Confiar el certificado en iPhone

Pasos generales:

1. Exporta el certificado raiz de Caddy
2. Envialo al iPhone
3. Abre el archivo en el iPhone e instalalo
4. Ve a:
   `Ajustes > General > Informacion > Configuracion de confianza de certificados`
5. Activa la confianza total para ese certificado

Sin este paso, Safari puede abrir la pagina, pero no tratarla como origen confiable completo para ciertas capacidades.

## 8. Abrir puertos en firewall

En el servidor, permite entrada TCP a:

- `443` para HTTPS

No necesitas exponer `8000` a la red si Caddy y Daphne corren en la misma maquina.

## 9. Verificacion recomendada

Comprueba lo siguiente:

1. `https://caerp.local` abre sin alerta de certificado en Windows
2. `https://caerp.local` abre sin alerta de certificado en iPhone
3. el acceso directo del iPhone abre esa URL
4. las notificaciones del navegador ya pueden solicitar permiso
5. las notificaciones externas llegan al centro de notificaciones del sistema cuando la app esta abierta o en segundo plano

## 10. Ejecutarlo como servicio

Cuando ya todo funcione, lo ideal es:

- dejar Caddy como servicio de Windows
- dejar la app Django/Daphne como servicio de Windows

Asi no dependes de abrir consolas manualmente cada dia.

## Notas importantes

- Esto mejora mucho escritorio Chromium/Edge
- En iPhone, las notificaciones web tienen mas restricciones que en escritorio
- Para recibir notificaciones con la app totalmente cerrada, el navegador y el sistema siguen imponiendo limites; esta configuracion es el requisito base para acercarnos a una experiencia real de app
