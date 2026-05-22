# pilltracker_backend/tasks.py

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import PillSchedule, Alert

@shared_task
def check_due_pills():
    now = timezone.now()  # Use timezone-aware datetime
    soon = now + timedelta(minutes=5)  # Pills due within the next 5 minutes

    # Filter pill schedules that are due soon and not taken
    due_pills = PillSchedule.objects.filter(
        scheduled_time__gte=now,
        scheduled_time__lte=soon,
        taken=False
    )

    for pill in due_pills:
        # Prevent duplicate alerts for the same schedule
        alert, created = Alert.objects.get_or_create(
            patient=pill.patient,
            pill_schedule=pill,
            alert_type='reminder',
            defaults={
                "message": f"💊 Reminder: It's time to take {pill.medicine_name}!"
            }
        )

        if created:
            print(f"🔔 Created reminder for {pill.patient.name} - {pill.medicine_name}")
        else:
            print(f"⏱ Reminder already exists for {pill.medicine_name}")

    print(f"✅ Checked for due pills at {now.strftime('%H:%M:%S')}, found {due_pills.count()} pills due soon.")
