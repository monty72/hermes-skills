# Home Assistant Energy Sensor Bridge

> Bypass HA's failed Tesla/Teslemetry integration by creating REST sensors that
> pull live data from the local energy dashboard API. No subscription, no re-auth needed.

## What This Bridge Covers

This bridge is specifically for **Tesla Powerwall live data** (solar, battery, grid, home power).
For **Octopus Energy rates, consumption, and billing**, use the native Octopus Energy HA integration
(see `octopus-energy` skill → Option A: Native HA Integration, and `ha-component-deployment` skill
for SSH installation).

The Home Assistant Tesla integration (official `tesla_fleet` or third-party `teslemetry`)
can fail in several ways:

- **Stale token** — 8-hour access token expired, auto-refresh failed
- **`auth_failed_subscription_required`** — Teslemetry subscription lapsed (state: `setup_error`). Check via `GET /api/config/config_entries/entry` — look for `domain: teslemetry` with `state: setup_error` and `reason: auth_failed_subscription_required`.
- **No HA API re-auth endpoint** — Teslemetry and Tesla Fleet have no programmatic re-auth;
  the user must use the GUI. `POST /api/config/config_entries/entry/{id}/reconfigure` returns 404.
- `supports_reconfigure` may be `true` but there's no programmatic endpoint to invoke it

Result: all `sensor.my_home_*` entities show `unavailable` with `restored: true`.

## Solution: REST Sensor Bridge

Create HA sensor entities via `POST /api/states/<entity_id>` from a script that polls
the local energy dashboard API. The script updates HA directly — no restart needed.

### Architecture

```
┌──────────────┐  GET /api/energy  ┌──────────────────┐  POST /api/states/  ┌──────────┐
│ Local Energy │ ◄──────────────── │ ha_energy_bridge │ ──────────────────► │ HA 2026  │
│ API :8081    │                   │ (cron every 1m)  │                     │ sensors  │
└──────────────┘                   └──────────────────┘                     └──────────┘
```

### Prerequisites

- Energy dashboard API running on port 8081 (`~/energy-dashboard/src/energy_api.py`)
- HA long-lived access token (`HASS_TOKEN` in `~/.hermes/.env`)
- HA instance on `http://192.168.1.146:8123` (or your HA URL)

### Script

Place this in `~/.hermes/scripts/ha_energy_bridge.py` (or wherever Hermes scripts live):

```python
#!/usr/bin/env python3
import json, urllib.request, ssl, os, re

HASS_URL = "http://192.168.1.146:8123"
ENERGY_API = "http://192.168.1.121:8081/api/energy"

# Read HASS_TOKEN from env file
hass_token = ""
with open(os.path.expanduser("~/.hermes/.env")) as f:
    for line in f:
        line = line.strip()
        if line.startswith("HASS_TOKEN="):
            hass_token = line.split("=", 1)[1]

SENSORS = {
    "sensor.energy_solar_power": {"unit": "kW", "icon": "mdi:solar-power", "name": "Solar Power"},
    "sensor.energy_battery_power": {"unit": "kW", "icon": "mdi:battery", "name": "Battery Power"},
    "sensor.energy_grid_power": {"unit": "kW", "icon": "mdi:transmission-tower", "name": "Grid Power"},
    "sensor.energy_home_power": {"unit": "kW", "icon": "mdi:home-lightning-bolt", "name": "Home Power"},
    "sensor.energy_battery_soc": {"unit": "%", "icon": "mdi:battery-charging", "name": "Battery SOC"},
    "sensor.energy_grid_export": {"unit": "kW", "icon": "mdi:export", "name": "Grid Export"},
}

ctx = ssl.create_default_context()

# Fetch energy API data
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

# Push to HA
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
```

### Cron Setup

Create a `no_agent=true` cron job that runs the script every 1 minute:

```bash
# Place script in ~/.hermes/scripts/
cp ha_energy_bridge.py ~/.hermes/scripts/ && chmod +x ~/.hermes/scripts/ha_energy_bridge.py

# Create cron job via Hermes
# cronjob(action='create', name='HA Energy Sensors Bridge', schedule='every 1m',
#         script='ha_energy_bridge.py', no_agent=True, deliver='local')
```

The `no_agent=true` flag means the scheduler runs the script directly and delivers
its stdout verbatim. No LLM tokens are burned.

### Creating Sensors (First Run)

The first run of the script auto-creates the entities in HA via `POST /api/states/`.
No prior setup needed — the entities appear in the entity registry instantly.

### Verifying Sensors

```bash
# Quick check via HA API
curl -s "http://192.168.1.146:8123/api/states/sensor.energy_solar_power" \
  -H "Authorization: Bearer $(grep -oP 'HASS_TOKEN=\K.*' ~/.hermes/.env)"
```

Or via the `ha_get_state` tool in Hermes. The sensors will appear in HA's
developer tools → states immediately.

### Pitfalls

- **HA must be reachable** — the script runs from the Hermes machine and needs
  network access to the HA instance (port 8123)
- **Token in .env is redacted** — you cannot `grep` the token to stdout; write
  the script to read it from the file internally
- **1 minute granularity** — cron's minimum interval is 1 minute. For finer
  resolution, modify the script to loop internally with `time.sleep(30)` and run
  it as a background process
- **Entities persist across restarts** — once created via `POST /api/states/`,
  the entities survive HA restarts but show `unavailable` until the script runs again
- **No discovery** — these won't auto-appear in the Energy dashboard. Add them
  manually in HA's Energy settings or via a Lovelace card
