# Tesla Owner API — Energy Endpoint Reference

Base URL: `https://owner-api.teslamotors.com`

## Authentication

All requests require `Authorization: Bearer <access_token>`.

## Live Status

```
GET /api/1/energy_sites/{energy_site_id}/live_status
```

Response body `response` keys:

```json
{
  "solar_power": 1525,          // W, positive = generating
  "battery_power": -876,        // W, negative = charging, positive = discharging
  "grid_power": 0,              // W, positive = import, negative = export
  "load_power": 649,            // W, house consumption
  "percentage_charged": 54.26,  // %
  "grid_status": "Active",
  "storm_mode_active": false,
  "island_status": "on_grid",
  "energy_exports": null,       // May be null
  "timestamp": "2026-05-26T19:25:35+01:00"
}
```

Balance check: `solar + battery + grid = load`

## Site Info

```
GET /api/1/energy_sites/{energy_site_id}/site_info
```

Key `response` fields:

- `default_real_mode`: "autonomous" | "self_consumption"
- `backup_reserve_percent`: 0-100
- `user_settings`: storm_mode_enabled, off_grid_vehicle_charging_enabled
- `components.solar`: bool
- `components.battery`: bool
- `components.grid`: bool
- `components.battery_type`: "solar_powerwall"
- `components.gateways[].firmware_version`: string
- `components.customer_preferred_export_rule`: "battery_ok" | "pv_only" | "never"
- `components.net_meter_mode`: string
- `components.edit_setting_energy_exports`: bool
- `components.grid_services_enabled`: bool
- `components.island_config`: string
- `tou_settings.optimization_strategy`: "economics"

## Operation (Set Mode)

```
POST /api/1/energy_sites/{energy_site_id}/operation
{"default_real_mode": "autonomous"}
```

Response: `{"response": {"Message": "Operation mode updated", "Code": 200}}`

## Backup Reserve

```
POST /api/1/energy_sites/{energy_site_id}/backup
{"backup_reserve_percent": 0}
```

Response: `{"response": {"Message": "Backup reserve updated", "Code": 200}}`

## Grid Import/Export

```
POST /api/1/energy_sites/{energy_site_id}/grid_import_export
{"grid_export": "battery_ok", "grid_import": true}
```

Response: `{"response": ""}` (empty string = success)

## Storm Mode

```
POST /api/1/energy_sites/{energy_site_id}/storm_mode
{"enabled": false}
```

## Token Refresh

```
POST https://auth.tesla.com/oauth2/v3/token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token
&client_id=ownerapi
&refresh_token=<REFRESH_TOKEN>
&scope=openid email offline_access
```
