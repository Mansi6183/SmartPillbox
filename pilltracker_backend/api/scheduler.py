from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
from .models import Medication, Dispense
import paho.mqtt.publish as publish
import json


def check_medications():

    now = timezone.localtime(timezone.now())

    current_time = now.strftime("%H:%M")
    today = now.date()

    medications = Medication.objects.all()

    print("Checking schedules:", current_time)

    for med in medications:

        med_time = med.time.strftime("%H:%M")

        print(f"{med.name} -> {med_time}")

        # Prevent duplicate dispensing
        if med.last_dispensed_date == today:
            continue

        if med_time == current_time:

            print(f"Dispensing {med.name}")

            # MQTT payload
            message = {
                "motor": med.compartment,
                "medicine": med.name
            }

            try:

                publish.single(
                    topic="pillbox/dispense",
                    payload=json.dumps(message),
                    hostname="broker.hivemq.com"
                )

                print("MQTT message sent")

                # Save dispense log
                Dispense.objects.create(
                    medication=med,
                    pill_name=med.name,
                    compartment=med.compartment,
                    status="Dispensed"
                )

                # Update medication
                med.last_dispensed_date = today
                med.status = "Taken"
                med.last_taken = now
                med.save()

            except Exception as e:

                print("MQTT ERROR:", e)


def start():

    scheduler = BackgroundScheduler()

    scheduler.add_job(
        check_medications,
        'interval',
        minutes=1
    )

    scheduler.start()

    print("Scheduler started")