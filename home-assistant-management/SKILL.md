---
name: home-assistant-management
description: "Management skill for Home Assistant deployments, configurations, and troubleshooting."
version: 2.1.0
author: User
license: MIT
---

# Home Assistant Management Skill

## Overview

This skill provides guidance on installing, managing, and troubleshooting Home Assistant. It covers both system-level operations (starting/stopping, securing) and within-HA management (adding integrations, configuring devices).

## References

- `references/adding-integrations-via-config-flow.md` — full walkthrough: adding the Philips Hue bridge to HA via the config flow REST API, including bridge discovery, flow steps, and link-button handling. The Hue example generalises to any HA integration.
- `references/home-assistant-chez-hogarth.md` — Home Assistant setup specifics for this user's environment (Tesla, Powerwall, Octopus integration specifics).
- `references/websocket-api-patterns.md` — HA WebSocket API patterns for real-time subscriptions and device control.

## Scripts

- `scripts/ha_cli.py` — Quick HA query/control CLI from within Hermes sessions. Usage: `HASS_TOKEN=... python3 scripts/ha_cli.py status`

---

## Add-on & HACS Frontend Card Management

For full detail including HA CLI command reference, supervisor troubleshooting, and common add-on slugs, see `references/ha-addon-management.md` (absorbed from the consolidated `ha-addon-management` skill).

### Quick Reference

**Adding repositories:**
```bash
ssh root@<ha-ip> "ha store add https://github.com/zigbee2mqtt/hassio-zigbee2mqtt"
ssh root@<ha-ip> "ha store reload"
```

**Installing add-ons:**
```bash
ssh root@<ha-ip> "ha store apps install <slug>"
```
Common slugs: `a0d7b954_vscode` (Code Server), `core_samba` (Samba), `45df7312_zigbee2mqtt` (Zigbee2MQTT), `core_mosquitto` (Mosquitto broker)

**Key pitfalls:** Supervisor must be up-to-date (`ha supervisor update`) before add-on installs. `ha store reload` is required after adding repos. Samba needs password set in config. HACS frontend cards can be deployed via `git clone --depth 1` into `/config/www/community/`.

---

## Custom Component Deployment

For full detail including GitHub download patterns, config flow API multi-step handling, and HA restart procedures, see `references/ha-component-deployment.md` (absorbed from the consolidated `ha-component-deployment` skill).

### Quick Reference

**Install custom_component via SSH:**
```bash
ssh root@<ha-ip> "
  cd /config
  wget -q -O component.zip 'https://github.com/{owner}/{repo}/archive/refs/tags/v{version}.zip'
  unzip -q component.zip
  cp -r {repo}-*/custom_components/{domain} custom_components/
  rm -rf component.zip {repo}-*/
  ha core restart
"
```

**Config flow via REST API (Python pattern):**
```python
# Step 1: Start the flow
POST /api/config/config_entries/flow
{"handler": "{domain}"}

# Step 2: Submit form data
POST /api/config/config_entries/flow/{flow_id}
# Include all expandable sections even if empty — they're required by the API

# Result: {"type": "create_entry"} on success
```

**Key pitfalls:** Expandable sections in config flow forms are API-required even when visually collapsed. Config flow IDs are single-use. HA restart can take 30-60s — poll for recovery.

---

## Hermes Agent — Home Assistant API Integration & Gateway

For full detail including token generation, API endpoints, gateway configuration, and HASS_TOKEN recovery after vault migration, see `references/ha-hermes-integration.md` (absorbed from the consolidated `home-assistant-integration` skill).

### Quick Reference

**Environment-based auth (recommended):**
```bash
# In ~/.hermes/.env:
HASS_URL=http://192.168.1.146:8123
HASS_TOKEN=eyJhbGci...
```

**Key endpoints:**
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/` | GET | Health check |
| `/api/config` | GET | HA config (version, location, components) |
| `/api/states` | GET | All entity states |
| `/api/services/<domain>/<service>` | POST | Call a service |

**Gateway restart caution:** Restarting the gateway kills the active agent session. Never restart mid-conversation. Defer to off-hours or schedule via cron (`hermes cron create "0 4 * * 0" ...`).

**Key pitfalls:** `unavailable` entities with `restored: true` indicate expired upstream tokens — re-authenticate via HA UI. HA's Tesla integration token and the energy dashboard token are independent — refreshing one does NOT fix the other. Long-Lived Access Tokens only work for REST endpoints, not WebSocket.

---

## Securing Home Assistant
1. Check if Home Assistant is running:
   ```bash
   sudo systemctl status home-assistant
   ```
2. If not, install or start the service:
   ```bash
   sudo systemctl start home-assistant
   ```
3. Secure with SSL using Certbot:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d montygroup.uk -d www.montygroup.uk
   ```
4. Enforce authentication via Home Assistant services to protect API access.

## Adding Integrations via the Config Flow API

HA exposes a REST API for its config flow system, allowing integrations (Hue, Zigbee2MQTT, ESPHome, Tesla, etc.) to be added programmatically. The flow is multi-step and usually requires:

1. **Starting a flow** — POST to `/api/config/config_entries/flow` with `{"handler": "<domain>"}`
2. **Selecting a device** — the response returns a `data_schema` with discovered devices; submit the selection
3. **Physical interaction** — some integrations (Hue, Tradfri) require pressing a link button on the device
4. **Completing the flow** — POST to the flow URL with the link-step response (usually empty body `{}`)

### General Pattern (Python)

```python
import json, urllib.request, ssl

HASS_URL = "http://<ha-ip>:8123"
TOKEN = "eyJh..."  # Long-Lived Access Token

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def ha_flow(method, path, body=None):
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(f"{HASS_URL}/api/{path}", data=data, method=method,
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=10)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read().decode()[:1000]}
    except Exception as e:
        return {"error": str(e)}

# Step 1: Start flow
flow = ha_flow("POST", "config/config_entries/flow", {"handler": "<domain>"})
flow_id = flow["flow_id"]

# Step 2: Submit the device selection (if data_schema present)
step2 = ha_flow("POST", f"config/config_entries/flow/{flow_id}", {"id": "<device_id>"})

# Step 3: After physical button press, complete
result = ha_flow("POST", f"config/config_entries/flow/{flow_id}", {})
# result["type"] == "create_entry" on success
```

### Checklist
- [ ] Long-Lived Access Token ready (from HA profile → Tokens)
- [ ] Integration domain known (e.g. `hue`, `esphome`, `zha`, `tradfri`)
- [ ] Device on same LAN (verify with network scan if needed)
- [ ] Physical button press available (Hue, IKEA Tradfri, some Zigbee coordinators)
- [ ] After success, verify entities appear via `GET /api/states`

### Network Discovery

To find HA-discoverable devices on the LAN:

```bash
# Find Hue bridges
for ip in $(seq 1 254); do
  timeout 0.5 bash -c "curl -s --connect-timeout 1 http://192.168.1.$ip/description.xml 2>/dev/null" 2>/dev/null |
    grep -qi 'hue\|philips' && echo "HUE FOUND: 192.168.1.$ip"
done

# Find any SSDP/uPnP device
for ip in $(seq 1 254); do
  timeout 0.5 bash -c "curl -s --connect-timeout 1 http://192.168.1.$ip/description.xml 2>/dev/null" 2>/dev/null |
    head -5 && echo "DEVICE: 192.168.1.$ip"
done
```

## Creating Scenes via REST API

Scenes can be created programmatically via the `scene.create` service — useful for saving light states that automations can reference.

```python
ha_req("POST", "api/services/scene/create", {
    "scene_id": "patio_lights_on",
    "entities": {
        "light.patio_seating": "on"
    }
})
```

**Important:**
- The `entities` value must be a **string** for simple on/off, or a **dict** for advanced attributes (`{"brightness": 255, "color_temp_kelvin": 2702}`)
- Scenes act as state snapshots — they don't have triggers themselves
- Scene entity IDs follow the pattern `scene.<scene_id>` (e.g. `scene.patio_lights_on`)

## Automation Creation: CRITICAL LIMITATION

**HA 2026.3.1 does NOT expose any programmatic API for creating automations.** This is a hard constraint:

| Approach | Result |
|----------|--------|
| REST `/api/config/automation/config` | 404 — endpoint doesn't exist |
| WebSocket `automation/config` | GET-only (by entity_id) — no create/update |
| WebSocket `automation/config/create` | `unknown_command` |
| `automation.*` services | Only: `turn_on`, `turn_off`, `toggle`, `trigger`, `reload` |
| `config_entries/flow` with handler `automation` | `invalid_handler` |
| Conversation/Assist API | Only handles entity control, not automation creation |

### Working Alternatives

1. **Write `automations.yaml` via Samba share** (recommended if available):
   - Install `smbclient` on the agent host
   - Mount `//<ha-ip>/config` with Samba credentials
   - Write automations YAML to `/config/automations.yaml`
   - Call `automation.reload` service to pick up changes

2. **Cron-based polling (no Samba/SSH needed)** — run a Python script every 5-15m that checks HA's sun.sun state via REST and calls a service when the state transitions. This is a silent watchdog (deliver='local') that only speaks when it acts.
   - Template: `templates/ha-sun-triggered-service.py` in this skill directory
   - Copy to `~/.hermes/scripts/`, edit CONFIG section, schedule as no-agent cron
   - Handles: any `sun.state` value (`above_horizon`/`below_horizon`) and any HA entity
   - Persists last action via a state file so it only fires once per transition
   - Works even when HA's native automation API is locked down

3. **Create scenes + rely on existing smart-bridge automations** — Hue, Tradfri, etc. maintain their own sunset/sunrise triggers on the bridge itself; those appear as `switch` entities in HA.

4. **Node-RED** (runs on port 1880 if installed) — create flows that trigger on sun events and call HA services.

5. **Use the HA WebSocket API for everything *else*** (see `references/websocket-api-patterns.md`).

## WebSocket API: Useful Commands

```python
import json, websocket
ws = websocket.create_connection("ws://192.168.1.146:8123/api/websocket", timeout=10)
msg = json.loads(ws.recv())  # "auth_required"
ws.send(json.dumps({"type": "auth", "access_token": "<token>"}))
msg = json.loads(ws.recv())  # "auth_ok"
msg_id += 1
ws.send(json.dumps({"id": msg_id, "type": "call_service", "domain": "light",
    "service": "turn_on", "target": {"entity_id": "light.patio_seating"}}))
result = json.loads(ws.recv())
```

**Commands that work:**
- `get_config` — HA version, config dir
- `config_entries/get` — list integrations
- `get_services` — all available service domains
- `call_service` — call any service
- `subscribe_events` — subscribe to event types
- `auth/current_user` — current user info
- `config/entity_registry/list` — all registered entities
- `config/device_registry/list` — all registered devices
- `config/area_registry/list` — all defined areas
- `blueprint/list` — list blueprints for a domain
- `automation/config` — GET automation config by entity_id

**Commands that DON'T work (create automation):**
- `automation/config/create`, `automation/config/update`, `automation/config/delete`
- `recipe/*`, `recipe/apply`
- `blueprint/import`, `blueprint/create`

## Troubleshooting
- **If the service is down:** Restart Home Assistant and check logs for errors.
- **If unable to connect:** Confirm network settings and service availability.
- **Config flow returns 404:** The integration domain may not be installed or available in this HA version. Verify via `/api/config/core/integrations`.
- **Link button step times out:** The bridge requires a physical button press within ~30 seconds of the flow reaching the "link" step. Press the button, then resubmit.
- **"Already configured" error:** The integration is already set up. Check existing entries via `GET /api/config/config_entries/entry`.
- **Can't find a service/API to create X:** Check `get_services` (WebSocket) to list ALL available service domains. If no create/setup service exists, that operation requires the UI or file-system config writes.
