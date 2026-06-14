# Tesla Powerwall Cloud API — Full Reference

*Absorbed from the consolidated `tesla-powerwall-cloud` skill.*

## Auth — Token Refresh

Tokens stored in `~/energy-dashboard/src/api.py`. Refresh via Owner API OAuth:

```python
POST https://auth.tesla.com/oauth2/v3/token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token
&client_id=ownerapi
&refresh_token=<REFRESH_TOKEN>
&scope=openid email offline_access
```

Returns: `access_token`, `refresh_token`, `expires_in: 28800` (8h).
Save both tokens back to the file, update `token_expires = int(time.time()) + expires_in`.

**Pitfall:** Owner API token ≠ Fleet API token. Owner API still serves energy endpoints.

## Key Endpoints

Base: `https://owner-api.teslamotors.com`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/1/energy_sites/{site_id}/live_status` | GET | Current power flows, SOC, storm mode |
| `/api/1/energy_sites/{site_id}/site_info` | GET | Settings, components, battery count, export rules |
| `/api/1/energy_sites/{site_id}/operation` | POST | Set mode: `autonomous` (TBC) or `self_consumption` (SP) |
| `/api/1/energy_sites/{site_id}/backup` | POST | Set `backup_reserve_percent` (0-100) |
| `/api/1/energy_sites/{site_id}/grid_import_export` | POST | Set grid export/import behaviour |

## Grid Import/Export

```json
POST /api/1/energy_sites/{site_id}/grid_import_export
{"grid_export": "battery_ok", "grid_import": true}
```

`grid_export` values:
- `battery_ok` — battery can export during peak (standard TBC)
- `pv_only` — only solar excess exports
- `never` — no export at all
- `everything` — maximum export (may fall back to `battery_ok`)

## Operation Modes

```json
POST /api/1/energy_sites/{site_id}/operation
{"default_real_mode": "autonomous"}
```

- `autonomous` — Time-Based Control. Uses TOU rates. During peak: discharge + export if profitable. Off-peak: may charge from grid.
- `self_consumption` — Self-Powered. Solar → house → battery → export excess. Battery covers house when solar drops, never exports to grid.

## Reading Live Status

```python
live = GET /api/1/energy_sites/{site_id}/live_status
lr = live["response"]
```

Key fields: `solar_power`, `battery_power` (neg=charging, pos=discharging), `grid_power` (pos=importing, neg=exporting), `load_power`, `percentage_charged`, `grid_status`, `storm_mode_active`, `island_status`.

## Export Earnings

```python
earnings_ph = export_kw × rate_p_per_kwh / 100  # £/hour
```

Use the actual export tariff rate (Agile Outgoing or Outgoing Fixed), NOT the peak import rate. Cross-reference with `references/octopus-api.md` for rate data.

## Key Pitfalls

1. Export takes time — Powerwall needs next algorithm cycle. Re-asserting the setting can kick it
2. House load matters — export only happens after covering house + battery charging
3. Storm mode blocks export — check `storm_mode_active` and disable via Tesla app
4. In `self_consumption` mode, battery does NOT export to grid — only solar excess exports once battery is full
5. Sign convention: battery_power negative = CHARGING, grid_power negative = EXPORTING
6. Token expiry — Owner API tokens last ~8h. HA integration token is INDEPENDENT — refreshing one doesn't fix the other
7. HA Tesla integration stuck with `setup_error`? Use the HA energy sensor bridge instead (see `ha-rate-bridge.md`)
