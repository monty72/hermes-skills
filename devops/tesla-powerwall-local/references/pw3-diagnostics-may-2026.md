# Powerwall 3 Diagnostics — May 2026

Captured from local Gateway diagnostics dump on UK G99 single-phase system.

## System

| Field | Value |
|-------|-------|
| Firmware | 26.10.3 |
| Capacity | 27 kWh (nominal), 24,690 Wh total |
| Power | 11.5 kW nominal output |
| Units | 2 (main + 1 expansion) |
| Backup reserve | 5% |
| Commissioned | Jan 13, 2026 |
| Grid | 230V / 50Hz / single-phase (G99) |
| SOC (at capture) | ~40.8% |

## Battery Units

| Unit | Serial | Last Measured Capacity |
|------|--------|----------------------|
| PW3 Main | TG125260002GXA | 14,210 Wh |
| Expansion | TG125175001A27 | 14,380 Wh |

## Network

| Interface | IP | Notes |
|-----------|-----|-------|
| WiFi (EE-32WZ9G) | 192.168.1.108 | 60% signal |
| Backup (Ethernet) | 192.168.90.2 | Internal PW3 subnet |
| Cellular (GSM) | 10.26.52.171 | Tesla cloud backup |
| Tesla Cloud | Connected | |

## Vehicle Charging (from diagnostics)

| Field | Value |
|-------|-------|
| Make | Audi |
| VIN | WAUZZZGF5SA048308 |
| Battery | 94.9 kWh |
| SOC | 78% |
| Charging status | FAULT |
