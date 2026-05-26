# NetZero Developer API Specification

From the Netzero app documentation (Settings > Developer API).

## Token Generation

1. Open Netzero app on your phone
2. Navigate to Account menu (last menu icon)
3. Select Settings > Developer API
4. Your API token and energy site ID are displayed
5. Token provides access to config + live status (read/write) but NOT firmware or energy history

## API Reference

### Base URL

```
https://api.netzero.energy/api/v1/{site_id}
```

### Authentication

Bearer token in the Authorization header.

### GET /api/v1/{site_id}/config

Returns current configuration AND live status in one response.

Response shape:
```json
{
  "backup_reserve_percent": 80,
  "operational_mode": "autonomous",
  "energy_exports": "pv_only",
  "grid_charging": true,
  "percentage_charged": 70,
  "grid_status": "Active (on_grid)",
  "live_status": {
    "solar_power": 4140,
    "battery_power": -2520,
    "load_power": 1620,
    "grid_power": 0,
    "wall_connectors": [
      {
        "din": "...",
        "wall_connector_state": 2,
        "wall_connector_fault_state": 2,
        "wall_connector_power": 0
      }
    ]
  }
}
```

### POST /api/v1/{site_id}/config

Modify configuration. Can set one or more parameters in the same request.

**backup_reserve_percent:** Integer 0-100
**operational_mode:** `autonomous`, `self_consumption`, `backup`
**energy_exports:** `pv_only`, `battery_ok`, `never`
**grid_charging:** `true` / `false`
**off_grid_status:** `go_off_grid` / `reconnect_grid` (requires subscription + Powerwall Pairing)

## Operational Modes

| Mode | Display Name | Behaviour |
|------|-------------|-----------|
| `autonomous` | Time-Based Control | Uses stored energy to maximise savings based on utility rate plan |
| `self_consumption` | Self-Powered | Uses stored energy to power home after sun goes down |
| `backup` | Backup Mode | Reserved for grid outages |

## Energy Export Rules

| Setting | Behaviour |
|---------|-----------|
| `pv_only` | Export solar energy only (default) |
| `battery_ok` | Export both solar AND stored Powerwall energy |
| `never` | No export to grid |

## Off-Grid Status

Requires:
- Active Netzero subscription
- Powerwall Pairing configured in app

Used to programmatically disconnect/reconnect from grid (e.g. avoid negative export pricing during specific periods).

## Error Handling

- **403:** Token expired or revoked. Regenerate from Netzero app Settings > Developer API.
- **401/403:** Also occurs if site_id doesn't match the token's authorised site.
- The API does NOT have a separate `/live_status` endpoint — live data is nested inside the `/config` response.

## Python Example

```python
import os
import requests

site_id = os.environ['SITE_ID']
api_token = os.environ['API_TOKEN']

# Read config
resp = requests.get(
    f'https://api.netzero.energy/api/v1/{site_id}/config',
    headers={'Authorization': f'Bearer {api_token}'},
)
data = resp.json()
print(f"Backup reserve: {data['backup_reserve_percent']}%")
print(f"Solar: {data['live_status']['solar_power']}W")

# Update config
config = {'backup_reserve_percent': 30, 'operational_mode': 'autonomous'}
resp = requests.post(
    f'https://api.netzero.energy/api/v1/{site_id}/config',
    headers={'Authorization': f'Bearer {api_token}'},
    json=config,
)
print(resp.json())
```
