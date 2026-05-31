import os

from daphne.cli import CommandLineInterface


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prefacturas.settings")
os.environ.setdefault("REALTIME_DB_FORCE_INLINE", "1")


def main():
    host = os.getenv("DAPHNE_HOST") or os.getenv("WAITRESS_HOST", "0.0.0.0")
    port = os.getenv("DAPHNE_PORT") or os.getenv("WAITRESS_PORT", "8000")
    endpoint = os.getenv("DAPHNE_APP", "prefacturas.asgi:application")
    args = [
        "-b",
        str(host),
        "-p",
        str(port),
        endpoint,
    ]
    return CommandLineInterface().run(args)


if __name__ == "__main__":
    raise SystemExit(main())
