@echo off
setlocal

cd /d "%~dp0"

set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=%~dp0venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo No se encontro Python del entorno virtual.
    echo.
    echo Busque una de estas rutas:
    echo   %~dp0.venv\Scripts\python.exe
    echo   %~dp0venv\Scripts\python.exe
    echo.
    echo Copia la carpeta completa del sistema o crea el entorno virtual antes de iniciar el agente.
    echo.
    pause
    exit /b 1
)

if not exist "%~dp0tools\local_print_agent.py" (
    echo No se encontro el archivo:
    echo   %~dp0tools\local_print_agent.py
    echo.
    echo Verifica que el .bat este dentro de la carpeta raiz de PRE-FACTURAS.
    echo.
    pause
    exit /b 1
)

call :run_agent "%PYTHON_EXE%"
if %ERRORLEVEL% EQU 0 exit /b 0

echo.
echo El Python del entorno virtual fallo. Intentando con Python instalado en Windows...
echo.

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    call :run_agent py -3
    if %ERRORLEVEL% EQU 0 exit /b 0
)

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    call :run_agent python
    if %ERRORLEVEL% EQU 0 exit /b 0
)

echo.
echo No se pudo iniciar el agente local de impresion.
echo.
echo Si ves un error como:
echo   did not find executable at '...\Python314\python.exe'
echo significa que el entorno virtual fue copiado desde otra PC y no sirve en esta maquina.
echo.
echo Soluciones:
echo   1. Instala Python 3 en esta PC y marca "Add python.exe to PATH".
echo   2. Luego vuelve a abrir este archivo.
echo.
echo Si el puerto 8765 esta ocupado, cierra el otro agente y vuelve a intentarlo.
echo.
pause
exit /b 1

:run_agent
echo Iniciando agente local de impresion...
echo Ruta: %~dp0
echo URL:  http://127.0.0.1:8765
echo Python: %*
echo.
%* "%~dp0tools\local_print_agent.py" --host 127.0.0.1 --port 8765
exit /b %ERRORLEVEL%
