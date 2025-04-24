import json
from types import SimpleNamespace
import requests

# Service Account credentials.
SERVICE_ACCOUNT_KEY_ID = 'd00d0k324t8000b24v80'
SERVICE_ACCOUNT_SECRET = '87580614800d45b8a3c3deda2c1aa998'

# Construct API URL.
PROJECT_ID = 'cvlr9f6skjsc739pln70'
DEVICE_ID = 'c9j6j2fck92000emu0lg'
API_BASE = 'https://api.disruptive-technologies.com/v2/'
DEVICE_URL = f'{API_BASE}projects/{PROJECT_ID}/devices/{DEVICE_ID}'


def get_co2():
    response = requests.get(
        url=DEVICE_URL,
        auth=(SERVICE_ACCOUNT_KEY_ID, SERVICE_ACCOUNT_SECRET)
    )

    if response.status_code == 200:
        data = json.loads(response.content.decode('ascii'), object_hook=lambda d: SimpleNamespace(**d))
        try:
            return data.reported.co2.ppm  # CO₂ value in ppm
        except AttributeError:
            return "CO₂ data not available."
    else:
        return f"Error: {response.status_code} - {response.text}"
