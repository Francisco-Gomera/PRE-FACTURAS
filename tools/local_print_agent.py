import argparse
import ctypes
from ctypes import wintypes
import json
import os
import socket
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import winreg
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


PRINT_LOCK = threading.Lock()
winspool = ctypes.WinDLL("winspool.drv")
CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


class PRINTER_INFO_2(ctypes.Structure):
    _fields_ = [
        ("pServerName", wintypes.LPWSTR),
        ("pPrinterName", wintypes.LPWSTR),
        ("pShareName", wintypes.LPWSTR),
        ("pPortName", wintypes.LPWSTR),
        ("pDriverName", wintypes.LPWSTR),
        ("pComment", wintypes.LPWSTR),
        ("pLocation", wintypes.LPWSTR),
        ("pDevMode", wintypes.LPVOID),
        ("pSepFile", wintypes.LPWSTR),
        ("pPrintProcessor", wintypes.LPWSTR),
        ("pDatatype", wintypes.LPWSTR),
        ("pParameters", wintypes.LPWSTR),
        ("pSecurityDescriptor", wintypes.LPVOID),
        ("Attributes", wintypes.DWORD),
        ("Priority", wintypes.DWORD),
        ("DefaultPriority", wintypes.DWORD),
        ("StartTime", wintypes.DWORD),
        ("UntilTime", wintypes.DWORD),
        ("Status", wintypes.DWORD),
        ("cJobs", wintypes.DWORD),
        ("AveragePPM", wintypes.DWORD),
    ]


winspool.EnumPrintersW.argtypes = [
    wintypes.DWORD,
    wintypes.LPWSTR,
    wintypes.DWORD,
    wintypes.LPBYTE,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.DWORD),
]
winspool.EnumPrintersW.restype = wintypes.BOOL
winspool.GetDefaultPrinterW.argtypes = [wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
winspool.GetDefaultPrinterW.restype = wintypes.BOOL
winspool.SetDefaultPrinterW.argtypes = [wintypes.LPWSTR]
winspool.SetDefaultPrinterW.restype = wintypes.BOOL


def run_powershell(command):
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True,
        text=True,
        timeout=20,
    )
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "PowerShell fallo.").strip())
    return result.stdout.strip()


def get_default_printer():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows NT\CurrentVersion\Windows") as key:
            device, _ = winreg.QueryValueEx(key, "Device")
        return str(device or "").split(",", 1)[0].strip()
    except OSError:
        return ""


def get_available_printers():
    default_printer = get_default_printer()
    printers = []
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows NT\CurrentVersion\Devices") as key:
        index = 0
        while True:
            try:
                name, _value, _value_type = winreg.EnumValue(key, index)
            except OSError:
                break
            index += 1
            name = str(name or "").strip()
            if not name:
                continue
            printers.append({"nombre": name, "es_predeterminada": name == default_printer})
    return sorted(printers, key=lambda row: (not row.get("es_predeterminada"), row.get("nombre", "").lower()))


def set_default_printer(printer_name):
    if not winspool.SetDefaultPrinterW(str(printer_name or "")):
        raise ctypes.WinError()


def find_browser():
    candidates = [
        os.environ.get("CA_PRINT_BROWSER", ""),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    for name in ("msedge.exe", "chrome.exe"):
        resolved = shutil.which(name)
        if resolved:
            return resolved
    raise RuntimeError("No se encontro Microsoft Edge ni Google Chrome.")


def sumatra_pdf_candidates():
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    return [
        os.environ.get("CA_PRINT_SUMATRA", ""),
        Path(__file__).resolve().parent / "bin" / "SumatraPDF.exe",
        Path(__file__).resolve().parent.parent / "tools" / "bin" / "SumatraPDF.exe",
        Path(local_appdata) / "SumatraPDF" / "SumatraPDF.exe" if local_appdata else "",
        Path(local_appdata) / "Programs" / "SumatraPDF" / "SumatraPDF.exe" if local_appdata else "",
        r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
        r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
    ]


def find_sumatra_pdf():
    candidates = sumatra_pdf_candidates()
    for candidate in candidates:
        if candidate and Path(candidate).exists() and not is_sumatra_installer(candidate):
            return str(candidate)
    resolved = shutil.which("SumatraPDF.exe")
    if resolved:
        return resolved
    return ""


def is_sumatra_installer(path):
    name = Path(path).name.lower()
    return "install" in name or "installer" in name


def describe_sumatra_candidates():
    rows = []
    for candidate in sumatra_pdf_candidates():
        candidate_text = str(candidate or "").strip()
        if not candidate_text:
            continue
        path = Path(candidate_text)
        rows.append({
            "path": candidate_text,
            "exists": path.exists(),
            "size": path.stat().st_size if path.exists() else 0,
            "looks_like_installer": is_sumatra_installer(path),
        })
    return rows


def add_autoprint_script(html):
    script = """
<script>
window.addEventListener("load", function () {
  var closed = false;
  function closeSoon() {
    if (closed) return;
    closed = true;
    setTimeout(function () { window.close(); }, 1500);
  }
  window.addEventListener("afterprint", closeSoon);
  setTimeout(function () { window.print(); }, 350);
  setTimeout(closeSoon, 6500);
});
</script>
"""
    lower = html.lower()
    index = lower.rfind("</body>")
    if index >= 0:
        return html[:index] + script + html[index:]
    return html + script


def render_html_to_pdf(browser, html, temp_dir, profile_dir):
    html_path = Path(temp_dir) / "documento.html"
    pdf_path = Path(temp_dir) / "documento.pdf"
    html_path.write_text(html, encoding="utf-8")
    process = subprocess.run(
        [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-search-engine-choice-screen",
            "--disable-background-mode",
            f"--user-data-dir={profile_dir}",
            f"--print-to-pdf={pdf_path}",
            html_path.as_uri(),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        timeout=45,
        creationflags=CREATE_NO_WINDOW,
    )
    if process.returncode != 0:
        raise RuntimeError((process.stderr or "No se pudo generar el PDF para imprimir.").strip())
    if not pdf_path.exists() or pdf_path.stat().st_size <= 0:
        raise RuntimeError("No se genero el PDF para imprimir.")
    return pdf_path


def print_pdf_silent(sumatra, printer_name, pdf_path):
    if is_sumatra_installer(sumatra):
        raise RuntimeError(
            "La ruta de SumatraPDF apunta al instalador, no al ejecutable portable. "
            "Instala SumatraPDF o coloca el ejecutable portable real en tools\\bin\\SumatraPDF.exe."
        )
    process = subprocess.run(
        [
            sumatra,
            "-silent",
            "-exit-on-print",
            "-print-to",
            printer_name,
            "-print-settings",
            "noscale",
            str(pdf_path),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        timeout=45,
        creationflags=CREATE_NO_WINDOW,
    )
    if process.returncode != 0:
        raise RuntimeError((process.stderr or "No se pudo enviar el PDF a la impresora.").strip())
    return {"returncode": process.returncode}


def cleanup_later(path, delay_seconds=60):
    def worker():
        time.sleep(max(5, int(delay_seconds or 60)))
        shutil.rmtree(path, ignore_errors=True)

    threading.Thread(target=worker, daemon=True).start()


def configure_browser_printer(profile_dir, printer_name):
    default_dir = Path(profile_dir) / "Default"
    default_dir.mkdir(parents=True, exist_ok=True)
    first_run_path = Path(profile_dir) / "First Run"
    first_run_path.touch(exist_ok=True)
    local_state_path = Path(profile_dir) / "Local State"
    local_state = {}
    if local_state_path.exists():
        try:
            local_state = json.loads(local_state_path.read_text(encoding="utf-8") or "{}")
        except Exception:
            local_state = {}
    local_state.setdefault("browser", {})
    local_state["browser"]["has_seen_welcome_page"] = True
    local_state["browser"]["check_default_browser"] = False
    local_state["browser"]["show_home_button"] = False
    local_state_path.write_text(json.dumps(local_state, ensure_ascii=False), encoding="utf-8")

    preferences_path = default_dir / "Preferences"
    preferences = {}
    if preferences_path.exists():
        try:
            preferences = json.loads(preferences_path.read_text(encoding="utf-8") or "{}")
        except Exception:
            preferences = {}
    app_state = {
        "version": 2,
        "isHeaderFooterEnabled": False,
        "isCssBackgroundEnabled": True,
        "selectedDestinationId": printer_name,
        "recentDestinations": [
            {
                "id": printer_name,
                "origin": "local",
                "account": "",
            }
        ],
    }
    printing = preferences.setdefault("printing", {})
    sticky = printing.setdefault("print_preview_sticky_settings", {})
    sticky["appState"] = json.dumps(app_state, ensure_ascii=False)
    preferences_path.write_text(json.dumps(preferences, ensure_ascii=False), encoding="utf-8")


def print_html(printer_name, html, title="", wait_seconds=8):
    if not printer_name:
        raise ValueError("No se recibio el nombre de la impresora.")
    if not html:
        raise ValueError("No se recibio contenido para imprimir.")

    browser = find_browser()
    sumatra = find_sumatra_pdf()
    previous_default = ""
    temp_dir = Path(tempfile.mkdtemp(prefix="ca_erp_print_"))
    profile_dir = Path(os.environ.get("CA_PRINT_PROFILE_DIR") or temp_dir / "profile")
    profile_dir.mkdir(parents=True, exist_ok=True)

    restore_default = str(os.environ.get("CA_PRINT_RESTORE_DEFAULT") or "").strip().lower() in {"1", "true", "yes", "si"}
    with PRINT_LOCK:
        if sumatra:
            pdf_path = render_html_to_pdf(browser, html, temp_dir, profile_dir)
            print_result = print_pdf_silent(sumatra, printer_name, pdf_path)
            cleanup_later(temp_dir, delay_seconds=60)
            return {
                "ok": True,
                "printer": printer_name,
                "title": title,
                "mode": "pdf_silent",
                "pdf_size": pdf_path.stat().st_size if pdf_path.exists() else 0,
                "sumatra": print_result,
            }

        configure_browser_printer(profile_dir, printer_name)
        html_path = temp_dir / "documento.html"
        html_path.write_text(add_autoprint_script(html), encoding="utf-8")
        try:
            previous_default = get_default_printer()
        except Exception:
            previous_default = ""
        set_default_printer(printer_name)
        process = subprocess.Popen(
            [
                browser,
                "--kiosk-printing",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-search-engine-choice-screen",
                "--disable-popup-blocking",
                "--disable-background-mode",
                "--disable-features=msEdgeWelcomePage",
                f"--user-data-dir={profile_dir}",
                html_path.as_uri(),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(max(5, int(wait_seconds or 5)))
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
        if restore_default and previous_default and previous_default != printer_name:
            try:
                set_default_printer(previous_default)
            except Exception:
                pass
    shutil.rmtree(temp_dir, ignore_errors=True)
    return {"ok": True, "printer": printer_name, "title": title}


class LocalPrintHandler(BaseHTTPRequestHandler):
    server_version = "CAERPPrintAgent/1.0"

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Requested-With")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/health"):
            self.write_json({"ok": True, "service": "CA ERP Local Print Agent"})
            return
        if self.path.startswith("/identity"):
            hostname = socket.gethostname() or os.environ.get("COMPUTERNAME") or "default"
            self.write_json({"ok": True, "terminal": str(hostname).strip()[:100] or "default"})
            return
        if self.path.startswith("/diagnostics"):
            browser = ""
            browser_error = ""
            try:
                browser = find_browser()
            except Exception as exc:
                browser_error = str(exc)
            found_sumatra = find_sumatra_pdf()
            self.write_json({
                "ok": True,
                "terminal": str(socket.gethostname() or os.environ.get("COMPUTERNAME") or "default").strip()[:100] or "default",
                "agent_file": str(Path(__file__).resolve()),
                "browser": browser,
                "browser_error": browser_error,
                "sumatra_found": bool(found_sumatra),
                "sumatra_path": found_sumatra,
                "sumatra_candidates": describe_sumatra_candidates(),
                "print_mode": "pdf_silent" if found_sumatra else "browser_kiosk",
            })
            return
        if self.path.startswith("/printers"):
            try:
                self.write_json({"ok": True, "printers": get_available_printers()})
            except Exception as exc:
                self.write_json({"ok": False, "detail": str(exc), "printers": []}, status=500)
            return
        if self.path.startswith("/test-print"):
            try:
                printer = ""
                query = self.path.split("?", 1)[1] if "?" in self.path else ""
                for part in query.split("&"):
                    key, _, value = part.partition("=")
                    if key == "printer":
                        from urllib.parse import unquote_plus

                        printer = unquote_plus(value).strip()
                        break
                printer = printer or get_default_printer()
                result = print_html(
                    printer,
                    """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body { font-family: Arial, sans-serif; font-size: 14px; padding: 24px; }
    h1 { font-size: 18px; margin: 0 0 8px; }
  </style>
</head>
<body>
  <h1>Prueba de impresion local</h1>
  <p>Si ves esta pagina impresa, el modo silencioso esta funcionando.</p>
</body>
</html>
""",
                    title="Prueba de impresion local",
                    wait_seconds=5,
                )
                self.write_json(result)
            except Exception as exc:
                self.write_json({"ok": False, "detail": str(exc)}, status=500)
            return
        self.write_json({"detail": "Ruta no encontrada."}, status=404)

    def do_POST(self):
        if not self.path.startswith("/print"):
            self.write_json({"detail": "Ruta no encontrada."}, status=404)
            return
        try:
            length = int(self.headers.get("Content-Length") or "0")
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            result = print_html(
                str(payload.get("printer") or "").strip(),
                str(payload.get("html") or ""),
                title=str(payload.get("title") or "").strip(),
                wait_seconds=int(payload.get("wait_seconds") or 8),
            )
            self.write_json(result)
        except Exception as exc:
            self.write_json({"ok": False, "detail": str(exc)}, status=500)

    def write_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main():
    parser = argparse.ArgumentParser(description="Agente local de impresion para CA ERP.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), LocalPrintHandler)
    print(f"CA ERP Local Print Agent escuchando en http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
