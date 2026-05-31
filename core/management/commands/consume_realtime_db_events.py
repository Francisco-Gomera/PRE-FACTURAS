import os
import time

from django.core.management.base import BaseCommand

from core.realtime_db import (
    claim_realtime_db_events,
    complete_realtime_db_event,
    dispatch_realtime_db_event,
    fail_realtime_db_event,
    format_realtime_db_event_log,
    realtime_db_queue_exists,
)


class Command(BaseCommand):
    help = "Consume una cola de eventos de SQL Server y los retransmite por websocket."

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=int(os.getenv("REALTIME_DB_BATCH_SIZE", "50") or 50),
            help="Cantidad maxima de eventos a reclamar por vuelta.",
        )
        parser.add_argument(
            "--sleep",
            type=float,
            default=float(os.getenv("REALTIME_DB_POLL_SECONDS", "1.0") or 1.0),
            help="Segundos de espera entre rondas cuando no hay eventos.",
        )
        parser.add_argument(
            "--worker",
            default=os.getenv("REALTIME_DB_WORKER_NAME", "django-realtime") or "django-realtime",
            help="Nombre del worker que quedara registrado en la cola.",
        )
        parser.add_argument(
            "--once",
            action="store_true",
            help="Procesa una sola tanda y termina.",
        )

    def handle(self, *args, **options):
        batch_size = max(1, min(int(options["batch_size"] or 50), 500))
        sleep_seconds = max(float(options["sleep"] or 1.0), 0.1)
        worker_name = str(options["worker"] or "django-realtime").strip() or "django-realtime"
        run_once = bool(options.get("once"))

        self.stdout.write(self.style.SUCCESS("Realtime DB worker iniciado."))
        self.stdout.write(f"worker={worker_name} batch_size={batch_size} sleep={sleep_seconds}")

        warned_missing_queue = False
        while True:
            if not realtime_db_queue_exists():
                if not warned_missing_queue:
                    self.stdout.write(
                        self.style.WARNING(
                            "La tabla WS_EVENT_QUEUE no existe todavia. Crea la cola SQL y vuelve a intentarlo."
                        )
                    )
                    warned_missing_queue = True
                if run_once:
                    return
                time.sleep(sleep_seconds)
                continue

            warned_missing_queue = False
            events = claim_realtime_db_events(batch_size=batch_size, worker_name=worker_name)
            if not events:
                if run_once:
                    return
                time.sleep(sleep_seconds)
                continue

            for event in events:
                event_id = int(event.get("id_evento") or 0)
                try:
                    dispatched = dispatch_realtime_db_event(event)
                    if not dispatched:
                        raise ValueError(f"Canal no soportado: {event.get('canal') or '-'}")
                    complete_realtime_db_event(event_id)
                    self.stdout.write(self.style.SUCCESS(format_realtime_db_event_log(event)))
                except Exception as exc:
                    fail_realtime_db_event(event_id, str(exc))
                    self.stderr.write(self.style.ERROR(f"{format_realtime_db_event_log(event)} | error={exc}"))

            if run_once:
                return
