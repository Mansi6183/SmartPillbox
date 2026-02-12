import json
import paho.mqtt.client as mqtt
from django.utils import timezone
from .models import PillEvent

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_CMD = "pill_dispenser/cmd"
TOPIC_STATUS = "pillbox/status"
TOPIC_SCHEDULE = "pillbox/schedule"

# ---------- MQTT CALLBACKS ----------
def on_connect(client, userdata, flags, rc):
    print("✅ Connected to MQTT broker:", BROKER)
    client.subscribe(TOPIC_STATUS)

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"📩 Message on {msg.topic}: {payload}")
    PillEvent.objects.create(event=payload, timestamp=timezone.now())

# ---------- START BACKGROUND LISTENER ----------
def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    client.loop_start()
    return client

mqtt_client = start_mqtt()

# ---------- PUBLISH FUNCTION ----------
def publish_schedule(time_str, motor, dose):
    """
    Publish schedule in format HH:MM,Mx,D → pillbox/schedule
    """
    message = f"{time_str},M{motor},{dose}"
    mqtt_client.publish(TOPIC_SCHEDULE, message)
    print(f"📡 MQTT → {TOPIC_SCHEDULE}: {message}")
    PillEvent.objects.create(event=f"Schedule sent: {message}", timestamp=timezone.now())
