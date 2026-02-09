import requests
import os
from dotenv import load_dotenv

# Load Adafruit credentials from .env file
load_dotenv(r"C:\Users\amrut\backend_project\.env")

# Fetch credentials
AIO_USERNAME = os.getenv("ADAFRUIT_IO_USERNAME")
AIO_KEY = os.getenv("ADAFRUIT_IO_KEY")

# Base API URL
BASE_URL = f"https://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds"

# ---------------------------------------------------------
# Function: Send data to Adafruit IO
# ---------------------------------------------------------
def send_to_adafruit(feed_key, value):
    """Send data to a specific Adafruit IO feed."""
    url = f"{BASE_URL}/{feed_key}/data"
    headers = {
        "Content-Type": "application/json",
        "X-AIO-Key": AIO_KEY
    }
    payload = {"value": value}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code in [200, 201]:
        print(f"✅ Sent to {feed_key}: {value}")
    else:
        print(f"❌ Failed ({response.status_code}) → {response.text}")

# ---------------------------------------------------------
# Function: Read latest value from a feed
# ---------------------------------------------------------
def read_from_adafruit(feed_key):
    """Read latest data value from a feed."""
    url = f"{BASE_URL}/{feed_key}/data/last"
    headers = {"X-AIO-Key": AIO_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        value = data.get("value", None)
        print(f"📥 {feed_key} → {value}")
        return value
    else:
        print(f"❌ Error reading {feed_key}: {response.status_code}")
        print(response.text)
        return None

# ---------------------------------------------------------
# 🧪 Test Section
# ---------------------------------------------------------
if __name__ == "__main__":
    # Send sample data to all feeds
    send_to_adafruit("pill-weight", 22.7)
    send_to_adafruit("pill-count", 10)
    send_to_adafruit("pill-taken", 1)
    send_to_adafruit("alert-status", 0)
    send_to_adafruit("box-status", "closed")
    send_to_adafruit("reminder-time", "08:00")
    send_to_adafruit("user-acknowledgement", "acknowledged")

    print("\n--- Reading back latest values ---\n")
    read_from_adafruit("pill-weight")
    read_from_adafruit("pill-count")
    read_from_adafruit("pill-taken")
    read_from_adafruit("alert-status")
    read_from_adafruit("box-status")
    read_from_adafruit("reminder-time")
    read_from_adafruit("user-acknowledgement")
