from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        import os
        # Only start pinger in the main process and in production
        if os.environ.get('RUN_MAIN') == 'true' or os.environ.get('RENDER'):
             from .utils import start_pinger
             start_pinger()
