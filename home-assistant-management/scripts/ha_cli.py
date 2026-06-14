#!/usr/bin/env python3
"""Home Assistant CLI — quick HA queries and device control from Hermes sessions."""
import json, os, sys, argparse
from urllib.request import Request, urlopen

HASS_URL = os.getenv("HASS_URL", "http://192.168.1.146:8123")
HASS_TOKEN = os.getenv("HASS_TOKEN", "")

if not HASS_TOKEN:
    print("❌ HASS_TOKEN not set. Use: HASS_TOKEN=$(grep ^HASS_TOKEN= ~/.hermes/.env | head -1 | cut -d= -f2-) python3 scripts/ha_cli.py <cmd>")
    sys.exit(1)

def api(path):
    req = Request(f"{HASS_URL}/api/{path}", headers={
        "Authorization": f"Bearer {HASS_TOKEN}",
        "Content-Type": "application/json",
    })
    return json.loads(urlopen(req, timeout=10).read())

def api_post(path, data):
    req = Request(f"{HASS_URL}/api/{path}", data=json.dumps(data).encode(),
        headers={"Authorization": f"Bearer {HASS_TOKEN}", "Content-Type": "application/json"},
        method="POST")
    return json.loads(urlopen(req, timeout=10).read())

parser = argparse.ArgumentParser(description="Home Assistant CLI")
sub = parser.add_subparsers(dest="cmd")
sub.add_parser("status", help="Show HA version & status")
list_p = sub.add_parser("list", help="List entities by domain")
list_p.add_argument("domain", nargs="?", help="e.g. sensor, switch, lock")
get_p = sub.add_parser("get", help="Get entity state")
get_p.add_argument("entity", help="entity_id e.g. sensor.my_home_solar_power")
call_p = sub.add_parser("call", help="Call a service")
call_p.add_argument("domain", help="e.g. switch, lock")
call_p.add_argument("service", help="e.g. turn_on, lock")
call_p.add_argument("entity", help="Target entity ID")

args = parser.parse_args()

if args.cmd == "status":
    config = api("config")
    states = api("states")
    print(f"🏠 Home Assistant {config['version']}")
    print(f"📍 {config.get('location_name', 'Unknown')} — {config.get('time_zone', '')}")
    print(f"📊 {len(states)} entities, state: {config.get('state', '')}")
elif args.cmd == "list":
    states = api("states")
    filtered = [e for e in states if not args.domain or e['entity_id'].startswith(args.domain + ".")]
    for e in sorted(filtered, key=lambda x: x['entity_id']):
        attrs = e.get("attributes", {})
        unit = attrs.get("unit_of_measurement", "")
        friendly = attrs.get("friendly_name", e['entity_id'])
        print(f"  {e['entity_id']}: {e['state']} {unit}  ({friendly})")
    print(f"\nTotal: {len(filtered)}")
elif args.cmd == "get":
    state = api(f"states/{args.entity}")
    for k, v in sorted(state.get("attributes", {}).items()):
        print(f"  {k}: {v}")
elif args.cmd == "call":
    result = api_post(f"services/{args.domain}/{args.service}", {"entity_id": args.entity})
    print(f"✅ Called {args.domain}.{args.service} on {args.entity}")
else:
    parser.print_help()
