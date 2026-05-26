# Tesla Owners API — Energy Endpoints Reference

Base URL: `https://owner-api.teslamotors.com`

Auth: `Authorization: Bearer <access_token>`

Access tokens expire in 8 hours. Use the refresh_token endpoint to get a new one.

## Products

```http
GET /api/1/products
```

Returns all Tesla products on the account (vehicles, energy sites). Find `energy_site_id` here.

```json
{
  "response": [
    {
      "energy_site_id": 1689543131745218,
      "site_name": "Chez Hogarth",
      "gateway_id": "1707000-30-L--TG125260002GXA",
      "battery_type": "solar_powerwall",
      "components": {
        "battery": true, "solar": true, "grid": true, "load_meter": true
      }
    }
  ],
  "count": 1
}
```

## Live Status

```http
GET /api/1/energy_sites/{energy_site_id}/live_status
```

```json
{
  "response": {
    "solar_power": 7957,
    "percentage_charged": 89.69,
    "battery_power": 0,
    "load_power": 2678,
    "grid_status": "Active",
    "grid_power": -5279,
    "generator_power": 0,
    "wall_connectors": [],
    "island_status": "on_grid",
    "storm_mode_active": false,
    "timestamp": "2026-05-25T13:48:42+01:00"
  }
}
```

## Site Info

```http
GET /api/1/energy_sites/{energy_site_id}/site_info
```

Returns battery count, nominal_full_pack_energy, site name, installer info.

## Power Sign Convention

| Field | Sign |
|-------|------|
| `solar_power` | Positive = producing |
| `battery_power` | Negative = charging, Positive = discharging |
| `grid_power` | Negative = exporting to grid, Positive = importing |
| `load_power` | Positive = home consuming |

All values in **watts**.

## Token Refresh

```http
POST https://auth.tesla.com/oauth2/v3/token
Content-Type: application/json

{
  "grant_type": "refresh_token",
  "client_id": "ownerapi",
  "refresh_token": "..."
}
```

Response:
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "expires_in": 28800
}
```
