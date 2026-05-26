---
name: netzero-powerwall-api
description: Control Tesla Powerwall 3 configuration via NetZero REST API — backup reserve, operational mode, energy exports, grid charging, off-grid toggling.
tags: [tesla, powerwall, netzero, energy, api]
---

# NetZero Powerwall API

Control Powerwall configuration via NetZero's REST API at `api.netzero.energy`. Works without local gateway password for Powerwall 3.

## Setup

Token stored in vault: `hermes-vault get NETZERO_API_TOKEN`
Site ID: `1689543131745218`

## Endpoints

### GET /config — Read current config + live status

```bash
export API_TOKEN="$(hermes-vault get NETZERO_API_TOKEN)"
export SITE_ID="1689543131745218"

curl -H "Authorization: Bearer $API_TOKEN" \
  https://api.netzero.energy/api/v1/$SITE_ID/config
```

Returns: `backup_reserve_percent`, `operational_mode`, `energy_exports`, `grid_charging`, `percentage_charged`, `grid_status`, `live_status` (solar_power, battery_power, load_power, grid_power, wall_connectors)

### POST /config — Update configuration

Parameters you can set (any combination in one request):
- `backup_reserve_percent`: Integer 0–100
- `operational_mode`: `autonomous` (Time-Based Control), `self_consumption` (Self-Powered), `backup`
- `energy_exports`: `pv_only`, `battery_ok`, `never`
- `grid_charging`: `true` / `false`
- `off_grid_status`: `go_off_grid` / `reconnect_grid` (requires Netzero subscription)

```bash
curl -H "Authorization: Bearer $API_TOKEN" \
  --json '{"backup_reserve_percent": 50, "operational_mode": "self_consumption"}' \
  https://api.netzero.energy/api/v1/$SITE_ID/config
```

### Python

```python
import os, requests
site_id = os.environ['SITE_ID']
api_token = os.environ['API_TOKEN']
config = {'backup_reserve_percent': 30, 'operational_mode': 'autonomous'}
resp = requests.post(
    f'https://api.netzero.energy/api/v1/{site_id}/config',
    headers={'Authorization': f'Bearer {api_token}'},
    json=config,
)
print(resp.json())
```

## Live Status Fields

| Field | Unit | Description |
|-------|------|-------------|
| `solar_power` | W | Solar generation (positive = generating) |
| `battery_power` | W | Battery power (positive = charging, negative = discharging) |
| `load_power` | W | Home consumption |
| `grid_power` | W | Grid power (positive = importing, negative = exporting, 0 = balanced) |
| `wall_connectors[].wall_connector_power` | W | EV charging power per Wall Connector |

## Reference

- `references/netzero-developer-api-spec.md` — Full NetZero Developer API specification including token generation from app, off-grid status requirements, Python examples, and edge cases from production use.

## Pitfalls

- Token scope is limited to config + live status only — no firmware, no energy history
- `off_grid_status` requires a paid Netzero subscription + Powerwall Pairing
- Token is user-facing (from Netzero phone app Settings > Developer API), treat as sensitive
- The `/config` endpoint returns `live_status` nested inside the config response — no separate `/live_status` endpoint needed
- 403 errors mean the token expired or was revoked — regenerate from the Netzero app
