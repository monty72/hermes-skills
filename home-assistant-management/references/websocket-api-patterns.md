# HA WebSocket API: Patterns & Pitfalls

> HA Core 2026.3.1 on HAOS. Discovered via extensive probing of available commands.

## Auth Flow

```python
import json, websocket

ws = websocket.create_connection("ws://<ha-ip>:8123/api/websocket", timeout=10)

# 1. Server sends auth_required
msg = json.loads(ws.recv())
assert msg["type"] == "auth_required"

# 2. Send long-lived access token (NOT wrapped in "id" — auth message has no id field)
ws.send(json.dumps({"type": "auth", "access_token": "<token>"}))

# 3. Server responds with auth_ok
msg = json.loads(ws.recv())
assert msg["type"] == "auth_ok"
```

**Pitfall:** The auth message does NOT accept an `id` field — `{"id": 1, "type": "auth", ...}` returns `auth_invalid`. Only the regular command messages use `id`.

## Standard Command Pattern

```python
msg_id = 0

def send(ws, cmd_type, **kwargs):
    global msg_id
    msg_id += 1
    payload = {"id": msg_id, "type": cmd_type, **kwargs}
    ws.send(json.dumps(payload))

def recv(ws):
    return json.loads(ws.recv())
```

## Working Commands

### `get_config`
Returns full HA configuration including version, config_dir, components, etc.

```python
send(ws, "get_config")
msg = recv(ws)
# msg["result"]["version"] -> "2026.3.1"
# msg["result"]["config_dir"] -> "/config"
```

### `config_entries/get`
Lists all configured integrations (config entries).

```python
send(ws, "config_entries/get")
msg = recv(ws)
for entry in msg["result"]:
    print(entry["domain"], entry["title"])
```

### `get_services`
Lists all available service domains and their methods. Use this before assuming a service exists.

```python
send(ws, "get_services")
msg = recv(ws)
auto_svcs = msg["result"].get("automation", {})
print(list(auto_svcs.keys()))  # e.g. ['trigger', 'toggle', 'turn_on', 'turn_off', 'reload']
```

### `call_service`
The workhorse — call any HA service.

```python
send(ws, "call_service",
    domain="light",
    service="turn_on",
    target={"entity_id": "light.patio_seating"},
    service_data={}  # optional
)
msg = recv(ws)
# msg["success"] == True on success
```

### `auth/current_user`
Get current authenticated user info.

```python
send(ws, "auth/current_user")
msg = recv(ws)
# msg["result"]["name"], msg["result"]["is_owner"], msg["result"]["is_admin"]
```

### `config/entity_registry/list`
Every registered entity with metadata (config_entry_id, device_id, area_id, etc.).

```python
send(ws, "config/entity_registry/list")
msg = recv(ws)
for ent in msg["result"]:
    print(ent["entity_id"], ent.get("config_entry_id", "?"))
```

### `config/device_registry/list`
Every registered device.

### `config/area_registry/list`
Every defined area in the system.

### `subscribe_events`
Subscribe to event types. Can be useful for building reactive patterns.

```python
send(ws, "subscribe_events", event_type="state_changed")
sub_msg = recv(ws)
sub_id = sub_msg["result"]  # subscription ID
# Events arrive as subsequent ws.recv() messages
```

### `blueprint/list`
List available blueprints for a domain.

```python
send(ws, "blueprint/list", domain="automation")
msg = recv(ws)
# msg["result"] -> {"homeassistant/motion_light.yaml": {...}}
```

### `automation/config`
GET automation config by entity_id. NOT for create/update.

```python
send(ws, "automation/config", entity_id="automation.my_auto")
msg = recv(ws)
# Not found -> msg["error"]["code"] == "not_found"
# Found -> msg["result"] has the full automation config
```

## Commands That DON'T Work

These all return `unknown_command` or `invalid_format` in HA 2026.3.1:

| Command | Error |
|---------|-------|
| `automation/config/create` | unknown_command |
| `automation/config/update` | unknown_command |
| `automation/config/delete` | unknown_command |
| `automation/config/subscribe` | unknown_command |
| `automation/create` | unknown_command |
| `automation/update` | unknown_command |
| `automation/delete` | unknown_command |
| `automation/reload` | unknown_command |
| `recipe/list` | unknown_command |
| `recipe/apply` | unknown_command |
| `blueprint/import` | invalid_format (needs url) |
| `blueprint/create` | unknown_command |
| `config_entries/flow` | unknown_command (WebSocket; use REST instead) |
| `config/automation/*` | unknown_command |

## REST API that Still Works

These REST endpoints complement the WebSocket:

| Endpoint | Method | Use |
|----------|--------|-----|
| `/api/states` | GET | All entity states |
| `/api/services` | GET | All services (same as WebSocket get_services) |
| `/api/config` | GET | HA config (version limited, components list) |
| `/api/config/config_entries/flow` | POST | **Start config flow for adding integrations** |
| `/api/config/config_entries/entry` | GET | List config entries |
| `/api/services/<domain>/<service>` | POST | Call a service |
| `/api/template` | POST | Render a Jinja2 template |
| `/api/conversation/process` | POST | HA Assist (handles entity control only) |
| `/auth/login_flow` | POST | HA login flow (for browser session auth) |
| `/auth/token` | POST | OAuth2 token endpoint |

## Key Takeaway

**There is no programmatic API to create automations in HA 2026.3.1.** The only paths are:
1. Write `automations.yaml` to `/config/` via Samba/SSH/filesystem access
2. Use the HA frontend UI
3. Use Hue/Tradfri bridge-side automations (exposed as `switch` entities)
4. Use Node-RED flows (separate add-on)
