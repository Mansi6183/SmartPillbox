
import requests
from django.conf import settings
from django.utils import timezone
from .models import PillSchedule, PillIntake, Alert
def auto_generate_all_alerts():
    auto_generate_missed_alerts()
    check_late_intake()
    check_refill()
    now = timezone.localtime()
    today = now.date()

    schedules = PillSchedule.objects.all()

    for schedule in schedules:
        scheduled_time = timezone.make_aware(
            timezone.datetime.combine(today, schedule.time)
        )

        # Check if already taken
        intake = PillIntake.objects.filter(
            schedule=schedule,
            date=today,
            taken=True
        ).exists()

        # If time passed & not taken → MISSED
        if now > scheduled_time and not intake:

            # Prevent duplicate alerts
            already_exists = Alert.objects.filter(
                patient=schedule.patient,
                alert_type="Missed Dose",
                created_at__date=today,
                message__icontains=schedule.pill_name
            ).exists()

            if not already_exists:
                Alert.objects.create(
                    patient=schedule.patient,
                    message=f"Patient missed {schedule.pill_name} dose at {schedule.time.strftime('%H:%M')}",
                    alert_type="Missed Dose"
                )



def get_latest_feed_value(feed_name):
    """
    Fetches the latest value of a given Adafruit IO feed.
    """
    username = settings.ADAFRUIT_IO_USERNAME
    aio_key = settings.ADAFRUIT_IO_KEY
    url = f"https://io.adafruit.com/api/v2/{username}/feeds/{feed_name}/data/last"

    try:
        response = requests.get(url, headers={"X-AIO-Key": aio_key})
        response.raise_for_status()
        data = response.json()
        return data.get("value", "N/A")
    except Exception as e:
        print(f"Error fetching {feed_name}: {e}")
        return "N/A"
