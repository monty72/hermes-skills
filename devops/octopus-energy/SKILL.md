---
name: octopus-energy
description: Integrate with the Octopus Energy API — account discovery, Agile/Agile Outgoing rates, tariff codes, regional pricing, consumption data, and Home Assistant sensor bridging.
category: devops
---

# Octopus Energy API

Integrate with `api.octopus.energy/v1` for tariff rates, account info, consumption, and billing data.

## When to use

- User asks about current Agile Outgoing / Agile import rates
- User wants to check their Octopus tariff, MPAN, meter serial, or account info
- User asks how much they're earning from solar/battery exports
- User wants to calculate export earnings in real time
- User shares their Octopus API key

## Authentication

HTTP Basic Auth with the API key as the username and empty password:

```python
import base64
auth_str = base64.b64encode(f"{API_KEY}:").encode().decode()
headers = {"Authorization": f"Basic {auth_str}"}
```

API key format: `sk_live_...` (get from [octopus.energy/dashboard/developer/](https://octopus.energy/dashboard/developer/))

## Product Discovery

List all available products to find the right tariff code:

```
GET /v1/products/
```

Each product has:
- `code` — e.g. `AGILE-OUTGOING-19-05-13`
- `display_name` — e.g. "Agile Outgoing Octopus"
- `direction` — `"EXPORT"` or `"IMPORT"` (critical for distinguishing import vs export tariffs)
- `brand` — e.g. `OCTOPUS_ENERGY`
- `available_from` / `available_to` — date range
- `single_register_electricity_tariffs` — nested dict keyed by region code (`_A`, `_B`, etc.)

**Filter by direction:** When the user has solar/battery exports, look for products with `direction: "EXPORT"`. Products with `direction: "IMPORT"` are consumption tariffs (not what you want for export rate queries).

## Account Discovery

```
GET /v1/accounts/{account_number}/
```

Account numbers start with `A-` (e.g. `A-A6E7949D`).

Response contains `properties[]`, each with:
- `mpan`: Meter Point Administration Number
- `electricity_meters[].serial_number`: Meter serial
- `electricity_meters[].agreements[]`: Tariff history
  - `tariff_code`: e.g. `E-1R-AGILE-OUTGOING-19-05-13-M`
  - `valid_from` / `valid_to`: Date range
- `is_export`: true for export MPAN, false for import

**Export vs Import:** A property may have two meter points — one for import consumption and one for export. The `is_export` field distinguishes them.

## Tariff Codes & Regions

Agile Outgoing tariff format: `E-1R-AGILE-OUTGOING-19-05-13-{REGION_LETTER}`

Region letters (UK electricity distribution zones):

| Code | Region |
|---|---|
| A | Eastern England |
| B | East Midlands |
| C | London |
| D | Merseyside & North Wales |
| E | West Midlands |
| F | North Eastern England |
| G | North Western England |
| H | Southern England |
| J | South Eastern England |
| K | South Wales |
| L | South Western England |
| M | Yorkshire |
| N | South & Central Scotland |
| P | North Scotland |

**Determine the region from the tariff code:** Look for the suffix letter on the user's current tariff agreement from their account data.

## Fetching Rates

```
GET /v1/products/{product_code}/electricity-tariffs/{tariff_code}/standard-unit-rates/?period_from={from_date}Z&period_to={to_date}Z
```

**Date format:** Must use ISO 8601 with `Z` suffix (e.g. `2026-05-26T00:00:00Z`). The `+00:00` format is rejected with a 400 error.

**Response ordering:** ⚠️ The API returns results in **reverse chronological order** (newest first). The most recent half-hour slot is at index 0. When building a chronological display (e.g. "coming up tonight" list), you MUST reverse the result list:

```python
results = list(data.get("results", []))
results.reverse()  # Now chronological: oldest → newest
```

**UTC timestamps:** All `valid_from` / `valid_to` values are in UTC (suffixed with `Z`). For UK users, convert to local time (BST = UTC+1 in summer, GMT = UTC+0 in winter):

```python
def local_time(utc_dt):
    is_dst = time.localtime().tm_isdst
    offset = timedelta(hours=1) if is_dst else timedelta(hours=0)
    return utc_dt + offset
```

Displaying UTC times without conversion will be off by one hour during BST.

**Product codes:**
- `AGILE-OUTGOING-19-05-13` — Agile Outgoing (export)
- `AGILE-24-10-01` — Agile Octopus (import)
- `AGILE-FLEX-22-11-25` — Older Agile import
- `OUTGOING-VAR-24-10-26` — Outgoing Octopus fixed rate (12p/kWh from March 2026)
- `INTELLI-FIX-12M-26-03-17` — Intelligent Octopus Go (import)

**Response:** Paginated results with `count` and `results[]`, each containing:
- `value_inc_vat`: Rate including VAT (prefer this)
- `value_exc_vat`: Rate excluding VAT
- `valid_from`: Start of half-hour slot (ISO 8601)
- `valid_to`: End of half-hour slot (ISO 8601)

There are 48 half-hour slots per day.

## Intelligent Octopus Go — Import Rates

Even though Intelligent Octopus Go is a "single register" tariff, the `standard-unit-rates` endpoint returns BOTH peak and off-peak rates as alternating blocks spanning multiple days. Each result has a `valid_from`/`valid_to` pair defining the block:

**Region M (Yorkshire) example:**

| Time (BST) | Rate | Period |
|---|---|---|
| 05:30-23:30 | **31.66p/kWh** | Peak |
| 23:30-05:30 | **5.49p/kWh** | Off-peak |
| Standing charge | **60.41p/day** | Constant |

The pattern repeats daily. To determine the current rate in code:

```python
hour_utc = now.hour + now.minute / 60
is_offpeak = (hour_utc >= 22.5) or (hour_utc < 4.5)  # 22:30-04:30 UTC = 23:30-05:30 BST
current_import_rate = import_offpeak_rate if is_offpeak else import_peak_rate
```

### Standing Charges

Fetch separately:

```
GET /v1/products/{product_code}/electricity-tariffs/{tariff_code}/standing-charges/
```

Returns a single result with `value_inc_vat` (p/day) and `valid_from`/`valid_to`.

## Listing Products

```
GET /v1/products/
```

Returns all available products with their `code`, `display_name`, `direction` ("IMPORT" or "EXPORT"), `brand`, and tariff structures in nested objects.

The product detail endpoint (`/v1/products/{code}/`) reveals:
- `single_register_electricity_tariffs` — dict keyed by region code (`_A`, `_B`, etc.)
- Each region has `direct_debit_monthly` with tariff code, standing charge, and standard unit rate (used for comparison, not the actual Agile rates)

## Consumption Data

```
GET /v1/electricity-meter-points/{mpan}/meters/{serial_number}/consumption/
```

Requires the MPAN (starting with 23...) and meter serial number from account data.

## Home Assistant Integration (Preferred) vs Bridge Script

### Option A: Native HA Integration (Preferred)

Install the official BottlecapDave Octopus Energy custom_component. This gives you 30+ sensors, cost tracking, intelligent tariff support, and automatic data refresh — all without a cron job.

**Install:** See the `ha-component-deployment` skill for SSH-based custom_component installation and config flow setup.

The integration handles:
- Import/export rates (Agile Outgoing, Intelligent Go, etc.)
- Previous-day consumption and cost
- Standing charges
- Off-peak detection (`binary_sensor.*_off_peak`)
- Octoplus points and saving sessions
- Gas rates (if applicable)
- Intelligent tariff dispatch support

### Option B: REST API Bridge (Fallback)

When the native integration can't be installed (no SSH access, HACS unavailable), create sensors via the HA REST API. Use `POST /api/states/{entity_id}` with:

```python
{"state": str(value), "attributes": {
    "unit_of_measurement": "p/kWh",
    "friendly_name": "Export Rate",
    "icon": "mdi:cash",
    "tariff": "Agile Outgoing",
    "region": "M - Yorkshire"
}}
```

### Sensors to Create

**Export (Agile Outgoing) sensors:**
- `sensor.energy_export_rate` — Current export rate (p/kWh)
- `sensor.energy_earning_rate` — Earnings per hour (£/h)
- `sensor.energy_slot_earnings` — Earnings for current half-hour slot (£)
- `sensor.energy_agile_schedule` — Today's full rate schedule

**Import (Intelligent Octopus Go) sensors:**
- `sensor.energy_import_rate` — Current import rate (p/kWh), with `peak_rate`, `offpeak_rate`, `period` attributes
- `sensor.energy_standing_charge` — Daily standing charge (p/day)

**Consumption sensors (from Octopus smart meter data — may be delayed):**
- `sensor.energy_today_export_kwh` — Today's metered export (kWh)
- `sensor.energy_today_import_kwh` — Today's metered import (kWh)
- `sensor.energy_today_earnings` — Today's estimated export earnings (£)
- `sensor.energy_today_import_cost` — Today's estimated import cost (£)

Put the bridge script in `~/.hermes/scripts/` and use a `no_agent=True` cron job running `every 1m`.

> For the complete bridge implementation (Octopus rates → HA sensors), including timezone handling, API response ordering, earnings calculations, and consumption sensors, see `references/ha-rate-bridge.md`.

**Pitfalls**

1. **Date format.** Always use `Z` suffix on timestamps (`2026-05-26T00:00:00Z`), not `+00:00` or other timezone formats. The API returns 400 for non-Z formats.
2. **Region detection.** Don't assume the user's region — always extract from their actual tariff code on the account. Region codes A-P are NOT the same as the first letter of the region name.
3. **Results are newest-first.** The API returns rates in reverse chronological order. Always reverse for chronological display.
4. **API times are UTC.** All `valid_from`/`valid_to` values are UTC (Z suffix). Convert to local time for UK users (BST = UTC+1).
5. **Agile Outgoing ≠ Outgoing Octopus.** Agile Outgoing is the variable half-hourly export tariff. Outgoing Octopus (OUTGOING-VAR-24-10-26) is the fixed 12p/kWh flat rate. The user may be on either.
6. **Agile rates change daily.** Based on day-ahead wholesale prices, published around 16:00 for the next day. Rates vary by region.
7. **API keys are long-lived.** Unlike Tesla tokens, Octopus API keys don't expire. Store securely in memory.
8. **datetime objects in JSON.** When building HA sensor attributes with rate schedules, convert datetime objects to strings first — HA attribute values must be JSON-serializable.
9. **Standard unit rate ≠ Agile rate.** The `standard_unit_rate_inc_vat` field in the product's tariff object is just a representative/comparison figure. The actual variable half-hourly Agile rates must be fetched from `standard-unit-rates/` endpoint.
10. **48 slots per day.** The Agile Outgoing schedule has exactly 48 half-hour slots per full day. When querying midnight-to-midnight, you may get fewer results if the current day's schedule hasn't been fully published yet.
11. **Single-register tariffs CAN have peak/off-peak rates.** Intelligent Octopus Go is listed as a "single register" tariff but its `standard-unit-rates` endpoint returns alternating peak and off-peak blocks, not a single flat rate. Don't assume a single-register tariff has a single rate — always fetch the actual rates.
12. **Consumption data is delayed.** Smart meter consumption data from the Octopus API can lag by several hours (sometimes 6-24h). Don't use it for real-time display; use the live Tesla energy API for current values and Octopus consumption for daily totals.
13. **Same meter, two MPANs.** Import and export can share the same physical meter (dual-register smart meter) but have different MPANs. Both are exposed under the same account's properties. The `is_export` field on each meter point distinguishes them.
