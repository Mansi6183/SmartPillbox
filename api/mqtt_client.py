import json
import paho.mqtt.client as mqtt
from django.utils import timezone
from .models import PillEvent

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_CMD = "pill_dispenser/cmd"
TOPIC_STATUS = "pillbox/status"

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with code", rc)
    client.subscribe(TOPIC_STATUS)

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"Message received on {msg.topic}: {payload}")
    PillEvent.objects.create(event=payload, timestamp=timezone.now())

def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    client.loop_start()
    return client

mqtt_client = start_mqtt()
