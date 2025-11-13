from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pilltracker_backend.settings')

# Create Celery app instance
app = Celery('pilltracker_backend')

# Load settings from Django settings.py (optional prefix CELERY_)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks.py in all apps
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
