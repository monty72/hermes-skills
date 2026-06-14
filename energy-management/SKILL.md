---
name: energy-management
description: "Integrate with home energy APIs — Tesla Powerwall (Owner/Fleet API) for live status, export/operation control, and Octopus Energy API for tariff rates, consumption data, Agile Outgoing pricing, and Intelligent Octopus Go schedules. For solar/battery homes."
category: devops
tags: [energy, powerwall, tesla, octopus, solar, battery, api, agile, tariff]
---

# Energy Management — Tesla Powerwall & Octopus Energy

## Overview

This umbrella skill covers the two core API integrations for a solar/battery home: **Tesla Powerwall** (cloud API for live status, export control, operation modes, backup reserve) and **Octopus Energy** (tariff rates, Agile/Agile Outgoing pricing, Intelligent Octopus Go schedules, consumption data). These APIs work together — Powerwall export earnings depend on Octopus export rates, and the HA energy bridge combines both data sources.

**Caveat:** A third skill, `uk-energy-research`, covers desktop research on the UK energy market (suppliers, VPPs, installer directories) and is NOT absorbed here — it's a research skill, not an API integration skill.

## Sections at a Glance

| Section | Reference File | Covers |
|---------|---------------|--------|
| 1. Tesla Powerwall Cloud API | `references/tesla-powerwall-api.md` | Auth/token refresh, live_status, grid import/export, operation modes (autonomous/self_consumption), backup reserve |
| 2. Octopus Energy API | `references/octopus-api.md` | Auth (API key), product discovery, tariff codes, Agile/Agile Outgoing rates, Intelligent Octopus Go, consumption data, account info |
| 3. Octopus — HA Integration | `references/octopus-api.md#home-assistant-integration-preferred-vs-bridge-script` | Native HA integration vs REST API bridge script |
| 4. Cross-Reference — Earnings Calculation | See §1 + §2 | Export earnings = export_kW × rate(p/kWh) / 100 £/h. Use Agile Outgoing or Outgoing Fixed rate. |
| 5. React Native Mobile App | `references/react-native-integration.md` | Build a mobile energy dashboard: Expo setup, Octopus/NetZero in-app patterns, Base64 auth in Hermes, tab navigation, mock data |

## Mobile App Integration (React Native / Expo)

When building a mobile energy dashboard app that integrates Tesla Powerwall (via NetZero API) and Octopus Energy, several React Native-specific patterns apply:

1. **No `btoa()` in Hermes** — Octopus Basic Auth needs a manual Base64 implementation
2. **Text in `<Text>`** — all text content must be in `<Text>` components, not `<View>`
3. **`react-native-screens` version lock** — 4.24.0 for RN 0.76/0.81 compatibility
4. **Configurable tariff codes** — never hardcode the user's Octopus tariff codes
5. **Surface API errors visibly** — red banners, not silent catch/empty-returns
6. **Mock data fallback** — return mock data when unconfigured so the UI is navigable

See `references/react-native-integration.md` for the full implementation guide: auth patterns, tariff discovery, tab navigation, NetZero vs Tesla API fallback, async data loading with pull-to-refresh, and cost calculation cards.

### Mobile-Specific Pitfalls

- **`btoa()` silently fails** — Hermes lacks it. Any API using HTTP Basic Auth (Octopus) needs manual Base64. Test with a "Test Connection" button before relying on tariff data.
- **API errors must be user-visible** — silent `try/catch` with empty returns leaves the user thinking "nothing works". Always show the error in a red banner and provide a test button in Settings.
- **Tariff codes are user-specific** — IOG, Agile, Go, and Outgoing all have different product/tariff codes. Make them editable in Settings with sensible defaults, not hardcoded.
- **NetZero `/config` nests `live_status`** — one call returns both config (backup reserve, mode) and live data (solar, battery, grid) in a single response.

## Quick Reference — Auth

### Tesla Powerwall (Owner API)
```python
# Token refresh
POST https://auth.tesla.com/oauth2/v3/token
grant_type=refresh_token&client_id=ownerapi&refresh_token=<TOKEN>&scope=openid email offline_access
# Returns: access_token (8h expiry), refresh_token
```

### Octopus Energy
```bash
# HTTP Basic Auth with API key as username, empty password
Authorization: Basic $(echo -n "sk_live_...:" | base64)
```
API keys are long-lived (get from https://octopus.energy/dashboard/developer/).

## Energy Balance Equation

For a Powerwall home: `solar_power + battery_power + grid_power ≈ load_power`

| Field | Sign Convention |
|-------|----------------|
| `solar_power` | Positive = generating |
| `battery_power` | Negative = charging, Positive = discharging |
| `grid_power` | Positive = importing, Negative = exporting |
| `load_power` | Positive = house consuming |

Difference of 0-50W is normal (measurement noise/Powerwall internal consumption).

## Key Pitfalls

1. **Tesla Owner API tokens last ~8 hours** — auto-refresh needed. HA Tesla integration token is INDEPENDENT of the energy dashboard token
2. **Storm mode blocks export** — if `storm_mode_active` is true, battery charges to 100% and stops exporting
3. **Export takes time** — Powerwall needs an algorithm cycle; re-asserting the setting can kick it
4. **Mode matters** — `self_consumption` = battery covers house, solar excess only exports. `autonomous` = Time-Based Control, battery can export to grid
5. **Octopus API times are UTC** — convert to local time (BST = UTC+1)
6. **Agile rates change daily** — published ~16:00 for next day. 48 half-hour slots per day
7. **Agile Outgoing ≠ Outgoing Octopus** — Agile is variable half-hourly; Outgoing Fixed is 12p/kWh flat rate
8. **Smart meter consumption data is delayed** (6-24h) — use live Tesla data for real-time, Octopus for daily totals
9. **Date format in Octopus API** — must use `Z` suffix (`2026-05-26T00:00:00Z`), not `+00:00`
10. **Results are newest-first** — always reverse for chronological display

## Reference Files

- `references/tesla-powerwall-api.md` — Full Tesla Owner API reference: endpoints, token management, grid export settings, operation modes, backup reserve, export earnings calculation
- `references/octopus-api.md` — Full Octopus Energy API reference: product discovery, tariff codes, Agile/Intelligent rates, region table, consumption data, HA integration options
- `references/ha-rate-bridge.md` — Bridge script for Octopus rates → HA sensors (from absorbed octopus-energy skill)
- `references/owner-api-endpoints.md` — Tesla endpoint details (from absorbed tesla-powerwall-cloud skill)
- `references/api-reference.md` — Additional Octopus API details (from absorbed octopus-energy skill)
- `references/react-native-integration.md` — Building a React Native mobile energy dashboard: Octopus + NetZero API integration patterns, Base64 auth in Hermes (no btoa()), react-native-screens version compatibility, tab navigation with expo-router, mock data fallback
