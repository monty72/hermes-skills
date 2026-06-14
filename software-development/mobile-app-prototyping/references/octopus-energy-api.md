# Octopus Energy API Integration

## Overview

Octopus Energy provides a REST API for tariff rates, consumption, account data, and IOG (Intelligent Octopus Go) charging slots. Auth is via HTTP Basic with an API key.

**Base URL:** `https://api.octopus.energy/v1/`

**Auth:** `Authorization: Basic <base64(api_key + ':')>`

## Key Endpoints

### Tariff Rates (Standard Unit Rates)
```
GET /products/{product_code}/electricity-tariffs/{tariff_code}/standard-unit-rates/
```
Parameters: `page_size`, `period_from`, `period_to`

Product codes:
- `AGILE-FLEX-22-11-25` — Agile Octopus import
- `AGILE-OUTGOING-19-05-17` — Agile Outgoing export
- `INTELLI-VAR-22-10-14` — Intelligent Octopus Go (IOG)
- `GO-V3-22-10-14` — Octopus Go (fixed off-peak)

Tariff codes follow the pattern `E-1R-{PRODUCT_CODE}-{REGION}`. Agile uses region C as default.

### Response shape:
```json
{
  "results": [
    {
      "valid_from": "2024-01-01T00:00:00Z",
      "valid_to": "2024-01-01T00:30:00Z",
      "value_exc_vat": 15.0,
      "value_inc_vat": 15.75
    }
  ]
}
```

### Standing Charges
```
GET /products/{product_code}/electricity-tariffs/{tariff_code}/standing-charges/
```
Returns daily standing charge in pence.

### Consumption
```
GET /electricity-meter-points/{mpan}/meters/{serial}/consumption/
```
Parameters: `page_size` (max 25000), `period_from`, `period_to`, `order_by` (period/consumption)

Response: `{ "results": [ { "consumption": 0.5, "interval_start": "...", "interval_end": "..." } ] }`

### Account Info
```
GET /accounts/{account_number}/
```

### IOG Charging Slots (Kraken Flex)
```
GET /kraken-flex/accounts/{account_number}/plans/current/schedule/
```
Returns charging/discharge slots for Intelligent Octopus Go.

If unavailable, fall back to:
```
GET /electricity-meter-points/{mpan}/meters/{serial}/iog-slots/
```

## Code Pattern

```typescript
const OCTOPUS_API = 'https://api.octopus.energy/v1';

function authHeader(apiKey: string): string {
  return 'Basic ' + btoa(apiKey + ':');
}

async function fetchRates(tariffCode: string, productCode: string) {
  const resp = await fetch(
    `${OCTOPUS_API}/products/${productCode}/electricity-tariffs/${tariffCode}/standard-unit-rates/?page_size=1500`,
    { headers: { Authorization: authHeader(apiKey) } }
  );
  return (await resp.json()).results;
}
```

## Common Usage

- **Agile rates** update every 30 minutes, published ~24h ahead
- **IOG rates** are static: ~31p peak, ~5.5p off-peak (6h window, typically 23:30–05:30)
- **Outgoing Agile** export rates are 15p flat (fixed), or variable depending on region
- **Consumption data** is in kWh, 30-minute intervals

## Account Reference

From session with user `monty72`:
- Account: `A-A6E7949D`
- Import: IOG (Intelligent Octopus Go)
- Export: Agile Outgoing
- Import rates: peak ~31.66p, off-peak ~5.49p
