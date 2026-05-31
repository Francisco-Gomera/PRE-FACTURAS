import os

from daphne.management.commands.runserver import Command as DaphneRunserverCommand

from core.realtime_worker import start_realtime_worker


class Command(DaphneRunserverCommand):
    def inner_run(self, *args, **options):
        use_reloader = bool(options.get("use_reloader"))
        run_main = os.environ.get("RUN_MAIN")
        should_start_worker = (not use_reloader) or (run_main == "true")
        if should_start_worker:
            start_realtime_worker(source="runserver")
        return super().inner_run(*args, **options)
