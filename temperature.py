import json
from types import SimpleNamespace
import requests

# Service Account credentials.
SERVICE_ACCOUNT_KEY_ID = 'd03qirj24te000b24tmg'
SERVICE_ACCOUNT_SECRET = '3b34c0b2e3f3414fb461da276cfd669f'

# Construct API URL.
PROJECT_ID = 'crcq5p9hf5ovi968ris0'
DEVICE_ID = 'clnem16jqvi000cri4lg'
API_BASE = 'https://api.disruptive-technologies.com/v2/'
DEVICE_URL = f'{API_BASE}projects/{PROJECT_ID}/devices/{DEVICE_ID}'


def get_temperature():
    response = requests.get(
        url=DEVICE_URL,
        auth=(SERVICE_ACCOUNT_KEY_ID, SERVICE_ACCOUNT_SECRET)
    )

    if response.status_code == 200:
        data = json.loads(response.content.decode('ascii'), object_hook=lambda d: SimpleNamespace(**d))
        try:
            return data.reported.temperature.value
        except AttributeError:
            return "Temperature data not available."
    else:
        return f"Error: {response.status_code} - {response.text}"
