---
name: ha-component-deployment
description: Install and configure Home Assistant custom_components remotely — SSH into HAOS, download from GitHub, restart core, and set up via config flow API. For when HACS isn't available or you need to deploy a component programmatically.
category: devops
---

# Home Assistant — Custom Component Deployment

Install HA custom_components on a remote HAOS machine and configure them via the REST API config flow. Covers the full lifecycle: SSH access, component download, HA restart, and config entry creation.

## When to use

- User asks to install an integration not available via HACS (or HACS isn't installed)
- User wants to configure an integration programmatically without using the HA GUI
- User has given you SSH access to their HA machine
- User's HA has a broken integration that needs replacing (e.g. Teslemetry → Octopus Energy)

## Prerequisites

1. **SSH access** to the HA machine (typically `root@<ha-ip>`, HAOS accepts SSH keys)
2. **HA long-lived access token** for the REST API (`HASS_TOKEN`) — in `~/.hermes/.env` as `HASS_TOKEN=...`
3. **HA URL** — typically `http://<ha-ip>:8123`

### Getting SSH Access

Add your SSH public key to the HA machine's `authorized_keys`:

```bash
# User runs this on the HA machine (terminal add-on, SSH, or direct console):
echo 'ssh-ed25519 AAAAC3... matth@Hermes' >> ~/.ssh/authorized_keys
```

Verify access:
```bash
ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=5 -o BatchMode=yes root@<ha-ip> "echo CONNECTED && uname -a"
```

## Step 1 — Identify the Integration

Find the GitHub repo for the HA custom_component. The integration must have:
- A `custom_components/<domain>/` directory in the repo
- A `manifest.json` with `"domain": "...", "config_flow": true` (for configurable integrations)

## Step 2 — Download and Install via SSH

```bash
ssh root@<ha-ip> "
cd /config

# Download the source from a GitHub release tag
wget -q -O component.zip 'https://github.com/{owner}/{repo}/archive/refs/tags/v{version}.zip'

# Unzip and find the custom_components folder
unzip -q component.zip
ls {repo}-*/custom_components/  # Should show the domain folder

# Copy to HA custom_components
cp -r {repo}-*/custom_components/{domain} custom_components/

# Verify
ls custom_components/{domain}/manifest.json

# Cleanup
rm -rf component.zip {repo}-*/
echo 'Integration installed'
"
```

**If the release has pre-built assets** (zip file in GitHub releases), use:
```bash
wget -q -O octopus_energy.zip 'https://github.com/{owner}/{repo}/releases/download/v{version}/octopus_energy.zip'
```

Most HA custom_components distribute via source only (no release assets). Use the archive method above.

**Check manifest.json manually** after install to confirm:
```bash
ssh root@<ha-ip> "cat /config/custom_components/{domain}/manifest.json"
```

## Step 3 — Restart Home Assistant

After installing files, restart HA core to register the new integration:

```bash
# Via SSH (HA CLI)
ssh root@<ha-ip> "ha core restart"

# Via REST API
POST /api/services/homeassistant/restart
Authorization: Bearer ${HASS_TOKEN}
```

Wait for HA to come back. Poll by checking the API:
```bash
for i in $(seq 1 30); do
  result=$(curl -s -o /dev/null -w "%{http_code}" http://<ha-ip>:8123/api/ 2>/dev/null)
  if [ "$result" = "200" ] || [ "$result" = "401" ]; then
    echo "HA is back!"
    break
  fi
  sleep 2
done
```

401 at `/api/` is expected (requires auth) — it means HA is running.

## Step 4 — Configure via Config Flow API

After restart, the integration is loaded but not configured. Create a config entry via HA's config flow API.

### 4a. Start the Flow

```python
POST /api/config/config_entries/flow
{
  "handler": "{domain}",
  "show_advanced_options": false
}
```

Returns a `flow_id` and `data_schema` describing the fields to submit.

### 4b. Submit the Form

The schema tells you what fields are expected. Common field types:
- `"type": "string"` — text input
- `"type": "boolean"` — toggle
- `"type": "float"` — number (may have `valueMin`, `default`)
- `"type": "expandable"` — nested section with sub-fields

**Crucial:** Expandable sections are often `"required": true` even when visually collapsed. You MUST provide all expandable sections in the POST body, even if their inner fields are optional:

```python
POST /api/config/config_entries/flow/{flow_id}
{
  "api_key": "sk_live_...",
  "account_id": "A-A6E7949D",
  "some_float": 40.0,
  "favour_direct_debit_rates": True,
  "home_mini_settings": {           # Expandable — required!
    "supports_live_consumption": False,
    "live_electricity_consumption_refresh_in_minutes": 1,
  },
  "intelligent_settings": {          # Expandable — required!
    "intelligent_manual_dispatches": False,
  },
  "home_pro_settings": {},           # Expandable — empty if no optional fields
  "price_cap_settings": {},          # Expandable — empty if no optional fields
}
```

If you omit an expandable section, the API returns 400 with `"required key not provided"`.

### 4c. Handle Follow-up Steps

Some flows have multiple steps (e.g. first the account form, then an intelligent tariff configuration). Check the response `type`:

- `"type": "form"` — another step needed, check `step_id`
- `"type": "create_entry"` — ✅ Done! Integration is configured

### 4d. Handle Errors

- **400 with `"required key not provided"`** — you omitted an expandable section or a required top-level field
- **404 on `/reconfigure`** — the re-auth endpoint is not programmatically accessible; user must use GUI
- **500 on `/services/homeassistant/restart`** — try `ha core restart` via SSH instead

## Step 5 — Verify

```python
POST /api/config/config_entries/entry
GET /api/config
```

Check that the entry has `"state": "loaded"`. The new sensors should appear in the entity registry:

```python
# List all sensors
GET /api/states
# Filter for your domain
sensors = [s for s in states if "{domain}" in s.get("entity_id", "")]
```

Errors at this stage:
- **State: `setup_error`** — the integration loaded but couldn't connect. Check `reason` field for details.
- **All sensors show `unknown`** — the integration is configuring but hasn't finished its first data poll yet. Wait 1-2 minutes and re-check.
- **Integration not in entries at all** — HA didn't pick it up. The manifest or file structure may be incorrect.

## Pitfalls

1. **GitHub releases may not have assets.** Most HA custom_components distribute via source only. Use the archive URL pattern: `https://github.com/{owner}/{repo}/archive/refs/tags/v{version}.zip` — NOT the release asset URL (which 404s if no asset was uploaded).

2. **Expandable sections are required.** Even though they look optional in the config flow UI (visually collapsed), the API requires them. Always include all expandable sections in the POST body, with `{}` for sub-sections that have no fields you want to set.

3. **HA restart may fail via API.** `POST /api/services/homeassistant/restart` returns HTTP 500 intermittently. Use `ssh root@<ha-ip> "ha core restart"` as fallback.

4. **Restart can take 30-60 seconds.** The HA "command timed out" doesn't mean it failed. Wait and poll for recovery.

5. **Config flow IDs are single-use.** Each attempt starts a NEW flow. You cannot retry a failed step on the same flow_id — start fresh.

6. **Cross-reference energy data.** When setting up an Octopus Energy or Tesla integration, the live power data (from the energy dashboard bridge) and the Octopus consumption/rate data serve different purposes. Don't confuse them:
   - `energy_*` sensors (from `ha_energy_bridge` cron) = **live Tesla Powerwall data** (instant power flows)
   - `octopus_energy_*` sensors (from native integration) = **Octopus tariff rates + daily consumption** (delayed)

7. **HASS_TOKEN may have trailing whitespace.** Read it with `.strip()` to avoid `"Invalid header value"` errors in curl/Python:
   ```python
   hass_token = line.split("=", 1)[1].strip()
   ```

8. **No need to remove old/broken integrations programmatically.** When replacing a failed integration (e.g. Teslemetry), a core restart often cleans up stale entries. If not, delete via `DELETE /api/config/config_entries/entry/{entry_id}` — but check the entry exists first; it may already be gone after restart.

## Cross-References

- **Add-ons:** For installing HA add-ons (Docker-based supervisor apps like Studio Code Server, Node-RED, ESPHome, Zigbee2MQTT, Samba), see `ha-addon-management`
- **HACS frontend cards:** For deploying Lovelace UI cards (Power Flow Card, ApexCharts, Mushroom), see `ha-addon-management`
- **Energy dashboard bridge:** For creating live Tesla Powerwall sensors in HA via cron + REST API, see `tesla-energy-dashboard` → `references/ha-energy-bridge.md`
- **Octopus Energy integration:** For Octopus-specific config flow parameters (account ID, API key, intelligent settings), see the `octopus-energy` skill
- **HA API basics:** For general HA REST API usage (entity state management, service calls), see `tesla-energy-dashboard` → `references/ha-energy-bridge.md`
