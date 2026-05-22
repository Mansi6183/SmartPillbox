
import requests
from django.conf import settings

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
