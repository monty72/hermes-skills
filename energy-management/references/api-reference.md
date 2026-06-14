# Octopus Energy API — Call Reference

Base URL: `https://api.octopus.energy/v1`

## Auth

```python
import base64
auth_str = base64.b64encode(f"{API_KEY}:".encode()).decode()
# In headers: {"Authorization": f"Basic {auth_str}"}
```

## Account Info

```
GET /v1/accounts/A-A6E7949D/
```

```json
{
  "number": "A-A6E7949D",
  "properties": [{
    "mpan": "2394300464700",
    "electricity_meter_points": [{
      "mpan": "2394300464700",
      "meters": [{"serial_number": "20L3570122"}],
      "agreements": [{"tariff_code": "E-1R-AGILE-OUTGOING-19-05-13-M"}],
      "is_export": true
    }]
  }]
}
```

## Products

List all:
```
GET /v1/products/
```

Agile Outgoing product detail:
```
GET /v1/products/AGILE-OUTGOING-19-05-13/
```

All outgoing products found:
- `AGILE-OUTGOING-19-05-13` — Agile Outgoing (variable, wholesale-linked)
- `OUTGOING-VAR-24-10-26` — Outgoing Octopus (fixed 12p/kWh from March 2026)
- `OUTGOING-SEG-FIX-12M-20-07-07` — Smart Export Guarantee fixed
- `OUTGOING-SEG-EO-FIX-12M-24-04-05` — SEG Export Only fixed

## Rates (Agile Outgoing, Region M)

```
GET /v1/products/AGILE-OUTGOING-19-05-13/electricity-tariffs/E-1R-AGILE-OUTGOING-19-05-13-M/standard-unit-rates/?period_from=2026-05-26T00:00:00Z&period_to=2026-05-27T00:00:00Z
```

Response shape:
```json
{
  "count": 48,
  "results": [
    {"value_inc_vat": 14.01, "valid_from": "2026-05-26T18:30:00Z", "valid_to": "2026-05-26T19:00:00Z"},
    ...
  ]
}
```

Sample rates (Region M, 2026-05-26 evening):
```
18:30-19:00: 13.78p   ← current at time
19:00-20:00: 14.16-14.26p  ← peak
20:00-21:30: 13.09-13.31p
21:30-23:00: 11.57-11.93p
23:00-00:00: 11.18p
```

## HA Sensor Bridge Pattern

Creating sensors via POST to HA API:

```python
def ha_post(entity_id, state, attrs):
    data = json.dumps({"state": state, "attributes": attrs}).encode()
    req = urllib.request.Request(f"{HASS_URL}/api/states/{entity_id}",
        data=data, method="POST",
        headers={"Authorization": f"Bearer {HASS_TOKEN}", "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req).read())

# Then call:
ha_post("sensor.energy_export_rate", "13.78",
    {"unit_of_measurement": "p/kWh", "friendly_name": "Export Rate", ...})
```

## Cron Setup

```bash
# Copy bridge script
cp script.py ~/.hermes/scripts/octopus_to_ha.py
chmod +x ~/.hermes/scripts/octopus_to_ha.py

# Create cron
# cronjob(action='create', name='Octopus Rates to HA', script='octopus_to_ha.py',
#         schedule='every 1m', no_agent=True, deliver='local')
```
