"""
Utilidades para gestionar impresoras del sistema.
"""

import subprocess
import re
import platform
import logging

logger = logging.getLogger(__name__)


def get_available_printers():
    """
    Detecta las impresoras disponibles en el sistema.
    Compatible con Windows y otros sistemas operativos.
    
    Returns:
        list: Lista de diccionarios con información de las impresoras disponibles.
              Cada diccionario contiene 'nombre' y 'es_predeterminada'.
    """
    system = platform.system()
    
    try:
        if system == "Windows":
            return _get_printers_windows()
        elif system == "Darwin":  # macOS
            return _get_printers_macos()
        elif system == "Linux":
            return _get_printers_linux()
        else:
            logger.warning(f"Sistema operativo no soportado: {system}")
            return []
    except Exception as e:
        logger.error(f"Error general detectando impresoras: {str(e)}")
        return []


def _get_printers_windows():
    """Detecta impresoras en Windows usando PowerShell."""
    try:
        # Comando PowerShell simple para obtener las impresoras
        powershell_cmd = 'Get-Printer | Select-Object -Property Name, Default | ConvertTo-Csv -NoTypeInformation'
        cmd = ["powershell", "-NoProfile", "-Command", powershell_cmd]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            logger.warning(f"Error ejecutando PowerShell: {result.stderr}")
            # Intentar con un comando alternativo
            try:
                cmd_alt = ["powershell", "-NoProfile", "-Command", "Get-Printer | Select-Object Name"]
                result = subprocess.run(cmd_alt, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    printers = []
                    for line in result.stdout.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('-'):
                            printers.append({'nombre': line, 'es_predeterminada': False})
                    return printers
            except Exception:
                pass
            return []
        
        printers = []
        lines = result.stdout.strip().split('\n')
        
        # Saltar la línea de encabezados
        if len(lines) > 1:
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue
                # Parsear CSV con comillas
                parts = []
                current = ""
                in_quotes = False
                for char in line:
                    if char == '"':
                        in_quotes = not in_quotes
                    elif char == ',' and not in_quotes:
                        parts.append(current)
                        current = ""
                    else:
                        current += char
                parts.append(current)
                
                if len(parts) >= 1:
                    nombre = parts[0].strip()
                    es_default = len(parts) > 1 and parts[1].strip().lower() == 'true'
                    if nombre:  # Solo si el nombre no está vacío
                        printers.append({
                            'nombre': nombre,
                            'es_predeterminada': es_default
                        })
        
        return printers
    except Exception as e:
        logger.error(f"Error detectando impresoras en Windows: {str(e)}")
        return []


def _get_printers_macos():
    """Detecta impresoras en macOS usando lpstat."""
    try:
        # Obtener impresoras disponibles
        result = subprocess.run(['lpstat', '-p', '-d'], capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            return []
        
        printers = []
        default_printer = None
        
        # Encontrar impresora predeterminada
        for line in result.stdout.split('\n'):
            if 'device for' in line:
                # Línea como: "device for HP_LaserJet: ..."
                default_printer = line.split('device for ')[-1].split(':')[0].strip()
        
        # Obtener lista de impresoras
        result = subprocess.run(['lpstat', '-p'], capture_output=True, text=True, timeout=10)
        
        for line in result.stdout.split('\n'):
            if line.startswith('printer'):
                # Línea como: "printer hp_2 is idle"
                parts = line.split()
                if len(parts) >= 2:
                    nombre = parts[1]
                    es_default = nombre == default_printer
                    printers.append({
                        'nombre': nombre,
                        'es_predeterminada': es_default
                    })
        
        return printers
    except Exception as e:
        logger.error(f"Error detectando impresoras en macOS: {str(e)}")
        return []


def _get_printers_linux():
    """Detecta impresoras en Linux usando CUPS (lpstat)."""
    try:
        # Comando para obtener impresoras en Linux
        result = subprocess.run(['lpstat', '-p', '-d'], capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            return []
        
        printers = []
        default_printer = None
        
        # Encontrar impresora predeterminada
        for line in result.stdout.split('\n'):
            if 'device for' in line:
                # Línea como: "device for HP_LaserJet: ..."
                parts = line.split('device for ')
                if len(parts) > 1:
                    default_printer = parts[1].split(':')[0].strip()
        
        # Obtener lista de impresoras
        result = subprocess.run(['lpstat', '-p'], capture_output=True, text=True, timeout=10)
        
        for line in result.stdout.split('\n'):
            if line.startswith('printer'):
                # Línea como: "printer hp_2 is idle"
                parts = line.split()
                if len(parts) >= 2:
                    nombre = parts[1]
                    es_default = nombre == default_printer
                    printers.append({
                        'nombre': nombre,
                        'es_predeterminada': es_default
                    })
        
        return printers
    except Exception as e:
        logger.error(f"Error detectando impresoras en Linux: {str(e)}")
        return []
