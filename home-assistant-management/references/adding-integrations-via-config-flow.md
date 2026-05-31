# Adding HA Integrations via Config Flow API

## Concrete Example: Philips Hue Bridge

### Prerequisites

- HA Long-Lived Access Token in `~/.hermes/.env` as `HASS_TOKEN`
- HA URL: `http://192.168.1.146:8123`
- Hue bridge on same LAN (press the physical button when prompted)

### Step 1: Discover the Hue Bridge

The bridge exposes a uPnP description.xml. Scan the LAN:

```bash
for ip in $(seq 1 254); do
  timeout 0.5 bash -c "curl -s --connect-timeout 1 http://192.168.1.$ip/description.xml 2>/dev/null" 2>/dev/null |
    grep -qi 'hue\|philips' && echo "HUE FOUND: 192.168.1.$ip"
done
```

Result for this setup: `HUE FOUND: 192.168.1.198`

### Step 2: Check Existing Integrations

```python
import json, urllib.request, ssl, os

hass_token = ''
with open(os.path.expanduser('~/.hermes/.env')) as f:
    for line in f:
        if line.startswith('HASS_TOKEN='):
            hass_token = line.split('=', 1)[1]

HASS_URL = 'http://192.168.1.146:8123'
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def ha_req(method, path, body=None):
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(f'{HASS_URL}/api/{path}', data=data, method=method,
        headers={'Authorization': f'Bearer {hass_token}', 'Content-Type': 'application/json'})
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=10)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {'error': e.code, 'body': e.read().decode()[:1000]}
    except Exception as e:
        return {'error': str(e)}

entries = ha_req('GET', 'config/config_entries/entry')
for e in entries or []:
    if isinstance(e, dict):
        print(f"{e.get('domain','?')}: {e.get('title','?')}")
```

### Step 3: Start the Config Flow

```python
flow = ha_req('POST', 'config/config_entries/flow', {
    'handler': 'hue',
    'show_advanced_options': False
})
# Returns flow_id, data_schema with discovered bridges
```

Response:
```json
{
  "type": "form",
  "flow_id": "01KSWDNQNH06CAZ5HM8PX8BFMC",
  "handler": "hue",
  "data_schema": [
    {
      "type": "select",
      "options": [
        ["ecb5fabe1ec1", "192.168.1.198"],
        ["manual", "Manually add a Hue Bridge"]
      ],
      "name": "id",
      "required": true
    }
  ],
  "step_id": "init"
}
```

### Step 4: Select the Bridge

```python
flow_id = flow['flow_id']
step2 = ha_req('POST', f'config/config_entries/flow/{flow_id}', {
    'id': 'ecb5fabe1ec1'
})
```

Response:
```json
{
  "type": "form",
  "flow_id": "01KSWDNQNH06CAZ5HM8PX8BFMC",
  "handler": "hue",
  "data_schema": [],
  "step_id": "link"
}
```

### Step 5: Press the Link Button + Complete

The bridge's link button must be pressed physically within ~30 seconds.

```python
result = ha_req('POST', f'config/config_entries/flow/{flow_id}', {})
```

Success response:
```json
{
  "type": "create_entry",
  "handler": "hue",
  "title": "Hue Bridge ecb5fabe1ec1",
  "result": {
    "entry_id": "01KSWDQQ49ESNQ6QPWVPW29S40",
    "domain": "hue",
    "state": "loaded",
    "title": "Hue Bridge ecb5fabe1ec1"
  }
}
```

### Step 6: Verify

```bash
python3 -c "
import json, urllib.request, ssl, os
hass_token = ''
with open(os.path.expanduser('~/.hermes/.env')) as f:
    for line in f:
        if line.startswith('HASS_TOKEN='):
            hass_token = line.split('=', 1)[1]
HASS_URL = 'http://192.168.1.146:8123'
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
req = urllib.request.Request(f'{HASS_URL}/api/states',
    headers={'Authorization': f'Bearer {hass_token}', 'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req, context=ctx, timeout=10)
states = json.loads(resp.read())
lights = [s for s in states if s['entity_id'].startswith('light.')]
print(json.dumps([{'id': s['entity_id'], 'state': s['state'], 'name': s['attributes'].get('friendly_name','')} for s in lights], indent=2))
"
```

## Useful HA Config Flow API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/config/config_entries/flow` | POST | Start a new config flow (`{"handler": "<domain>"}`) |
| `/api/config/config_entries/flow/{flow_id}` | POST | Continue a flow (submit step data) |
| `/api/config/config_entries/entry` | GET | List all configured integrations |
| `/api/config/config_entries/entry/{entry_id}` | DELETE | Remove an integration |
| `/api/config/config_entries/entry/{entry_id}/reload` | POST | Reload an integration |
| `/api/config/core/integrations` | GET | List available integration domains |

## General Pattern for Other Integrations

Not all integrations follow the same flow shape. Common step sequences:

- **hue / tradfri**: `init` (select bridge) → `link` (press button) → `create_entry`
- **esphome / zha**: `init` (select device/serial) → `configure` (set params) → `create_entry`
- **mqtt**: `user` (enter broker URL/credentials) → `create_entry`
- **mobile_app**: `init` → QR code / link step → external confirmation

Always check the `data_schema` and `step_id` at each step — they tell you what input is expected next.
