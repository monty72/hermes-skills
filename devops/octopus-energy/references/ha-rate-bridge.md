# Octopus → Home Assistant Rate Bridge

Push live Agile Outgoing rates to HA sensors alongside the energy dashboard data.

## Sensors Created

| Sensor | Purpose | Unit |
|---|---|---|
| `sensor.energy_export_rate` | Current half-hour export rate | p/kWh |
| `sensor.energy_earning_rate` | Earnings per hour at current export | £/h |
| `sensor.energy_slot_earnings` | Earnings for current 30-min slot | £ |
| `sensor.energy_agile_schedule` | Today's full rate schedule | slots |

## Key Implementation Details

### Authentication
- Octopus API: HTTP Basic Auth (API key as username, empty password)
- HA API: Bearer token from `HASS_TOKEN` in `~/.hermes/.env`

### Rate Fetching
```python
# Get today's Agile Outgoing rates (region M = Yorkshire)
tariff = f"E-1R-AGILE-OUTGOING-19-05-13-{REGION}"
url = f"/products/AGILE-OUTGOING-19-05-13/electricity-tariffs/{tariff}/standard-unit-rates/"
# Must use Z-suffixed timestamps
params = f"?period_from={today_start}Z&period_to={tomorrow_start}Z"
```

### API Response Ordering
The Octopus API returns rates **newest-first** (reverse chronological). Always reverse for display:

```python
results = list(data.get("results", []))
results.reverse()
```

### Timezone Handling
All API timestamps are UTC. UK users need local time conversion (BST = UTC+1 in summer):

```python
import time as time_mod
from datetime import timedelta

def fmt_time(utc_dt):
    if utc_dt is None:
        return "?"
    is_dst = time_mod.localtime().tm_isdst
    offset = timedelta(hours=1) if is_dst else timedelta(hours=0)
    lt = utc_dt + offset
    return lt.strftime("%H:%M")
```

### HA Sensor Creation
Use `POST /api/states/{entity_id}` with JSON body:

```python
body = json.dumps({
    "state": str(rate_value),
    "attributes": {
        "unit_of_measurement": "p/kWh",
        "friendly_name": "Export Rate",
        "icon": "mdi:cash",
        "tariff": "Agile Outgoing",
        "region": "M - Yorkshire",
        "slot_start": fmt_time(slot_start),
        "slot_end": fmt_time(slot_end)
    }
})
```

⚠️ All attribute values must be JSON-serializable. Convert datetimes to strings first.

### Earnings Calculation
```python
export_kw = abs(grid_kw) if grid_kw < 0 else 0  # From Tesla API
rate_p = current_rate  # From Octopus API (p/kWh)
earnings_ph = round(export_kw * rate_p / 100, 2)  # £/h
slot_earnings = round(earnings_ph / 2, 2)  # £ per 30-min slot
```

### Cron Setup
Create a `no_agent=True` cron job running `every 1m`:

```python
# cronjob(action='create', name='Octopus Rates to HA',
#         script='octopus_to_ha.py', no_agent=True,
#         schedule='every 1m', deliver='local')
```

## Cross-References
- Power data sensors: see `tesla-energy-dashboard` → `references/ha-energy-bridge.md`
- Export settings: see `tesla-powerwall-cloud` skill
- Full Octopus API details: see the parent `octopus-energy` skill
