# Octopus Energy API — Full Reference

*Absorbed from the consolidated `octopus-energy` skill.*

## Authentication

HTTP Basic Auth: API key as username, empty password.
```python
import base64
auth_str = base64.b64encode(f"{API_KEY}:").decode().decode()
headers = {"Authorization": f"Basic {auth_str}"}
```
API key format: `sk_live_...` (get from octopus.energy/dashboard/developer/). **Long-lived** — store securely.

## Product Discovery

```text
GET /v1/products/
```
Each product has `code` (e.g. `AGILE-OUTGOING-19-05-13`), `display_name`, `direction` (`EXPORT`/`IMPORT`), `brand`.

Filter by `direction: "EXPORT"` for solar/battery export tariffs.

## Account Discovery

```text
GET /v1/accounts/{account_number}/
```
Account numbers start with `A-`. Response has `properties[]` with `mpan`, `electricity_meters[].serial_number`, `electricity_meters[].agreements[].tariff_code`. Export vs import: `is_export` field on each meter point.

## Tariff Codes & Regions

Format: `E-1R-AGILE-OUTGOING-19-05-13-{REGION_LETTER}`

| Code | Region |
|------|--------|
| A | Eastern England |
| B | East Midlands |
| C | London |
| ... M | Yorkshire |
| P | North Scotland |

**Determine region from the user's actual tariff agreement.**

## Fetching Rates

```text
GET /v1/products/{product_code}/electricity-tariffs/{tariff_code}/standard-unit-rates/
  ?period_from=2026-05-26T00:00:00Z&period_to=2026-05-27T00:00:00Z
```

**Date format:** MUST use `Z` suffix, NOT `+00:00`. Returns 400 for non-Z formats.

**Response ordering: REVERSE CHRONOLOGICAL** (newest first). Always reverse for chronological display:
```python
results = list(data.get("results", []))
results.reverse()  # Now oldest → newest
```

**Times are UTC.** Convert to local time:
```python
def local_time(utc_dt):
    is_dst = time.localtime().tm_isdst
    return utc_dt + timedelta(hours=1 if is_dst else 0)
```

## Product Codes

- `AGILE-OUTGOING-19-05-13` — Agile Outgoing (export)
- `AGILE-24-10-01` — Agile Octopus (import)
- `OUTGOING-VAR-24-10-26` — Outgoing Octopus fixed (12p/kWh as of March 2026)
- `INTELLI-FIX-12M-26-03-17` — Intelligent Octopus Go (import)

## Intelligent Octopus Go — Import Rates

Single-register tariff, but `standard-unit-rates` returns alternating peak/off-peak blocks:
- Peak: ~31.66p/kWh (05:30-23:30 BST)
- Off-peak: ~5.49p/kWh (23:30-05:30 BST)
- Standing charge: ~60.41p/day

Detection: `is_offpeak = (hour_utc >= 22.5) or (hour_utc < 4.5)`

### Standing Charges
```text
GET /v1/products/{product_code}/electricity-tariffs/{tariff_code}/standing-charges/
```

## Consumption Data

```text
GET /v1/electricity-meter-points/{mpan}/meters/{serial_number}/consumption/
```
Requires MPAN (starts with 23...) and meter serial from account data. **Data is delayed 6-24h.**

## HA Sensor Bridge

### Option A: Native HA Integration (Preferred)
Install BottlecapDave Octopus Energy custom_component via SSH (`ha-component-deployment` reference). Gives 30+ sensors with auto-refresh.

### Option B: REST API Bridge
Create sensors via `POST /api/states/{entity_id}`:
```python
{"state": str(value), "attributes": {
    "unit_of_measurement": "p/kWh",
    "friendly_name": "Export Rate",
    "icon": "mdi:cash",
}}
```

**Key sensors:** `sensor.energy_export_rate`, `sensor.energy_earning_rate`, `sensor.energy_import_rate`, `sensor.energy_standing_charge`.

See `references/ha-rate-bridge.md` for the full bridge implementation.

## Key Pitfalls

1. **Date format:** MUST use `Z` suffix. No other timezone format accepted
2. **Region detection:** Extract from actual tariff code, not assumed
3. **Results newest-first:** Always reverse for chronological display
4. **Times are UTC:** Convert to local time (BST = UTC+1)
5. **Agile Outgoing ≠ Outgoing Octopus:** Variable half-hourly vs fixed 12p/kWh
6. **Agile rates change daily:** 48 half-hour slots, published ~16:00 for next day
7. **API keys don't expire:** Store securely in vault
8. **Standard unit rate ≠ Agile rate:** The product's `standard_unit_rate_inc_vat` is a comparison figure, not the actual variable rate
9. **Single-register ≠ single rate:** Intelligent Go has peak/off-peak despite being single-register
10. **Consumption data delayed:** Use live Tesla data for real-time values
