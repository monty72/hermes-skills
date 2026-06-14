# HA Hermes API Integration & Gateway — Full Reference

*Absorbed from the consolidated `home-assistant-integration` skill.*

## Authentication

Generate a Long-Lived Access Token at `http://<ha-ip>:8123/profile` → Long-Lived Access Tokens → Create Token. Copy immediately (JWT starting with `eyJhbGci...`).

Test:
```bash
curl -s -H "Authorization: Bearer YOUR_TOKEN" http://<ha-ip>:8123/api/
# Expected: {"message": "API running."}
```

## HA REST API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/` | GET | Health check |
| `/api/config` | GET | HA config (version, location, components) |
| `/api/states` | GET | All entity states |
| `/api/states/<entity_id>` | GET | Single entity state |
| `/api/services/<domain>/<service>` | POST | Call a service |

## Hermes Gateway Integration

### Method A: Environment Variables (Recommended)
```bash
# In ~/.hermes/.env:
HASS_URL=http://192.168.1.146:8123
HASS_TOKEN=eyJhbGci...
```
Then `hermes gateway restart` (⚠️ kills active session).

### Method B: Config Section
```yaml
# In config.yaml:
homeassistant:
  enabled: true
  token: eyJhbGci...
  extra:
    url: http://192.168.1.146:8123
    watch_domains: [sensor, binary_sensor]
    cooldown_seconds: 30
```

### Event Filtering
- `watch_all: true` — every state change (noisy!)
- `watch_domains: [sensor]` — specific categories
- `watch_entities: [sensor.my_home_solar_power]` — individual entities
- `cooldown_seconds: 60` — rate-limit per entity

Without any filter, state_changed events are dropped (logged as warning).

## HASS_TOKEN Recovery After Vault Migration

When `.env` shows `HASS_TOKEN=***`, restore from vault:
```bash
python3 -c "
import os, subprocess
path = os.path.expanduser('~/.hermes/.env')
with open(path) as f: content = f.read()
tok = subprocess.run(['hermes-vault', 'get', 'HASS_TOKEN'], capture_output=True, text=True).stdout.strip()
content = content.replace('HASS_TOKEN=***', f'HASS_TOKEN={tok}')
with open(path, 'w') as f: f.write(content)
print('HASS_TOKEN restored')
"
```

## Quick HA Query Script

Script at `scripts/ha_cli.py` — usage with HASS_TOKEN:
```bash
HASS_TOKEN=$(grep ^HASS_TOKEN= ~/.hermes/.env | head -1 | cut -d= -f2-) python3 scripts/ha_cli.py status
HASS_TOKEN=... python3 scripts/ha_cli.py list sensor
HASS_TOKEN=... python3 scripts/ha_cli.py call lock lock audi_q6_suv_e_tron_door_lock
```

## Key Pitfalls

1. **Gateway restart kills the active session** — never do it mid-conversation. Defer or schedule via cron
2. **`.env` changes require gateway restart** — not hot-reloaded
3. **`unavailable` with `restored: true`** — upstream token expired. HA's Tesla integration token and the energy dashboard token are INDEPENDENT. Refreshing one does NOT fix the other. Re-authenticate via HA Settings → Devices & Services
4. **Token is JWT, not short code** — starts with `eyJh...`
5. **`api/services` POST needs `Content-Type: application/json`** or returns 400
6. **No websocket with REST token** — Long-Lived Access Tokens only work for REST endpoints
