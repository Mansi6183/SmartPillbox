import paho.mqtt.client as mqtt
import json
import time

broker = "broker.hivemq.com"
port = 1883
topic = "pillbox/schedule"

# Create MQTT client (old API)
client = mqtt.Client("BackendPublisher")
client.connect(broker, port, 60)

# Prepare JSON schedule
schedule = {
    "hour": 14,
    "minute": 30,
    "motor": 1,
    "dose": 2
}

payload = json.dumps(schedule)
client.publish(topic, payload)
print("✅ Schedule sent to ESP32!")
time.sleep(1)
client.disconnect()
