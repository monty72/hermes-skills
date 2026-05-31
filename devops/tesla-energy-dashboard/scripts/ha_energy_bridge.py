#!/usr/bin/env python3
"""HA Energy Sensor Bridge — pushes Tesla energy data to Home Assistant REST sensors.

Usage:
  python3 ha_energy_bridge.py

Requires:
  - Energy dashboard API running on port 8081
  - HASS_TOKEN in ~/.hermes/.env
  - HA instance reachable at http://192.168.1.146:8123

Cron:
  cronjob(action='create', name='HA Energy Sensors Bridge', schedule='every 1m',
          script='ha_energy_bridge.py', no_agent=True, deliver='local')
"""
import json, urllib.request, ssl, os, re

HASS_URL = "http://192.168.1.146:8123"
ENERGY_API = "http://192.168.1.121:8081/api/energy"

hass_token = ""
with open(os.path.expanduser("~/.hermes/.env")) as f:
    for line in f:
        line = line.strip()
        if line.startswith("HASS_TOKEN="):
            hass_token = line.split("=", 1)[1]

if not hass_token:
    print("ERROR: No HASS_TOKEN found in ~/.hermes/.env")
    exit(1)

SENSORS = {
    "sensor.energy_solar_power": {"unit": "kW", "icon": "mdi:solar-power", "name": "Solar Power"},
    "sensor.energy_battery_power": {"unit": "kW", "icon": "mdi:battery", "name": "Battery Power"},
    "sensor.energy_grid_power": {"unit": "kW", "icon": "mdi:transmission-tower", "name": "Grid Power"},
    "sensor.energy_home_power": {"unit": "kW", "icon": "mdi:home-lightning-bolt", "name": "Home Power"},
    "sensor.energy_battery_soc": {"unit": "%", "icon": "mdi:battery-charging", "name": "Battery SOC"},
    "sensor.energy_grid_export": {"unit": "kW", "icon": "mdi:export", "name": "Grid Export"},
}

ctx = ssl.create_default_context()

try:
    req = urllib.request.Request(ENERGY_API)
    resp = urllib.request.urlopen(req, context=ctx, timeout=10)
    data = json.loads(resp.read())
except Exception as e:
    print(f"Error fetching energy API: {e}")
    exit(1)

if "error" in data:
    print(f"Energy API error: {data['error']}")
    exit(1)

for entity_id, config in SENSORS.items():
    if entity_id == "sensor.energy_grid_export":
        state = str(abs(data.get("grid_kw", 0)) if data.get("grid_kw", 0) < 0 else 0)
    elif entity_id == "sensor.energy_battery_soc":
        state = str(round(data.get("battery_percent", 0), 1))
    elif entity_id == "sensor.energy_solar_power":
        state = str(data.get("solar_kw", 0))
    elif entity_id == "sensor.energy_battery_power":
        state = str(data.get("battery_kw", 0))
    elif entity_id == "sensor.energy_grid_power":
        state = str(data.get("grid_kw", 0))
    elif entity_id == "sensor.energy_home_power":
        state = str(data.get("home_kw", 0))
    else:
        continue

    body = json.dumps({
        "state": state,
        "attributes": {
            "unit_of_measurement": config["unit"],
            "friendly_name": config["name"],
            "icon": config["icon"],
            "source": "tesla_cloud"
        }
    }).encode()

    req = urllib.request.Request(
        f"{HASS_URL}/api/states/{entity_id}",
        data=body, method="POST",
        headers={
            "Authorization": f"Bearer {hass_token}",
            "Content-Type": "application/json"
        }
    )
    try:
        urllib.request.urlopen(req, context=ctx, timeout=10)
    except Exception as e:
        print(f"Error updating {entity_id}: {e}")

print("ok")
