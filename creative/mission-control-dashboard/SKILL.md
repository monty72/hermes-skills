---
name: mission-control-dashboard
description: "Build and deploy the Hermes Mission Control dashboard — a dark-themed, real-time system monitoring dashboard showing agent status, token usage, API calls, system info, and activity timeline. Deployed as a static site via Surge.sh or localhost.run tunnel with a live data API endpoint."
version: 2.2.0
---

# Mission Control Dashboard

## Overview

Build and deploy the Hermes Agent Mission Control dashboard — a high-end, dark-themed, real-time system monitoring dashboard.

**URL:** https://mission-control-hermes.surge.sh (or latest deployed URL)

## Features

- 6 key metrics: active agents, tokens used, API calls, memory %, uptime, skills count
- System services grid with health indicators
- Activity timeline
- 7 agent status cards with real-time status
- Quick actions panel
- Live UTC clock
- Dark interstellar theme with gradient glows and CSS animations
- CORS-ready JSON API endpoint for live data

## Project Structure

```
~/mission-control/
├── src/
│   ├── index.html        # Dashboard HTML (all CSS + JS inlined)
│   └── api.py            # Live data API server (Python, port 8081)
├── deploy.sh             # Deploy to Surge.sh
└── README.md             # This file
```

## Quick Rebuild

To rebuild from scratch:

```bash
# 1. Create the project structure
mkdir -p ~/mission-control/src

# 2. Write index.html from the skill reference
cp ~/.hermes/skills/creative/mission-control-dashboard/references/index.html ~/mission-control/src/index.html

# 3. Write api.py from the skill reference
cp ~/.hermes/skills/creative/mission-control-dashboard/references/api.py ~/mission-control/src/api.py

# 4. Deploy
cd ~/mission-control
npx surge ./src mission-control-hermes.surge.sh
```

Or, to have Hermes rebuild it instantly, just say **"rebuild Mission Control"** — I'll recreate the files from the stored references and redeploy.

## Deployment Pipeline

The canonical deployment flow for a dashboard like this is a three-stage pipeline:

### Stage 1: Local Dev & Verify
```bash
cd ~/mission-control/src
python3 -m http.server 8080
# Visit http://localhost:8080 to verify the dashboard renders
```

### Stage 2: Temporary Tunnel Preview (no auth, instant)
```bash
# While the http.server is running, start a tunnel:
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 \
  -R 80:localhost:8080 nokey@localhost.run
# Outputs: https://<hash>.lhr.life — share for immediate review
```
The tunnel URL changes every session. Use this for demos and quick shares. See the `static-site-deployment` skill for full tunnel reference.

### Stage 3: Permanent Deploy
```bash
cd ~/mission-control
npx surge ./src mission-control-hermes.surge.sh
```
Requires Surge login (email + password) on first use. Once logged in, subsequent deploys are instant.

## Starting the Live Data API

The `api.py` server provides real-time system metrics to the dashboard if JavaScript can reach it:

```bash
# Start the live data server on port 8081
python3 ~/mission-control/src/api.py

# Serve JSON at http://localhost:8081/
# CORS headers allow access from any origin
# The dashboard falls back to embedded static snapshot if API is unreachable
```

**Live data pattern** (reusable for any dashboard):
- The HTML has `window.__SNAPSHOT_DATA` — an embedded static dataset built at deploy time
- On load, it tries to `fetch(API)` from a live endpoint
- If the API is unreachable (no backend running, CORS mismatch), it falls back to the snapshot
- This means the dashboard always renders something useful, even as a static site
- See `references/live-data-pattern.md` for a full architectural description of this pattern

## Reference Files

- `references/index.html` — Full dashboard HTML (CSS + JS inlined, single file)
- `references/api.py` — Live data API server (reads agent.log, /proc, filesystem)
- `references/live-data-pattern.md` — Reusable static+live dashboard architecture pattern

## Colors

| Role | Dark hex |
|------|---------|
| Background | `#08080e` |
| Card | `#14141f` |
| Border | `#22223a` |
| Accent | `#6c8cff` |
| Green (good) | `#34d399` |
| Amber (warning) | `#fbbf24` |
| Red (error) | `#f87171` |

## Data Sources

The dashboard pulls from:
1. **`~/.hermes/logs/agent.log`** — token counts, API call history
2. **`/proc/uptime`** — system uptime
3. **`/proc/meminfo`** — memory usage
4. **`~/.hermes/skills/`** — skills count
5. **`~/.hermes/cron/`** — cron job count
6. **`~/.hermes/sessions/sessions.json`** — session data