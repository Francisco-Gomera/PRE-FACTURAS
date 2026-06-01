import os
from pathlib import Path

from daphne.cli import CommandLineInterface


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prefacturas.settings")
os.environ.setdefault("REALTIME_DB_FORCE_INLINE", "1")

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CERT_FILE = BASE_DIR / "certs" / "localhost+4.pem"
DEFAULT_KEY_FILE = BASE_DIR / "certs" / "localhost+4-key.pem"


def _endpoint_arg(value):
    return str(value).replace("\\", "/").replace(":", r"\:")


def _endpoint_path(path):
    path = Path(path)
    try:
        path = path.resolve().relative_to(BASE_DIR)
    except ValueError:
        path = path.resolve()
    return _endpoint_arg(path)


def main():
    host = os.getenv("DAPHNE_HOST") or os.getenv("WAITRESS_HOST", "0.0.0.0")
    port = os.getenv("DAPHNE_PORT") or os.getenv("WAITRESS_PORT", "8000")
    endpoint = os.getenv("DAPHNE_APP", "prefacturas.asgi:application")
    cert_file = Path(os.getenv("DAPHNE_CERT_FILE", DEFAULT_CERT_FILE))
    key_file = Path(os.getenv("DAPHNE_KEY_FILE", DEFAULT_KEY_FILE))
    ssl_enabled = os.getenv("DAPHNE_SSL", "1").strip().lower() not in {"0", "false", "no"}

    if ssl_enabled and cert_file.exists() and key_file.exists():
        bind_endpoint = (
            f"ssl:{port}:interface={_endpoint_arg(host)}:"
            f"privateKey={_endpoint_path(key_file)}:certKey={_endpoint_path(cert_file)}"
        )
        print(f"Iniciando servidor HTTPS en https://{host}:{port}")
        args = ["-e", bind_endpoint, endpoint]
    else:
        print(f"Iniciando servidor HTTP en http://{host}:{port}")
        args = ["-b", str(host), "-p", str(port), endpoint]

    return CommandLineInterface().run(args)


if __name__ == "__main__":
    raise SystemExit(main())
