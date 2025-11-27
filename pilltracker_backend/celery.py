from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pilltracker_backend.settings')

app = Celery('pilltracker_backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Periodic task scheduler
app.conf.beat_schedule = {
    'check-reminders-every-5-minutes': {
        'task': 'api.tasks.check_pill_reminders',
        'schedule': crontab(minute='*/5'),  # every 5 minutes
    },
}
