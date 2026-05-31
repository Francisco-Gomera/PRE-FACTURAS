from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        from .realtime_worker import maybe_start_realtime_worker_for_current_process

        maybe_start_realtime_worker_for_current_process()
