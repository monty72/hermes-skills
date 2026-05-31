#!/usr/bin/env python3
"""
Template: Sun-triggered HA service via polling cron
====================================================
Polls HA's sun.sun state periodically and calls a service when the
sun crosses the horizon. Use as a cron-no-agent watchdog script when
HA's native automation API doesn't expose create/update endpoints.

Copy this file to ~/.hermes/scripts/, edit the CONFIG section, then
schedule via: cronjob(action='create', schedule='every 15m', no_agent=True,
                    script='<your-script-name>.py', deliver='local')

For even coverage, 'every 15m' catches the transition within ~7.5 minutes.
If you need tighter, use 'every 5m' (but HA's sun.sun state updates at
most every 60s so sub-5m adds no value).
"""
import json, urllib.request, ssl, os, sys
from datetime import datetime, timezone

# ── CONFIG ── edit these for your setup ──────────────────────────
HASS_URL = "http://192.168.1.146:8123"
ENTITY_ID = "light.patio_seating"          # entity to control
ON_TRIGGER = "below_horizon"               # sun.state value → turn on
OFF_TRIGGER = "above_horizon"              # sun.state value → turn off
STATE_FILE = os.path.expanduser(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        os.path.splitext(os.path.basename(__file__))[0] + "_state.json"
    )
)
# ──────────────────────────────────────────────────────────────────

# Read token
TOKEN = ""
env_path = os.path.expanduser("~/.hermes/.env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("HASS_TOKEN="):
                TOKEN = line.split("=", 1)[1]
if not TOKEN:
    print("ERROR: HASS_TOKEN not found in ~/.hermes/.env")
    sys.exit(1)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def ha_req(method, path, body=None):
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        f"{HASS_URL}/api/{path}", data=data, method=method,
        headers={"Authorization": f"Bearer {TOKEN}",
                 "Content-Type": "application/json"}
    )
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=10)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HA error {e.code}: {e.read().decode()[:200]}")
        return None
    except Exception as e:
        print(f"Request error: {e}")
        return None

def get_sun_state():
    state = ha_req("GET", "states/sun.sun")
    if not state:
        return None
    attrs = state.get("attributes", {})
    return {
        "state": state.get("state"),
        "next_setting": attrs.get("next_setting"),
        "next_rising": attrs.get("next_rising"),
    }

def turn_entity(on=True):
    service = "turn_on" if on else "turn_off"
    result = ha_req("POST", f"services/light/{service}",
                    {"entity_id": ENTITY_ID})
    return result is not None

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {"last_action": None}

def save_state(s):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(s, f)

# ── Main logic ───────────────────────────────────────────────────
sun = get_sun_state()
if not sun:
    sys.exit(1)

state = load_state()
current = sun["state"]
now = datetime.now(timezone.utc).isoformat()

print(f"Sun: {current} | Last action: {state.get('last_action')}")

if current == ON_TRIGGER and state.get("last_action") != "on":
    if turn_entity(on=True):
        save_state({"last_action": "on", "last_trigger": now})
        print(f"→ Turned {ENTITY_ID} ON ({ON_TRIGGER})")

elif current == OFF_TRIGGER and state.get("last_action") != "off":
    if turn_entity(on=False):
        save_state({"last_action": "off", "last_trigger": now})
        print(f"→ Turned {ENTITY_ID} OFF ({OFF_TRIGGER})")
    save_state({"last_action": "off", "last_trigger": now})
