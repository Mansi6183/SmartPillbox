# pilltracker_backend/tasks.py
from celery import shared_task
from datetime import datetime, timedelta
from .models import PillSchedule, Alert

@shared_task
def check_due_pills():
    now = datetime.now()
    soon = now + timedelta(minutes=5)  # pills due within next 5 minutes

    due_pills = PillSchedule.objects.filter(
        scheduled_time__lte=soon,
        scheduled_time__gte=now,
        taken=False
    )

    for pill in due_pills:
        # Create alert if not already created
        Alert.objects.get_or_create(
            patient=pill.patient,
            pill_schedule=pill,
            defaults={"message": f"Time to take {pill.medicine_name}!"}
        )

    print(f"✅ Checked for due pills at {now}, found {due_pills.count()} pills due soon.")
