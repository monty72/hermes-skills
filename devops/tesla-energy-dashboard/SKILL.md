---
name: tesla-energy-dashboard
description: "A real-time energy dashboard for Tesla Powerwall + Solar — shows solar production, battery state of charge, home consumption, grid import/export, and live energy flow. Deployed as a combined static + API proxy server."
version: 1.1.0
---

# Tesla Energy Dashboard

## Overview

A real-time dashboard for your Tesla Powerwall and solar system. Shows live solar generation, battery %, home consumption, grid flow, and daily energy totals. Uses Tesla Cloud API (no local password needed for PW3).

## Requirements

- Access to Powerwall data via **one** of:
  - **Tesla Cloud API (recommended for PW3)** — direct HTTP to `owner-api.teslamotors.com` with access token. No password needed.
  - **pyPowerwall Cloud** — Tesla account login, no local password needed
  - **Local Gateway API** — Powerwall on LAN with known password (works for PW2/PW+)
  - **pyPowerwall TEDAPI** — Gateway Wi‑Fi password from QR sticker
  - **pyPowerwall v1r LAN** — Wired Ethernet + RSA key (PW3 only)
- Python 3 (for the data API server)
- Tesla access token (from OAuth flow)

> **⚠️ PW3 note:** Powerwall 3 does NOT have a local web portal to set a customer password. The `/api/login/Basic` endpoint exists but was never provisioned with credentials. If your installer didn't set it, you MUST use Tesla Cloud API or pyPowerwall Cloud mode. See the `tesla-powerwall-local` skill for setup details.

## Architecture — Proxy Pattern

Two servers on separate ports, one public front-door:

```
┌──────────┐    /api/*     ┌──────────────────┐    Tesla Cloud     ┌───────────┐
│ Browser  │ ───────────► │ Proxy Server     │ ◄──────────────── │ Tesla API │
│ (tunnel) │    /          │ port 8000        │   access_token   │           │
│          │ ───────────► │                  │                  │           │
│          │              │ static files:    │                  │           │
│          │              │  • index.html     │                  │           │
│          │              │  • energy.html    │                  │           │
│          │              │  • mc.html        │                  │           │
│          │              │ proxy:            │                  │           │
│          │              │  • /api/* → :8081 │                  │           │
└──────────┘              └────────┬──────────┘                  └───────────┘
                                   │
                          ┌────────▼──────────┐
                          │ Backend API        │
                          │ port 8081          │
                          │ (energy_api.py)    │
                          │ embedded token     │
                          │ + auto-refresh     │
                          └───────────────────┘
```

> **⚠️ Critical:** Dashboard JS must use a **relative** API path (`/api/energy`), not an absolute `localhost:8081` URL. Absolute URLs break from tunnels since the remote browser can't reach the server's localhost.

## Quick Start

### 1. Set up credentials

You need a Tesla access token. See `tesla-powerwall-local` for OAuth flow. The token can be embedded in the backend API server (`scripts/energy_api.py` in this skill).

### 2. Start the backend API server

```bash
cd ~/energy-dashboard/src && python3 energy_api.py &
# Serves on port 8081 — has your Tesla token + auto-refresh
```

### 3. Start the proxy server

```bash
cd ~/dev-site/src && python3 api.py 8000 &
# Serves on port 8000 — static files + /api/* proxy to :8081
```

### 4. Open the dashboard

- Locally: `http://localhost:8000/energy.html`
- Via tunnel: `https://xxxx.lhr.life/energy.html`

> See `references/combined-api-server.md` for the complete proxy pattern code and gotchas.

## Deployment via localhost.run

```bash
# 1. Kill old tunnels (avoid duplicates)
kill $(pgrep -f 'ssh.*localhost.run') 2>/dev/null

# 2. Ensure both servers are running
fuser -k 8000/tcp 8081/tcp 2>/dev/null
cd ~/energy-dashboard/src && python3 energy_api.py &
cd ~/dev-site/src && python3 api.py 8000 &

# 3. Wait for backend to be ready
sleep 2

# 4. Create tunnel (background)
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 \
  -R 80:localhost:8000 nokey@localhost.run
# Output: https://<hash>.lhr.life tunneled with tls termination
```

**Pitfalls:**
- localhost.run takes 15-30s to print the URL — be patient
- Kill duplicate tunnels before creating new ones
- Always verify the tunnel URL responds before sharing

## Dashboard HTML Requirements

The `energy.html` JS must:

1. **Use relative API path:** `const API = '/api/energy';` — NOT `http://localhost:8081/api/energy`
2. **Handle fetch failures gracefully** — catch errors and show the "not connected" state
3. **Stay under Telegram's page limits** — the HTML is served via a web server, not embedded in messages

### Common Bugs That Break the Dashboard

- **Stray `}` in JavaScript** — a single extra closing brace from a bad patch or refactor will silently break `fetchData()` without throwing an error because it closes the function before the real closing brace. The dashboard then stays on "disconnected" forever. Symptoms: page loads, no JS console error, but `fetchData()` never runs. Fix: read lines 95-145 and verify `async function fetchData() { ... }` has exactly one `}` for the function body and one `}` for the async block.
- **Absolute API URL** — `const API = 'http://localhost:8081'` works for local testing but breaks through tunnels because the remote browser can't reach the server's localhost. Always use `/api/energy` (relative).
- **Empty catch block** — `catch(e) { }` swallows all errors. Always `console.warn('fetch failed:', e)` so the error surfaces in browser dev tools.

## Gateway Restart Survival

After a gateway restart, the backend API server (port 8081), proxy server (port 8000), and localhost.run tunnel may all be killed. Recovery steps:

```bash
# 1. Kill stale processes
fuser -k 8000/tcp 8081/tcp 2>/dev/null
kill $(pgrep -f 'ssh.*localhost.run') 2>/dev/null
sleep 2

# 2. Start backend API (has embedded Tesla token)
cd ~/energy-dashboard/src && python3 energy_api.py &

# 3. Start combined proxy server
cd ~/dev-site/src && python3 api.py 8000 &

# 4. Wait, verify, then tunnel
sleep 3
curl -s http://localhost:8081/  # Should return energy data
curl -s http://localhost:8000/api/energy  # Should proxy data

# 5. Create tunnel (background)
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 \
  -R 80:localhost:8000 nokey@localhost.run
```

> **Cron safety:** Do NOT schedule the above as a cron job — it restarts everything, which would interrupt conversations. The gateway itself has a separate weekly restart cron. These servers should be manually restarted as needed after a gateway restart.

## Scripts

- `scripts/energy_api.py` — standalone backend API server with embedded Tesla token + auto-refresh. Run on port 8081.
- `scripts/ha_energy_bridge.py` — push live energy data to Home Assistant as REST sensors (bypasses failed Tesla/Teslemetry HA integration). See `references/ha-energy-bridge.md`.

## References

- `references/restart-survival.md` — recovery steps after a gateway restart kills background processes.
- `references/combined-api-server.md` — combined proxy server pattern (static files + API proxy).
- `references/ha-energy-bridge.md` — Home Assistant energy sensor bridge: create REST sensors from the local energy API when the HA Tesla/Teslemetry integration is down.

## API Endpoint

**`GET /api/energy`** returns:

```json
{
  "solar_kw": 7.9,
  "battery_kw": -1.0,
  "grid_kw": -6.0,
  "home_kw": 0.9,
  "battery_percent": 89.7,
  "grid_status": "Active",
  "island_status": "on_grid",
  "storm_mode": false,
  "timestamp": "2026-05-25T12:58:24+00:00",
  "source": "tesla_cloud"
}
```

Sign convention:
- `solar_kw`: positive = producing
- `battery_kw`: negative = charging, positive = discharging
- `grid_kw`: positive = importing, negative = exporting
- `home_kw`: positive = home consuming

**Balance check:** `solar_kw + battery_kw + grid_kw ≈ home_kw` (should roughly equal — a non-zero difference indicates measurement noise or internal Powerwall consumption, not a bug)

## Troubleshooting

### Stale Token — Auto-Refresh Might Not Have Fired

The `energy_api.py` server's `refresh_access_token()` function only triggers on **401 HTTP errors** from API calls. If the server hasn't been polled in hours (e.g. dashboard not open, no cron jobs hitting `/api/energy`), the token sits stale. When you next query it, the first request fails, triggers a refresh, and the second succeeds — but this adds latency.

To verify token freshness without waiting for a 401:
```bash
python3 -c "
import re, time
with open('/home/matth/energy-dashboard/src/api.py') as f:
    content = f.read()
expires = re.search(r'token_expires\s*=\s*(\d+)', content)
if expires:
    t = int(expires.group(1))
    remaining = t - time.time()
    print(f'Token expires in {remaining/3600:.1f}h ({'STALE - refresh needed' if remaining < 60 else 'OK'})')
"
```

If stale, force a refresh by hitting the dashboard API once:
```bash
curl -s http://localhost:8081/api/energy 2>/dev/null || python3 -c "
# Run a manual refresh
exec(open('/home/matth/refresh_tesla.py').read())
"

## Dashboard Features

- Live energy flow visualization (solar → battery → home → grid)
- Battery state of charge with color coding (green > 80%, amber > 30%, red < 30%)
- Daily energy totals (solar today, grid import, grid export)
- Grid connection status
- Auto-refresh every 10 seconds
- Dark theme (interstellar style)
