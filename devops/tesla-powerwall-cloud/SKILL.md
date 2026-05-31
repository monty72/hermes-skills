---
name: tesla-powerwall-cloud
description: Manage Tesla Powerwall via the Tesla Owner API / Fleet API (cloud, not local gateway). Covers token refresh, export settings, operation modes, backup reserve, and live status polling.
category: devops
---

# Tesla Powerwall — Cloud API

Manage Tesla Powerwall export and operation settings via `owner-api.teslamotors.com` (the legacy Owner API, which still works for most energy endpoints).

## When to use

- User asks to change Powerwall export behaviour (grid export on/off/battery_ok)
- User asks to switch between Time-Based Control and Self-Powered modes
- User asks to change backup reserve percentage
- User asks to refresh expired Tesla API tokens
- User asks why the Powerwall isn't exporting / why grid reading is 0
- User asks to check current Powerwall live status

## Auth — Token Refresh

Tokens are stored inline in the energy dashboard file (e.g. `~/energy-dashboard/src/api.py`).

```python
# Refresh flow (Owner API OAuth)
POST https://auth.tesla.com/oauth2/v3/token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token
&client_id=ownerapi
&refresh_token=<REFRESH_TOKEN>
&scope=openid email offline_access
```

Returns: `{"access_token": "...", "refresh_token": "...", "expires_in": 28800}`

Save both tokens back to the file, and update `token_expires` timestamp (`int(time.time()) + expires_in`).

**Pitfall:** The Owner API token is separate from the Fleet API token. The Owner API still serves energy endpoints even though it's technically deprecated. Use `owner-api.teslamotors.com` as the base URL.

## Key Endpoints

All calls use `Authorization: Bearer <access_token>`.

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/1/energy_sites/{site_id}/live_status` | GET | Current power flows, SOC, storm mode, island status |
| `/api/1/energy_sites/{site_id}/site_info` | GET | Settings, components, battery count, tariff config, export rules |
| `/api/1/energy_sites/{site_id}/operation` | POST | Set mode: `autonomous` (Time-Based Control) or `self_consumption` (Self-Powered) |
| `/api/1/energy_sites/{site_id}/backup` | POST | Set `backup_reserve_percent` (0-100) |
| `/api/1/energy_sites/{site_id}/grid_import_export` | POST | Set grid export/import behaviour |

## Grid Import/Export

```json
POST /api/1/energy_sites/{site_id}/grid_import_export
{"grid_export": "battery_ok", "grid_import": true}
```

Grid_export values:
- `battery_ok` — battery can export during peak (standard Time-Based Control behaviour)
- `pv_only` — only solar excess exports (battery never exports)
- `never` — no export at all
- `everything` — maximum export (accepted by API but may fall back to `battery_ok` on some API versions — confirm via `site_info.components.customer_preferred_export_rule` after setting)

`grid_import` values:
- `true` — allow importing from grid
- `false` — disallow grid import (island mode)

## Operation Modes

```json
POST /api/1/energy_sites/{site_id}/operation
{"default_real_mode": "autonomous"}
```

- `autonomous` — Time-Based Control. Uses TOU rates to optimise charge/discharge. During peak, will discharge battery to cover house AND export if profitable. During off-peak, may charge from grid.
- `self_consumption` — Self-Powered mode. Solar → house → battery charge → export excess. Battery only discharges to cover house when solar drops, never exports to grid.

## Backup Reserve

```json
POST /api/1/energy_sites/{site_id}/backup
{"backup_reserve_percent": 0}
```

Range: 0-100. 0% means battery can discharge fully. Setting close to current SOC tells the system "keep this level for backup, export the rest."

## Reading Live Status

```python
live = GET /api/1/energy_sites/{site_id}/live_status
lr = live["response"]
```

Key fields:

| Field | Sign Convention |
|---|---|
| `solar_power` | Positive = generating |
| `battery_power` | **Negative = charging** (absorbing power). **Positive = discharging** (supplying power) |
| `grid_power` | **Positive = importing from grid. Negative = exporting to grid.** Zero = neutral |
| `load_power` | Positive = house consuming |
| `percentage_charged` | Battery state of charge (0-100) |
| `grid_status` | "Active" = grid-connected |
| `storm_mode_active` | True = storm watch engaged (prevents export) |
| `island_status` | "on_grid" or "islanded" |

**Balance equation:** `solar_power + battery_power + grid_power = load_power`

A non-zero difference in the balance equation (solar + battery + grid - load) indicates measurement noise or internal Powerwall consumption, not a bug. Differences of 0-50W are normal.

## Export Earnings

When the Powerwall is exporting to grid, calculate earnings with:

```
earnings_ph = export_kw × rate_p_per_kwh / 100  # £/hour
```

The rate depends on the user's export tariff:
- **Agile Outgoing** — variable half-hourly rates (see `octopus-energy` skill)
- **Outgoing Fixed** — flat rate (e.g. 12p/kWh from March 2026)
- **SEG** — Smart Export Guarantee rate

Cross-reference: For Octopus Agile Outgoing rates, consumption data, and billing, see the `octopus-energy` skill.

## Site Info — Key Settings

```python
info = GET /api/1/energy_sites/{site_id}/site_info
si = info["response"]
comp = si["components"]
```

- `comp.customer_preferred_export_rule` — current export setting
- `comp.net_meter_mode` — net metering mode
- `si.default_real_mode` — current operation mode
- `si.backup_reserve_percent` — current reserve
- `comp.grid_services_enabled` — VPP participation (not general export)
- `comp.edit_setting_energy_exports` — whether export can be changed via API

## Cross-References

- **Export earnings calculation:** For live export rate data and earnings (£/h), see the `octopus-energy` skill — it covers Agile Outgoing rates, fixed Outgoing Octopus, and HA sensor bridging.
- **Energy dashboard:** For the combined dashboard + HA bridge architecture, see the `tesla-energy-dashboard` skill.
- **Local gateway:** For local (LAN-based) Powerwall control without cloud tokens, see the `tesla-powerwall-local` skill.

## Pitfalls

1. **Export takes time.** After changing `grid_import_export`, the Powerwall may not immediately start exporting. It needs the next algorithm cycle. Re-asserting the setting can help kick it.
2. **House load matters.** The Powerwall only exports excess power after covering the house load and battery charging. If house load > solar + battery, nothing exports regardless of settings.
3. **Storm mode blocks export.** If `storm_mode_active` is true, the battery will charge to 100% and stop exporting. Check and disable storm mode via the Tesla app or the `storm_mode` endpoint.
4. **Mode matters.** In `self_consumption` mode, battery discharges to cover house load but does NOT export to grid. Only solar excess exports (once battery is full). For battery-to-grid export, use `autonomous` mode.
5. **Sign convention confusion.** Newcomers frequently misread `battery_power` — negative is CHARGING, positive is DISCHARGING. Grid power follows the same logic: negative = exporting.
6. **Token expiry.** Owner API tokens last ~8 hours. The energy dashboard's auto-refresh may need a fresh refresh token if the old one also expired.
7. **Home Assistant separate token.** HA's Tesla/Teslemetry integration has its own token separate from the energy dashboard. Refreshing one does NOT refresh the other. If the HA Tesla/Teslemetry integration is stuck with `setup_error` / `auth_failed_subscription_required`, it's usually a lapsed Teslemetry subscription or stale HA token.
   - **Workaround:** Use the HA energy sensor bridge (see `tesla-energy-dashboard` skill → `references/ha-energy-bridge.md`) to bypass the failed integration entirely. Create REST sensors from your local energy API instead.
8. **Export timing is algorithm-dependent.** The Powerwall's Time-Based Control algorithm decides WHEN to export based on TOU rates, battery SOC, and expected solar. Setting export mode to `battery_ok` doesn't force immediate discharge — it just permits it.
   - **Kick technique:** If export hasn't started after 2-3 minutes, re-assert the same `POST /api/1/energy_sites/{site_id}/grid_import_export` with `{"grid_export": "battery_ok"}`. Re-sending the identical setting can force the algorithm to re-evaluate.
   - **Mode toggle:** Switching briefly (e.g. `self_consumption` → `autonomous`) can also nudge the algorithm.
9. **Export earnings — use the correct rate.** Calculate with the ACTUAL export tariff rate (e.g. Agile Outgoing), NOT the peak import rate. Common mistake: quoting £1.90/h at 31.7p import rate when the export rate is ~14p → ~62p/h. Cross-reference via `octopus-energy` skill.
