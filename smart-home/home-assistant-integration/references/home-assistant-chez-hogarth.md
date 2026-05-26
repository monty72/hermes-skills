# Home Assistant Setup — Chez Hogarth

## Server Details
- **URL:** `http://192.168.1.146:8123`
- **Version:** 2026.3.1
- **Location:** UK (Europe/London, GB, GBP, metric)
- **State:** RUNNING

## Token & Gateway
- Long-Lived Access Token stored in `~/.hermes/.env` as `HASS_TOKEN`
- HA URL stored in `~/.hermes/.env` as `HASS_URL`
- Gateway auto-detects these on startup — no separate config.yaml section needed
- Connected as Hermes gateway platform at startup (check: `grep homeassistant ~/.hermes/logs/gateway.log`)

## Entity Summary (123 total)

| Domain | Count | Notes |
|--------|-------|-------|
| sensor | 72 | Powerwall (unavailable), Audi ETron (charging 2kW external power active), iPad/iPhone battery |
| binary_sensor | 21 | Audi door/window states (all off/closed) |
| device_tracker | 3 | Matt's iPad (home), Matt's iPhone (home), Audi ETron (home) |
| media_player | 3 | Shield (off), Living Room TV (unavailable), Shield 2 (unavailable) |
| lock | 1 | Audi ETron door lock (locked) |
| switch | 2 | Tesla storm watch (unavailable), grid charging (unavailable) |
| update | 9 | Various HA add-on updates |
| weather | 1 | Met Office integration |

## Problems Found
- **Tesla/Teslemetry sensors all `unavailable`** — Teslemetry integration likely needs re-authentication or the cloud API is having issues
- **Living Room TV + Shield 2 `unavailable`** — devices may be powered off or network-disconnected

## Suggested Next Steps
1. Re-authenticate Teslemetry integration in HA to restore Powerwall data
2. Consider adding the Tesla Owner API directly (bypass HA) for the energy dashboard (already done)

## Gateway Restart Notes
- `hermes gateway restart` **kills the active agent session** — do not run while user is mid-conversation
- `.env` changes require gateway restart (read once at startup)
- Weekly scheduled restart: Sunday 4AM BST (job ID: d66fa995aba8)
