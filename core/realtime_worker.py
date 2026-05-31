import atexit
import os
import sys
import threading
import time

from django.db import close_old_connections

from .realtime_db import (
    claim_realtime_db_events,
    complete_realtime_db_event,
    dispatch_realtime_db_event,
    fail_realtime_db_event,
    realtime_db_queue_exists,
)


_worker_thread = None
_worker_lock = threading.Lock()
_worker_stop_event = threading.Event()


def _env_flag(name, default=False):
    raw = os.getenv(name)
    if raw is None:
        return bool(default)
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def should_autostart_realtime_worker():
    if _env_flag("REALTIME_DB_AUTOSTART", True) is False:
        return False
    if _env_flag("REALTIME_DB_WORKER_DISABLED", False):
        return False
    return True


def _worker_loop(batch_size, sleep_seconds):
    while not _worker_stop_event.is_set():
        try:
            close_old_connections()
            if not realtime_db_queue_exists():
                _worker_stop_event.wait(sleep_seconds)
                continue
            events = claim_realtime_db_events(batch_size=batch_size, worker_name="django-inline")
            if not events:
                _worker_stop_event.wait(sleep_seconds)
                continue
            for event in events:
                event_id = int(event.get("id_evento") or 0)
                try:
                    dispatched = dispatch_realtime_db_event(event)
                    if dispatched:
                        complete_realtime_db_event(event_id)
                    else:
                        fail_realtime_db_event(event_id, f"Canal no soportado: {event.get('canal') or '-'}")
                except Exception as exc:
                    fail_realtime_db_event(event_id, str(exc))
        except Exception:
            _worker_stop_event.wait(sleep_seconds)
        finally:
            close_old_connections()


def stop_realtime_worker():
    _worker_stop_event.set()


atexit.register(stop_realtime_worker)


def start_realtime_worker(*, source="server", batch_size=None, sleep_seconds=None):
    del source
    if not should_autostart_realtime_worker():
        return None

    safe_batch_size = max(1, min(int(batch_size or os.getenv("REALTIME_DB_BATCH_SIZE", "50") or 50), 500))
    safe_sleep_seconds = max(float(sleep_seconds or os.getenv("REALTIME_DB_POLL_SECONDS", "1.0") or 1.0), 0.1)

    with _worker_lock:
        global _worker_thread
        if _worker_thread and _worker_thread.is_alive():
            return _worker_thread
        _worker_stop_event.clear()
        _worker_thread = threading.Thread(
            target=_worker_loop,
            args=(safe_batch_size, safe_sleep_seconds),
            name="realtime-db-worker",
            daemon=True,
        )
        _worker_thread.start()
        return _worker_thread


def maybe_start_realtime_worker_for_current_process():
    if _env_flag("REALTIME_DB_FORCE_INLINE", False):
        return start_realtime_worker(source="forced-inline")
    argv = [str(arg or "").strip().lower() for arg in sys.argv]
    if len(argv) < 2:
        return None
    command = argv[1]
    if command != "runserver":
        return None
    uses_reloader = "--noreload" not in argv
    run_main = os.environ.get("RUN_MAIN")
    if uses_reloader and run_main != "true":
        return None
    return start_realtime_worker(source="runserver")
