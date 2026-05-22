import os
from django.apps import AppConfig


class ApiConfig(AppConfig):

    default_auto_field = 'django.db.models.BigAutoField'

    name = 'pilltracker_backend.api'

    def ready(self):

        # Prevent duplicate scheduler
        if os.environ.get('RUN_MAIN') != 'true':
            return

        from .scheduler import start

        start()