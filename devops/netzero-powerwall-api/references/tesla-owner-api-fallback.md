# Tesla Owner API — Direct Access Fallback

> When NetZero API returns 403 (token expired), or HA Tesla entities show `unavailable`,
> fall back to the Tesla Owner API directly using tokens stored in the local energy dashboard.

## Token Source

Tesla tokens are stored (and periodically refreshed) in:
```
~/energy-dashboard/src/energy_api.py
```

Variables:
- `ACCESS_TOKEN` — JWT bearer token for Tesla Owner API
- `REFRESH_TOKEN` — OAuth refresh token (long-lived)
- `ENERGY_SITE_ID` — Powerwall site ID (e.g. `1689543131745218`)

## Token Refresh Flow

Tesla access tokens expire after ~8 hours. Refresh via OAuth:

```python
import urllib.request, json

refresh_tok = "eyJhbG..."  # from energy_api.py

data = urllib.parse.urlencode({
    "grant_type": "refresh_token",
    "client_id": "ownerapi",
    "refresh_token": refresh_tok,
    "scope": "openid email offline_access",
}).encode()

req = urllib.request.Request(
    "https://auth.tesla.com/oauth2/v3/token",
    data=data, method="POST",
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)
resp = urllib.request.urlopen(req, timeout=15)
body = json.loads(resp.read())
new_token = body["access_token"]
new_refresh = body.get("refresh_token", refresh_tok)  # new refresh token
expires_in = body.get("expires_in", 28800)  # 8 hours
```

## Tesla Owner API Endpoints — GET (Read)

| Endpoint | Method | Returns |
|----------|--------|---------|
| `/api/1/products` | GET | All Tesla products (vehicles + energy sites) with IDs |
| `/api/1/energy_sites/{site_id}/live_status` | GET | Live Powerwall data: battery_power, solar_power, load_power, grid_power, percentage_charged, grid_status, storm_mode_active |
| `/api/1/energy_sites/{site_id}/site_info` | GET | Config: backup_reserve_percent, default_real_mode, storm_mode_enabled, version, grid_services_enabled, components (battery, solar, grid flags + customer_preferred_export_rule) |

## Tesla Owner API Endpoints — POST (Write Configuration)

These endpoints change Powerwall settings directly via the Tesla cloud API (no NetZero, no local gateway needed).

| Endpoint | Body JSON | Description |
|----------|-----------|-------------|
| `POST /api/1/energy_sites/{site_id}/grid_import_export` | `{"grid_export": "battery_ok", "grid_import": true}` | Set energy export rules. `grid_export`: `battery_ok` (solar+battery), `pv_only` (solar only), `never` (no export). The Owner API also accepts `everything` as a value but stores it as `battery_ok`. `grid_import`: `true`/`false` (allow grid charging) |
| `POST /api/1/energy_sites/{site_id}/operation` | `{"default_real_mode": "autonomous"}` | Set operating mode. `autonomous` (Time-Based Control), `self_consumption` (Self-Powered), `backup` |
| `POST /api/1/energy_sites/{site_id}/backup` | `{"backup_reserve_percent": 20}` | Set backup reserve percentage (0–100) |
| `POST /api/1/energy_sites/{site_id}/storm_mode` | `{"enabled": false}` | Enable/disable storm watch participation |

### Python Example — Setting Grid Export

```python
import json, urllib.request, ssl

def api_post(site_id, path, body, access_token):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"https://owner-api.teslamotors.com{path}",
        data=data, method="POST",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    )
    ctx = ssl.create_default_context()
    resp = urllib.request.urlopen(req, context=ctx, timeout=15)
    return json.loads(resp.read())

# Set energy exports to allow battery-to-grid
api_post(SITE_ID, f"/api/1/energy_sites/{SITE_ID}/grid_import_export",
    {"grid_export": "battery_ok", "grid_import": True}, ACCESS_TOKEN)
```

### Verification After Setting

The POST endpoints return `{"response": ""}` on success (empty string — this is normal). Verify the change took effect by checking the relevant field:

- **Grid export:** check `site_info` → `components.customer_preferred_export_rule` → should show `"battery_ok"`, `"pv_only"`, or `"never"`
- **Operating mode:** check `site_info` → `default_real_mode`
- **Backup reserve:** check `site_info` → `backup_reserve_percent`

Note: `energy_exports` is **not** a field in `live_status` response — you must check `site_info.components.customer_preferred_export_rule` to confirm the export setting.

### Sign Convention

| Field | Positive | Negative |
|-------|----------|----------|
| `battery_power` | Charging | Discharging |
| `solar_power` | Generating (always + when sun) | N/A |
| `grid_power` | Importing from grid | Exporting to grid |
| `load_power` | Home consuming (always +) | N/A |

### Export Revenue — Don't Confuse Import and Export Rates

When the Powerwall is exporting to the grid (`grid_power` negative), the revenue earned depends on the **export tariff**, NOT the peak import rate (~31.7p/kWh). Using the import rate gives a wildly inflated figure.

**UK Octopus Energy export rates (March 2026):**
- **Octopus Outgoing Fixed:** **12p/kWh** (reduced from 15p on 1 March 2026)
- **Agile Outgoing:** varies by half-hourly wholesale price
- **SEG minimum:** ~6–7p/kWh (supplier-dependent)

**Correct calculation:**
```
export_earnings_per_hour = abs(grid_kw) × export_rate
Example: 6 kW × 12p = 72p/hour
```

**Pitfall:** Always confirm the user's specific export tariff before quoting earnings. Saying "£1.90/hour" when the real figure is 72p/hour is misleading and wastes trust.

## Common Queries

```bash
# Products (find your energy_site_id)
curl -s -H "Authorization: Bearer $TOKEN" \
  https://owner-api.teslamotors.com/api/1/products | jq '.response[] | select(.energy_site_id)'

# Live status
curl -s -H "Authorization: Bearer $TOKEN" \
  https://owner-api.teslamotors.com/api/1/energy_sites/1689543131745218/live_status \
  | jq '.response | {battery: .battery_power, solar: .solar_power, load: .load_power, grid: .grid_power, percentage: .percentage_charged, grid_status: .grid_status, storm: .storm_mode_active}'

# Site config (read-only check)
curl -s -H "Authorization: Bearer $TOKEN" \
  https://owner-api.teslamotors.com/api/1/energy_sites/1689543131745218/site_info \
  | jq '.response | {reserve: .backup_reserve_percent, mode: .default_real_mode, storm_enabled: .storm_mode_enabled, version: .version}'

# Check export rule (site_info.components, not top-level)
curl -s -H "Authorization: Bearer $TOKEN" \
  https://owner-api.teslamotors.com/api/1/energy_sites/1689543131745218/site_info \
  | jq '.response.components | {export_rule: .customer_preferred_export_rule, net_meter: .net_meter_mode}'

# Set export rule to battery_ok (allows battery-to-grid export)
curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"grid_export": "battery_ok", "grid_import": true}' \
  https://owner-api.teslamotors.com/api/1/energy_sites/1689543131745218/grid_import_export

# Set to self-consumption mode
curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"default_real_mode": "self_consumption"}' \
  https://owner-api.teslamotors.com/api/1/energy_sites/1689543131745218/operation
```

## Diagnosing HA Tesla Integration Downtime

### Tesla Fleet Integration

When HA shows all `sensor.my_home_*` entities as `unavailable` with `restored: true`:

1. The Tesla Fleet API token likely expired (tokens last ~8 hours)
2. The integration in HA needs re-authentication or the token refresh failed
3. **Workaround:** Use the Tesla Owner API directly (as above) for live data
4. **Fix in HA:** Go to Settings → Devices & Services → Tesla Fleet → Re-authenticate
5. **Fix in energy dashboard:** The `energy_api.py` server auto-refreshes tokens on 401 via its `refresh_access_token()` function — check if it's running

### Teslemetry Integration (Third-Party)

Some HA users use the **Teslemetry** integration (third-party Tesla API proxy at teslemetry.com) instead of the official Tesla Fleet integration. The storage path and diagnostics are different:

1. **Check integration state via HA API:** `GET /api/config/config_entries/entry` returns all entries. Look for `"domain": "teslemetry"`. The `state` field may be `"loaded"`, `"setup_error"`, or `"not_loaded"`. A `"reason"` of `"auth_failed_subscription_required"` means the Teslemetry subscription has lapsed.
2. **Teslemetry subscription lapsed** — `auth_failed_subscription_required` means the user's Teslemetry plan expired and needs renewing at teslemetry.com. A stale token is a secondary concern; the subscription itself has expired.
3. **Fix:** User goes to teslemetry.com → renews subscription → then reconfigures the integration in HA (Settings → Devices & Services → Teslemetry → Reconfigure). The HA API does NOT expose a re-auth endpoint for Teslemetry — the user must use the GUI.
4. **API check (no browser needed):**
   ```python
   entries = ha_get("/api/config/config_entries/entry")
   for e in entries:
       if e.get("domain") == "teslemetry":
           print(f"State: {e.get('state')}, Reason: {e.get('reason')}")
           print(f"Supports reconfigure: {e.get('supports_reconfigure')}")
   ```

### Two Token Domains

### Autonomous (Time-Based Control) — Solar Charging vs Grid Export

Counterintuitive but correct: even with `grid_export: battery_ok` in **autonomous** mode during **peak pricing hours**, the Powerwall may **charge from solar** rather than export. This is the algorithm optimising for total economics:

1. Free solar power is available now
2. Charging the battery now stores that energy at zero cost
3. The battery discharges during remaining peak hours, selling at the peak rate
4. More profit than exporting solar immediately

**Do not assume the export setting is broken** when you see `battery_power` negative (charging) and `grid_power` 0 during peak with solar available. The algorithm is working correctly. The battery will discharge when:
- The algorithm determines the economic window closes (end of peak approaches)
- Solar generation drops below house load
- The battery state of charge reaches the algorithm's target

### Switching Modes as a Diagnostic/Trigger

Switching from `autonomous` → `self_consumption` (or back) can trigger the Powerwall to re-evaluate and change its behaviour. This is a useful diagnostic:

```python
# Switch to self_consumption (forces re-evaluation)
api_post(f"/api/1/energy_sites/{site_id}/operation", {"default_real_mode": "self_consumption"})
time.sleep(5)
# Switch back to time-based control
api_post(f"/api/1/energy_sites/{site_id}/operation", {"default_real_mode": "autonomous"})
```

In this session, after switching from `autonomous` to `self_consumption`, the battery immediately started discharging at 1.8kW (it had been charging before). The effect persisted after switching back to `autonomous`.

### Supply > Load Is Required for Grid Export

Grid export (negative `grid_power`) only happens when total supply exceeds house load:

```
solar_power + (battery discharging if positive) > load_power
```

If the house is drawing 3.3kW and solar + battery only supply 3.3kW combined, grid stays at 0W — every watt is consumed locally. To diagnose why nothing is exporting:

1. Check `live_status` for all four values: `solar_power`, `battery_power`, `load_power`, `grid_power`
2. Compute: `excess = solar_power + max(battery_power, 0) - load_power`
3. If `excess` is zero or negative, no export is possible regardless of settings — the house is consuming everything

### Backup Reserve Is a Floor, Not a Ceiling

`backup_reserve_percent` prevents discharging BELOW that level — it does NOT prevent charging ABOVE it. Setting it to match the current SOC (e.g. 54%) does not stop charging. The battery will still charge from solar until the algorithm's target is reached.

### Two Separate Token Domains

The energy dashboard (`~/energy-dashboard/src/energy_api.py`) and the Home Assistant Tesla integration use **independent** Tesla tokens with separate refresh cycles:

| Location | Auth Flow | Token Lifespan | Refresh Mechanism |
|----------|-----------|---------------|-------------------|
| `energy_api.py` | Owner API OAuth tokens hardcoded in file | ~8 hours | Built-in `refresh_access_token()` on 401, or manual via `auth.tesla.com` |
| HA Tesla Fleet integration | Registered through HA UI (OAuth) | ~8 hours | Re-authenticate in HA Settings → Devices & Services |

Refreshing one does NOT fix the other. When HA shows all `sensor.my_home_*` as `unavailable`, check BOTH token sources. The energy dashboard may be fine while HA is stale, or vice versa.

## Pitfalls

- **Timing matters — export doesn't start immediately** — After calling `grid_import_export` with `battery_ok`, the Powerwall may not start exporting right away. It can take several minutes for the algorithm to re-evaluate and begin discharging to grid. Factors include: current SOC, house load, remaining peak duration, and algorithm cycle timing. Don't assume it's broken after 30 seconds — wait and re-check.
- `token expired (401)` — always refresh via OAuth before querying
- The energy dashboard backend auto-refreshes tokens — if the server at `~/dev-site/src/api.py` or the combined server is running, tokens stay fresh
- Tesla API rate limits are generous (~100 req/min) but don't hammer `/live_status` — cache every 5-10 seconds
- `site_info` fields differ per Powerwall version (PW2 vs PW3). `default_real_mode` is the operating mode on PW3; older units may use `operational_mode`
- The Owner API is being deprecated in favour of Fleet API (newer Tesla integrations use this). Fleet API uses a different auth flow. If the Owner API starts returning 410/404, switch to Fleet API.
- **Tokens are redacted from terminal output** — Hermes terminal tool automatically redacts JWT-looking strings from stdout/stderr. You cannot `grep` or `cat` tokens to see them. Instead, write a Python script that reads tokens from the file, does the API work, and writes results back — without ever printing the raw token to stdout. The `execute_code` tool is safer for token operations since its output is not redacted.
- **`energy_exports` is not in `live_status`** — The `live_status` response has NO `energy_exports` field. To verify the export setting, check `site_info.components.customer_preferred_export_rule` and `site_info.components.net_meter_mode`.
- **POST returns empty response on success** — `{"response": ""}` means the setting was applied. Don't panic at the empty string; verify with a subsequent GET to confirm.
- **Grid import/export works with Owner API directly** — You do NOT need NetZero to set `grid_export` or `grid_import`. The Tesla Owner API `grid_import_export` endpoint works with just the site ID and a valid access token. This is useful when the NetZero token is expired or the user doesn't have a NetZero subscription.
