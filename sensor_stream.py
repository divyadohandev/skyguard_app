import random
import time
import requests

API_URL = "https://skyguard-app-xeak.onrender.com/api/v1/detect"

print("📡 Starting SkyGuard Telemetry Simulator Stream...")

while True:
    # Simulate normal stream vs anomaly injection on interval
    inject_fault = random.random() < 0.2  # 20% anomaly chance

    payload = {
        "station_id": "AWS-IND-001",
        "temperature": 58.4 if inject_fault else round(random.uniform(24, 32), 2),
        "humidity": round(random.uniform(50, 70), 2),
        "pressure": round(random.uniform(1008, 1014), 2),
    }

    try:
        res = requests.post(API_URL, json=payload)
        print(f"Sent Telemetry -> Status: {res.status_code} | Res: {res.json()}")
    except Exception as e:
        print(f"Stream Failed: {e}")

    time.sleep(3)