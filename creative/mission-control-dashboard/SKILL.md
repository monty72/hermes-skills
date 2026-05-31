---
name: mission-control-dashboard
description: "Build and deploy the Hermes Mission Control dashboard — a dark-themed, tabbed, real-time system monitoring dashboard showing agent health, token usage, API performance, gateway status, and OpenClaw managed-agent readiness. Delivered as a combined Python server (HTML + JSON API) with a permanent systemd service and fallback static snapshot. Tabs over scrolling: user prefers tabbed navigation sections over long single-scroll pages."
version: 4.2.0
---

# Mission Control Dashboard

## Overview

Build and deploy the Hermes Agent Mission Control dashboard — a high-end, dark-themed, tabbed real-time system monitoring dashboard.

**Architecture:** Combined Python HTTP server (`server.py`) serves both the HTML dashboard and a JSON API (`/api`). The dashboard uses a live-data pattern: JavaScript tries to `fetch(API)` on load, falls back to embedded `window.__SNAPSHOT_DATA` if the API is unreachable. A systemd user service keeps it running permanently.

**Tabs (user preference):** The dashboard uses tabbed navigation (Overview / Hermes Self / OpenClaw) instead of a single long scroll. Each tab focuses on one aspect of the system. This is the user's preferred layout — never build a single-scroll dashboard for them.

**URL:** Served locally at `http://localhost:8081`, or via localhost.run tunnel.

## Features

- **📊 Overview tab** — 6 key metrics, dual-pane Hermes + OpenCrawl agent view, activity timeline, 8 tracked agent services, quick actions panel
- **🖥️ Hermes Self tab** — gateway status (systemd), API latency & error rate, error log, session counts, cron jobs, system resources, DeepSeek balance
- **🔧 OpenClaw tab** — managed-agent service readiness: bot pool counts (Telegram + Discord), LLM key pool status, config templates, provisioning scripts, customer count & health
- Local time (BST/GMT auto-detected via `Intl.DateTimeFormat`), dark interstellar theme
- CORS-ready JSON API endpoint (`/api`) — same-origin fetch only (no external API URLs)
- Embedded static snapshot fallback (`window.__SNAPSHOT_DATA`)
- **Proxmox tab** — hypervisor monitoring via PVE API (node status, CPU/memory, all 7 VMs/CTs with drill-down)
- systemd user service for permanent deployment
- Data collector cron (`observability-collect.py`) runs every 5 minutes

## Project Structure

```\n~/mission-control/\n├── src/\n│   ├── index.html        # Dashboard HTML (all CSS + JS inlined, tabbed)\n│   ├── server.py         # Combined HTTP server (HTML + JSON API, port 8081)\n│   └── __pycache__/      # (auto-generated)\n├── deploy.sh             # Deploy to Surge.sh (legacy)\n├── README.md             # (optional)\n└── references/           # MC V4.0 design brief at references/mc-v4-design-brief.md\n\n~/mission-control-v4/        # V4.0 Next.js frontend (see references/mc-v4-design-brief.md for full structure)\n├── src/\n│   ├── app/              # Pages + API proxy route\n│   ├── components/       # Sidebar, StatusCard, Modal, PixelProgressBar, AgentAvatar\n│   └── lib/api.ts        # TypeScript types + fetch helpers\n├── next.config.ts\n├── package.json\n└── tsconfig.json\n\n~/.hermes/scripts/\n└── observability-collect.py   # Data collector (cron: every 5m)\n\n~/.config/systemd/user/\n└── mission-control.service    # Permanent systemd service\n```

## Data Collector

The data collector at `~/.hermes/scripts/observability-collect.py` is a no-agent cron script (runs every 5 minutes via the existing "Observability snapshot" cron). It gathers:

### Hermes Agent self-monitoring
- **System**: uptime, CPU/Mem/Disk from `/proc` and `df`
- **Tokens**: input/output/total + cache hit rate from `~/.hermes/logs/agent.log`
- **API metrics**: avg latency, total API calls, error rate from `agent.log`
- **Gateway**: systemd `is-active hermes-gateway` check
- **Errors**: 24h error count, API error count from `agent.log`
- **Sessions**: today/total from `hermes sessions list --json`
- **Skills & Cron**: skills count from `~/.hermes/skills/`, cron count from `~/.hermes/cron/jobs.json`
- **DeepSeek balance**: from `~/.hermes/data/deepseek-history.json`

### OpenCrawl Worker
- SSH to `matth@192.168.1.137`, runs `~/scripts/worker-metrics.sh`
- Returns: uptime, mem, disk, load avg, services running, Docker containers, Ollama status/models, Hermes worker process count

### OpenClaw managed-agent
- **Bot pools**: Telegram + Discord bot counts from `~managed-agent/configs/*-bot-pool.json`
- **Key pool**: LLM key readiness from `~managed-agent/configs/llm-key-pool.json`
- **Customers**: count from `~managed-agent/customers/` directories, health from individual `health.json` files
- **Templates**: config YAML count from `~managed-agent/configs/`
- **Scripts**: provisioning script count from `~managed-agent/scripts/`
- **Health check**: `~managed-agent/scripts/check-health.sh` existence + executable

### Output
Writes to `~/.hermes/data/observability.json`. The server reads this file on every `/api` request.

### ⚠️ CRITICAL PITFALL: Data Source Location Mismatch

The MC server reads `Path.home() / ".hermes" / "data" / "observability.json"` as its single data source. **The collector and server MUST run on the same host**, or the snapshot must be synced (via cron + scp/rsync) to the server's host.

If you deploy the MC server to a different host than the collector (e.g., a separate web LXC), the server's `build_status()` falls back to `fallback_status()` which returns all zeros and N/A values. The main dashboard renders but displays empty data. All drill-down endpoints (cron, skills, errors, bot pools) also return empty results.

**The fix:** Either co-locate the collector cron and MC server on the same machine, or add a data-sync step to the collector cron that copies the snapshot to the remote host.

## Adding Basic Auth (No nginx required)

When deploying the MC server on a machine where you can't install nginx or run sudo (no TTY, no passwordless sudo), add Basic Auth directly to the Python HTTP server. This is self-contained in one file and works in any Python 3 environment.

### Pattern

```python
import base64

AUTH_USER = os.environ.get("MC_USER", "mc")
AUTH_PASS = os.environ.get("MC_PASS", "MissionCtrl2026!")
AUTH_REALM = "Mission Control"

def _check_auth(headers):
    """Returns True if the request is authorized."""
    auth = headers.get("Authorization", "")
    if not auth.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(auth[6:]).decode()
        user, pwd = decoded.split(":", 1)
        return user == AUTH_USER and pwd == AUTH_PASS
    except Exception:
        return False

def _require_auth(handler):
    """Send 401 to the client."""
    handler.send_response(401)
    handler.send_header("WWW-Authenticate", f'Basic realm="{AUTH_REALM}"')
    handler.send_header("Content-Type", "application/json")
    handler.end_headers()
    handler.wfile.write(b'{"error":"Authorization required"}')
```

Then at the top of `do_GET()`:

```python
def do_GET(self):
    path = urllib.parse.urlparse(self.path).path

    # Basic Auth check
    if not _check_auth(self.headers):
        _require_auth(self)
        return
```

### Credentials via Environment Variables

```bash
export MC_USER=mc
export MC_PASS=MissionCtrl2026!
```

Or in a systemd service unit:

```ini
[Service]
Environment=MC_USER=mc
Environment=MC_PASS=MissionCtrl2026!
```

### ⚠️ CRITICAL PITFALL: Basic Auth Blocks JavaScript fetch() Calls

When Basic Auth is enabled, the browser authenticates for page loads but JavaScript `fetch('/api')` calls **fail silently**. The reason: browsers treat page-load credentials (from the login prompt or `user:pass@host` URL) as "default credentials" that should be sent with same-origin XHR/fetch requests by default — BUT this behaviour is unreliable in practice. Specifically:

- **URL-embedded credentials** (`https://user:pass@host/`) are deprecated in modern browsers. Chrome/Firefox strip the credentials from sub-resource requests, including fetch/XHR. The page loads (because the browser handled auth for the navigation) but every JS fetch call returns 401 → falls back to `window.__SNAPSHOT_DATA` (static).
- **Browser login-prompt credentials** (native HTTP Basic Auth dialog) are cached per origin and sent with subsequent requests — this should work, but is unreliable with localhost.run tunnels due to TLS/redirect behaviour.

**Diagnosis:** The dashboard shows "Static snapshot (API unreachable)" at the top right, all data is stale (from the embedded snapshot), and clicking any metric card or drill-down link shows "Failed to load" modals.

**Fix options (choose one):**

1. **Remove Basic Auth entirely (when behind a tunnel).** The localhost.run tunnel URL is a random hash — effectively unguessable. This is the simplest fix for a homelab dashboard:
   ```python
   # Just remove the two lines in do_GET() and do_POST():
   # if not _check_auth(self.headers):
   #     _require_auth(self)
   ```
   Then restart the server and re-create the tunnel.

2. **Send credentials explicitly in every fetch call.** Instead of `fetch('/api')`, use:
   ```javascript
   fetch('/api', { credentials: 'include' })
   ```
   This tells the browser to send cookies and HTTP Basic Auth credentials even if it wouldn't by default. Apply to ALL fetch calls in the dashboard: `/api`, `/api/tasks`, `/api/drill/`, `/api/cron`, `/api/skills`, `/api/errors`, `/api/tg-bots`, `/api/dc-bots`, `/api/ocla-templates`, `/api/pve-action/`.

3. **Use a proxy pattern (Next.js V4 approach).** The V4 Next.js frontend uses a catch-all API route at `src/app/api/[[...slug]]/route.ts` that injects the Basic Auth header into proxied requests to the Python backend. The browser talks to Next.js (no auth), Next.js talks to Python (with auth). This is the cleanest solution for a production deployment.

**Surface coverage for fix #2 (all fetch locations):**
- Overview render → `fetch(API)` (line ~1248 in index.html)
- Tasks tab → `fetch('/api/tasks')`
- Deep drill → `fetch('/api/drill/${key}')`
- Cron detail → `fetch('/api/cron')`
- Skills detail → `fetch('/api/skills')`
- Error detail → `fetch('/api/errors')`
- Bot pool → `fetch('/api/tg-bots')` and `fetch('/api/dc-bots')`
- Template detail → `fetch('/api/ocla-templates')`
- PVE action → `fetch('/api/pve-action/${vmid}/${action}')`
- All POST calls → task creation, note adding, status updates

### Pitfalls

- **`patch` tool fails on HTML+JS escaped quotes.** The `patch` tool returns "Escape-drift detected" when `old_string`/`new_string` contain `\"` sequences inside JavaScript template literals. This happens in `index.html` where template strings like `` `<div onclick=\"showDeepDrill('x')\">` `` use `\"`. **Fix:** Use a Python script (`python3 -c` with `.replace()`) or `terminal` with sed for the replacement instead of the `patch` tool. The `write_file` approach works if you read the whole file content first.

- **When migrating from old `showXDetail()` to `showDeepDrill(key)`, every surface must be updated individually.** The 7 surfaces in the Overview tab that need updating are: (1) metric cards array, (2) Hermes agent pane 4-grid, (3) OpenCrawl worker pane 4-grid, (4) Hermes agent detail rows (Cron + Skills), (5) agent list `clickMap` (8 entries by initial), (6) clickMap fallback (`||'showSystemDetail()'` on line 461), (7) activity timeline items. In the Hermes Self tab: (1) 6 metric cards, (2) gateway info table (6 rows), (3) API info table (3 rows), (4) error info table (1 row), (5) session info table (4 rows). Missing any surface leaves old shallow modals still reachable.

- `BaseHTTPRequestHandler.headers` is case-insensitive for dict-like access — `headers.get("Authorization")` works
- The `_require_auth` function sends `WWW-Authenticate: Basic realm=...` so the browser pops up a native auth dialog
- Set credentials via env vars, never hardcode them in server.py — but if you must, the env-var fallback (`os.environ.get()`) allows runtime override

## Watchdog Cron (When systemd Isn't Available)

If you can't install a systemd service (no sudo TTY), use a Hermes cron job to keep the MC server alive:

### Watchdog script (`~/.hermes/scripts/mc-watchdog.sh`)

```bash
#!/bin/bash
# Called by cron every 5 minutes — restarts MC server if down
MC_PID=$(pgrep -f "server.py" | head -1)
if [ -z "$MC_PID" ]; then
    cd /home/matth/mission-control/src
    python3 server.py &>/tmp/mc-server.log &
    disown
    echo "MC server restarted at $(date)" >&2
else
    echo "MC server running (pid $MC_PID)" >&2
fi
```

### Cron job (Hermes cron, not system cron)

```bash
hermes cron create \
  --name "MC Server Watchdog" \
  --schedule "every 5m" \
  --prompt "Check if MC server is alive, restart if not" \
  --deliver local \
  --repeat -1
```

This avoids the no-TTY problem with sudo/systemd while achieving the same auto-restart guarantee.

### Stage 0: Systemd System Services (MC v4.1 — Current)

MC v4.1 runs as **two systemd system services** (not user services) for auto-start on boot and restart-on-failure:

**Backend (Python API, port 8081):** `/etc/systemd/system/mc-backend.service`
```ini
[Unit]
Description=Mission Control v4.1 — Python Backend API (port 8081)
After=network.target
Before=mc-frontend.service

[Service]
Type=simple
User=matth
WorkingDirectory=/home/matth/mission-control
ExecStart=/usr/bin/python3 /home/matth/mission-control/src/server.py
Restart=always
RestartSec=5
Environment=PORT=8081

[Install]
WantedBy=multi-user.target
```

**Frontend (Next.js production, port 3000):** `/etc/systemd/system/mc-frontend.service`
```ini
[Unit]
Description=Mission Control v4.1 — Next.js Production Server
After=network.target
Wants=mc-backend.service

[Service]
Type=simple
User=matth
WorkingDirectory=/home/matth/mission-control-v4
ExecStart=/home/matth/.local/bin/node /home/matth/mission-control-v4/node_modules/.bin/next start -p 3000
Restart=always
RestartSec=5
Environment=NODE_ENV=production
Environment=PORT=3000
Environment=PATH=/home/matth/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

[Install]
WantedBy=multi-user.target
```

**⚠️ CRITICAL PITFALL — Node.js binary path:** `node` is NOT at `/usr/bin/node` on the Hermes VM. It's at `/home/matth/.local/bin/node`. Systemd does NOT source the user's shell profile — `ExecStart` must use the full absolute path. Running `which node` first is mandatory before writing the service unit.

**⚠️ PITFALL — Port still in use:** The old Next.js dev server (`npm run dev`) from a previous terminal session may still hold port 3000. Before first systemd start, kill orphans:
```bash
fuser -k 3000/tcp 2>/dev/null
fuser -k 8081/tcp 2>/dev/null
sleep 2
sudo systemctl restart mc-backend mc-frontend
```

**Commands:**
```bash
sudo systemctl enable mc-backend mc-frontend
sudo systemctl start mc-backend mc-frontend
sudo systemctl status mc-backend mc-frontend --no-pager
sudo journalctl -fu mc-backend
sudo journalctl -fu mc-frontend
```

**Old port 8081 redirect:** The HTML file at `~/mission-control/src/index.html` was replaced with an auto-redirect to port 3000. Any browser or service hitting the old port 8081 directly gets redirected to the current MC.

**Troubleshooting:** If `sudo systemctl start` fails with exit code 1, check `sudo journalctl -u mc-frontend -n 20` for the error. Common causes: port in use (EADDRINUSE), wrong Node.js path, or TypeScript compilation error (for Next.js, run `npx next build` first to catch build-time errors).

### Stage 1: Temporary Tunnel Preview (Instant, No Auth)

```bash
# MC v4.1 — tunnel to port 3000 (Next.js production)
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 \
  -R 80:localhost:3000 nokey@localhost.run
# Outputs: https://<hash>.lhr.life — share for immediate review

# MC v3.x (legacy) — tunnel to port 8081 (Python server)
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 \
  -R 80:localhost:8081 nokey@localhost.run
```

**Pitfalls with localhost.run:**
- The tunnel can take 15–45s to print the URL. Use a background process with `pty=true`, then `process(action='wait', timeout=60)` and read the log for the URL.
- Always kill old tunnels first: `kill $(pgrep -f 'ssh.*localhost.run') 2>/dev/null`
- The URL changes every session. The systemd service is the permanent method.
- Tunnel may return 503 for the first 30 seconds while TLS termination propagates.

See `static-site-deployment` skill for full tunnel reference.

### Stage 2: Surge.sh Deploy (Legacy, HTML-only)

```bash
cd ~/mission-control
npx surge ./src mission-control-hermes.surge.sh
```
Static-only — the API won't work on Surge (no Python backend). The dashboard falls back to the embedded snapshot.

## Tabbed Layout Architecture

The user prefers tabbed navigation over long-scrolling single pages. The dashboard uses:

```html
<div class="tabs">
  <div class="tab active" onclick="switchTab('overview')">📊 Overview</div>
  <div class="tab" onclick="switchTab('tasks')">📋 Tasks</div>
  <div class="tab" onclick="switchTab('hermes')">🖥️ Hermes Self</div>
  <div class="tab" onclick="switchTab('openclaw')">🔧 OpenClaw</div>
  <div class="tab" onclick="switchTab('proxmox')">🔲 Proxmox</div>
</div>
<div class="tab-content active" id="tab-overview">...</div>
<div class="tab-content" id="tab-hermes">...</div>
<div class="tab-content" id="tab-openclaw">...</div>
```

JavaScript `switchTab()` toggles active class — no URL routing, single-page app pattern.

### Design Preferences for This User

### Timezone
**Always show local time (BST/GMT), not UTC.** The user is UK-based (Europe/London). The header clock and 'last updated' timestamps use `toLocaleString('en-GB')` and auto-detect the timezone abbreviation via `Intl.DateTimeFormat`. Never hardcode UTC.

### Tabbed Layout (Not Scrolling)\nThe user **dislikes long-scrolling single pages**. Always use tabbed navigation for dashboard content. Each tab focuses on one system aspect. This applies to any new page or dashboard this user might request.\n\n### Navigation Structure (V4.1+)\nThe sidebar uses two nav groups:\n- **MONITOR** — system observability (Overview, Hermes Self, OpenClaw, Proxmox)\n- **MANAGE** — operations & knowledge (Tasks, Content, Calendar, Projects, Memory, Docs, Team, Visual)\n\nBoth groups are rendered by a reusable `NavGroup` component that takes a title, items array, and the current pathname. Active nav items get the primary purple background; inactive items get a hover-to-purple treatment.

### Interactive / Full Drill-Down — Every Data Point
The user expects **every data point** to be clickable. This is not optional — static numbers without drill-down are considered incomplete. The rule is: if it's a number, it must open a modal with detail.

Coverage must be complete across ALL surfaces:

**V3 Python version surfaces:**
- **Metric cards** (6 per tab) — every one has an `onclick`. No card uses the conditional `${m.click ? ...}` pattern. All cards always clickable.
- **Table rows** — every meaningful value in an info-table has a `<a>` drill-down link with ›
- **Agent pane 4-grid** — Tokens, API Calls, Memory, Disk in the Hermes card AND Disk, Memory, Uptime, Services in the OpenCrawl card all must be clickable to appropriate drill-downs
- **Detail rows** — Cron Jobs, Skills rows already clickable via `showCronDetail()`/`showSkillsDetail()`
- **VM/CT list** — every VM/CT item clickable to VM detail modal
- **Activity timeline** — every timeline-item clickable to `showActivityDetail(idx)`
- **Agent Services list** — every agent item maps initial to a drill-down function (H→System, O→Worker, C→Cron, T→Token, G→System, X→Customer, D→Worker, P→PveSystem)

**V4 Next.js version surfaces (React with `fetchDrill(key)`):**
- **5 metric cards** — Tokens→`fetchDrill('tokens')`, API Calls→`fetchDrill('api')`, Skills→loadDrillDown('skills'), Cron→loadDrillDown('cron'), System→`fetchDrill('system')`
- **9 Agent avatars** — each maps initial letter to drill key (H→system, O→worker, C→cron, T→tokens, P→pve, etc.)
- **7 Activity timeline items** — all clickable via `fetchDrill('sessions')`
- **All 8 Services** — displayed with status dot, not clickable (metadata-tier, per user expectation)

**Pitfall — wrong drill-down mappings in V4 Next.js Overview page (fixed 2026-05-27).** The original code had:
- Tokens card → `loadDrillDown("cron")` — WRONG, showed cron modal
- API Calls card → `loadDrillDown("errors")` — WRONG, showed error modal
- System metric → didn't exist (was "Agents" with no onClick)

**Fix:** Define a `loadDrillDown(type)` function that dispatches to the correct fetch:
```typescript
const loadDrillDown = async (type: string) => {
  if (type === "cron") { setCronData((await fetchCron()).jobs); setCronOpen(true); return; }
  if (type === "skills") { setSkillsData(await fetchSkills()); setSkillsOpen(true); return; }
  if (type === "errors") { setErrorData(await fetchErrors()); setErrorsOpen(true); return; }
  if (type === "tokens" || type === "cost" || type === "api" || type === "system" || type === "worker") {
    setDrillData(await fetchDrill(type));
    // Open the appropriate modal
    if (type === "tokens") setTokenOpen(true);
    else if (type === "api") setApiOpen(true);
    else if (type === "system") setSystemOpen(true);
    else if (type === "worker") setWorkerOpen(true);
  }
};
```

**Pitfall — `fetchDrill(key)` returns data for ALL drill keys but the React modal state is per-key.** Each drill type needs its own `useState<boolean>` for the modal visibility. Define a reusable `<DrillModal>` component that accepts an `open` and `onClose` prop and renders the same `drillData` state — keeps the code DRY:

```tsx
const DrillModal = ({ open, onClose }: { open: boolean; onClose: () => void }) => (
  <Modal open={open} onClose={onClose} title={drillData?.title || ""}>
    <div className="space-y-1">
      {drillData?.rows?.map(([label, value], i) => (
        <div key={i} className="flex items-center justify-between border-b border-lo-border py-1.5">
          <span className="text-lo-text-muted text-xs">{label}</span>
          <span className={`font-mono text-xs text-right ${
            String(value).startsWith("$") ? "text-lo-warning" : /* ...color logic... */ ""
          }`}>{value}</span>
        </div>
      ))}
    </div>
  </Modal>
);
```

**Pitfall — TypeScript type error when using object literals as index lookup.** A priority sort like:
```typescript
const pr = { high: 0, medium: 1, low: 2 };
return (pr[a.priority] ?? 1) - (pr[b.priority] ?? 1);
```
Fails at build time with: `Type error: Element implicitly has an 'any' type because expression of type 'string' can't be used to index type '{ high: number; medium: number; low: number; }'.`

**Fix:** Explicitly type the map with `Record<string, number>`:
```typescript
const pr: Record<string, number> = { high: 0, medium: 1, low: 2 };
```

All metric cards have `cursor: pointer` in CSS by default (`.metric-card { cursor: pointer; }`). No card is ever left without an onclick handler.

### Naming: All drill-down functions use `show<X>Detail()` pattern for consistency.

### API Source
The dashboard's JS must use `const API = '/api'` (same-origin relative URL). Never hardcode an external URL like `https://some-service.deno.dev` — that was the old pattern and it broke when the external API returned stale data.

## Tab Contents

**📊 Overview**: 6 metric cards (tokens, cost, API calls, skills, uptime, worker), dual agent panes with metrics and detail rows, activity timeline, agent services list, quick actions panel.

**🖥️ Hermes Self**: 6 metric cards (gateway, latency, error rate, sessions, cron, skills), gateway/system info table, API performance table, error log table, sessions & cron table.

**🔧 OpenClaw**: Status banner + Save Stats button, 3 metric rows (bot pools, key & provisioning, customers & templates), **Worker Node** health panel (uptime, mem%, disk%, services, load avg + MEM progress bar), **Container Stack** panel (Docker status + containers count, Ollama status + models count). The Worker Node panel mirrors the Hermes Self system panel layout — same border/row/padding structure, same PixelProgressBar.

**🔲 Proxmox**: 6 metric cards (CPU, memory, VMs running/stopped, uptime, status), node status table, full VM/CT list with VMID, name, mem, disk, vCPU. Click any VM for drill-down detail with labels (e.g. "This is the Hermes agent VM").

### Data Source: Proxmox API
The Proxmox tab queries the PVE API at `192.168.1.6:8006` via the observability collector using `urllib.request`:
- Token from `hermes-vault get PROXMOX_API_TOKEN` and `PROXMOX_URL`
- Endpoints: `/nodes/pve1/status` (node CPU/memory/uptime) and `/cluster/resources?type=vm` (all VMs/CTs)
- Token stored in vault: `PVEAPIToken=hermes2@pve!api=19b5fd1b-...`
- See `proxmox-host-creation` skill for full API reference

## Live Data Pattern

- The HTML embeds `window.__SNAPSHOT_DATA` — a static dataset built at deploy time
- On load, JS tries `fetch(API_URL)` from the live endpoint
- If the API is unreachable, it falls back to the snapshot
- This means the dashboard always renders something useful, even without the Python server
- See `references/live-data-pattern.md` for the full architectural pattern

## Drill-Down Modal Pattern

Any metric card or detail row can open a modal with deeper detail. The pattern:

### 1. Add an API endpoint in `server.py`

```python
if path == "/api/cron" or path == "/api/cron/":
    self.send_response(200)
    self.send_header("Content-Type", "application/json")
    self.send_header("Access-Control-Allow-Origin", "*")
    self.end_headers()
    self.wfile.write(cron_path.read_bytes())
    return
```

Register the route BEFORE the static-file handler at the bottom of `do_GET()`. Each drill-down endpoint reads from a local file (jobs.json, skills dir, etc.) and returns JSON inline.

### 2. Make every metric card clickable (always — no conditional)

```javascript
{l:'Cron Jobs', v:count, c:'purple', s:'click to drill down →', click:'showCronDetail()'},
// NEVER leave click:null — every card must drill down to something
```
Then in the `.map()`: `` `${m.click}` `` — always a function, no conditional. Every metric card must have an onclick handler.

### 3. Info table row drill-down links

Every info-table row that has a meaningful value (count, name, status badge) gets a `<a>` drill-down link with a › arrow. Only purely static/descriptive rows (IP, version string) can stay plain.

```javascript
// Good — drillable
['Memory', `<a href="#" onclick="showPveMemDetail();return false"
  style="color:var(--text-secondary);text-decoration:none">
  ${used} GB / ${total} GB ›</a>`],

// Also good — static, stays plain
['Version', pve.version || 'N/A'],
```

### 4. Activity timeline — clickable items

Add `cursor: pointer` and hover effect to `.timeline-item` in CSS:

```css
.timeline-item { cursor: pointer; border-radius: 8px; margin: 0 -8px; padding: 7px 8px; }
.timeline-item:hover { background: rgba(108,140,255,0.06); }
```

In the render function, pass the array index:
```javascript
d.activity.map((a, i) =>
  `<div class="timeline-item" onclick="showActivityDetail(${i})">...</div>`
).join('');
```

The `showActivityDetail(idx)` modal shows the selected event in detail plus a list of all events for context.

### 5. Agent Services list — clickable items

Map each agent's initial to the appropriate drill-down function:

```javascript
const clickMap = {
  'H': 'showSystemDetail()',   // Hermes
  'O': 'showWorkerDetail()',   // OpenCrawl
  'C': 'showCronDetail()',     // Cron
  'T': 'showTokenDetail()',    // Tokens
  'G': 'showSystemDetail()',   // Gateway
  'X': 'showOclaCustomerDetail()', // OpenClaw
  'D': 'showWorkerDetail()',   // Docker
  'P': 'showPveSystemDetail()', // Proxmox
};
```

Add CSS:
```css
.agent-item { cursor: pointer; border-radius: 8px; margin: 0 -8px; padding: 10px 8px; }
.agent-item:hover { background: rgba(108,140,255,0.06); }
```

### 6. Add the modal HTML

```html
<div class="modal-overlay" id="drillModal" onclick="if(event.target===this)closeModal()">
  <div class="modal">
    <div class="modal-header">
      <div class="modal-title" id="modalTitle">📋 Details</div>
      <button class="modal-close" onclick="closeModal()">✕</button>
    </div>
    <div class="modal-body" id="modalBody"></div>
  </div>
</div>
```

### 7. Add the fetch-and-render function

```javascript
async function showCronDetail() {
  openModal('⏰ Title', '<div>Loading...</div>');
  try {
    const r = await fetch('/api/cron'); const d = await r.json();
    // Build HTML table, assign to document.getElementById('modalBody').innerHTML
  } catch(e) {
    document.getElementById('modalBody').innerHTML = '<div>Failed</div>';
  }
}
```

### 8. Modal helpers

```javascript
function openModal(title, bodyHtml) { /* set title + body, add 'open' class */ }
function closeModal() { /* remove 'open' class */ }
document.addEventListener('keydown', e => { if(e.key === 'Escape') closeModal(); });
```

### 9. Safe HTML rendering for raw log lines

When displaying raw log lines or untrusted text in modals, escape HTML to prevent XSS:

```javascript
function escHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}
```

Use it like: `` `<div>${escHtml(rawLogLine)}</div>` ``

### Unified `showDeepDrill(key)` Pattern (MC v4)

In MC v4, a single unified drill-down function replaces many individual `showXDetail()` functions. Define it once, use it everywhere:

```javascript
async function showDeepDrill(key) {
  openModal('📊 Loading...', '<div>Loading...</div>');
  try {
    const r = await fetch(`/api/drill/${key}`);
    const d = await r.json();
    if (d.error) { /* show error */ return; }
    let h = `<div style="margin-bottom:12px;font-weight:600;">${d.title}</div>`;
    if (d.rows && d.rows.length) {
      h += `<table class="info-table">`;
      d.rows.forEach(r => {
        h += `<tr><td>${r[0]}</td><td>...</td></tr>`;
      });
      h += `</table>`;
    }
    document.getElementById('modalBody').innerHTML = h;
  } catch(e) { /* show error */ }
}
```

**Server side:** `GET /api/drill/:key` returns `{title: string, headers: [string, string], rows: [[string, string], ...]}` built from the observability snapshot. Available keys: `tokens`, `cost`, `api`, `system`, `worker`, `cron`, `skills`, `errors`, `sessions`, `pve`, `ocla_customers`.

**Migration from old pattern:** When replacing old `showTokenDetail()`, `showSystemDetail()`, etc., search the file for EVERY occurrence of each function name. The 7 Overview tab surfaces are listed under Pitfalls above. After migration, old function definitions remain as dead code — they're harmless but can be removed for cleanliness.

### Existing drill-down endpoints for reference

| Modal | API endpoint | Data source |
|-------|-------------|-------------|
| Cron Jobs | `/api/cron` | `~/.hermes/cron/jobs.json` |
| Skills | `/api/skills` | `~/.hermes/skills/` directory walk |
| Error Log | `/api/errors` | `~/.hermes/data/observability.json` → mainAgent.errors.recentErrors |
| API Breakdown | _(from main API)_ | `apiMetrics.providers` in observability snapshot |
| Token Detail | _(from main API)_ | mainAgent.tokens in observability snapshot |
| Cost Detail | _(from main API)_ | mainAgent.tokens + balance.records |
| System Info | _(from main API)_ | mainAgent + gateway fields |
| Worker Detail | _(from main API)_ | openCrawl fields + docker + ollama |
| Session Detail | _(from main API)_ | sessions.today + sessions.total |
| Activity Detail | _(from main API)_ | activity[] array item by index |
| PVE System | _(from main API)_ | proxmox fields (cpuModel, cores, version, uptime) |
| PVE Memory | _(from main API)_ | proxmox.memUsedGB, memTotalGB, memPct |
| PVE VM Overview | _(from main API)_ | proxmox.vms[] filtered by status |
| PVE VM Detail | _(from main API)_ | proxmox.vms[].find(vmid) |
| OpenClaw Customers | _(from main API)_ | openClaw fields |
| OpenClaw Readiness | _(from main API)_ | openClaw fields (7 checks) |
| OpenClaw Bot Pool | `/api/tg-bots`, `/api/dc-bots` | bot pool JSON files |
| OpenClaw Key Pool | _(from main API)_ | openClaw.keyPoolReady, defaultKeySet |
| OpenClaw Templates | `/api/ocla-templates` | `~managed-agent/configs/*.yaml` |
| OpenClaw Scripts | _(from main API)_ | openClaw.provisioningScripts + hardcoded list |
| **Tasks List** | `/api/tasks` | `~/.hermes/data/mc-tasks.json` (auto + user merged) |
| **Task Detail** | `/api/tasks/:id` | Single task from mc-tasks.json |
| **Task Notes** | `/api/tasks/:id/notes` | Notes array from task object |
| **Deep Drill (any)** | `/api/drill/:key` | Structured `{title, headers, rows}` — unified drill endpoint |

Functions ending in `Detail()` that fetch from the main API just re-fetch `/api` — no separate endpoint needed. Functions fetching structured data (cron, skills, errors, bot pools, templates) use dedicated API endpoints.

For the V4 Next.js version, the drill-down modal pattern uses React `useState` + Modal component instead of the Python `showXDetail()` JavaScript pattern. See `references/v4-nextjs-drill-down-pattern.md` for the React-specific approach (arrow function body conversion, `data!` non-null assertion, and Modal component pattern).

## Colors

### V3.x — Dark Interstellar Theme

| Role | Dark hex |
|------|---------|
| Background | `#08080e` |
| Card | `#14141f` |
| Border | `#22223a` |
| Accent | `#6c8cff` |
| Green (good) | `#34d399` |
| Amber (warning) | `#fbbf24` |
| Red (error) | `#f87171` |

### V4.0 — Lonely Octopus Brand (White + Purple + Pixel Accents)

| Role | Hex | Usage |
|------|-----|-------|
| Base | `#FFFFFF` | Page backgrounds |
| BG Alt | `#F5F5F5` | Sidebar, card backgrounds |
| Primary | `#6B21A8` | Headings, active nav, accents |
| Primary Light | `#7C3AED` | Hover states, icon accents |
| Accent | `#A855F7` | Secondary highlights, pixel icons |
| Highlight | `#E905FF` | Tags, special emphasis |
| Text | `#1A1A2E` | Body text |
| Text Muted | `#6B7280` | Secondary text, metadata |
| Border | `#E5E7EB` | Card borders, dividers |
| Success | `#22C55E` | Green status dots |
| Warning | `#F59E0B` | Amber status |
| Error | `#EF4444` | Red status |
| Info | `#3B82F6` | Blue accents |

### POST Routes (Tasks Tab)

Three POST endpoints for task CRUD + notes. Register them in `do_POST()`:

```python
def do_POST(self):
    path = urllib.parse.urlparse(self.path).path
    if not _check_auth(self.headers): return _require_auth(self)
    
    content_len = int(self.headers.get("Content-Length", 0))
    body = self.rfile.read(content_len) if content_len > 0 else b"{}"
    data = json.loads(body) if body else {}
    
    # Create task
    if path == "/api/tasks":
        task = {
            "id": f"task_{uuid.uuid4().hex[:8]}",
            "title": data.get("title", ""),
            "description": data.get("description", ""),
            "status": "pending",
            "priority": data.get("priority", "medium"),
            "category": data.get("category", "general"),
            "source": "user",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "notes": [],
        }
        stored.append(task)
        _save_tasks(stored)
        self._json_response(task)
    
    # Add note
    if path.startswith("/api/tasks/") and path.endswith("/notes"):
        task_id = path.split("/")[3]
        note = {"id": f"note_{uuid.uuid4().hex[:8]}", "text": data["note"],
                "created_at": datetime.now(timezone.utc).isoformat()}
        for t in stored:
            if t["id"] == task_id:
                t.setdefault("notes", []).append(note)
                _save_tasks(stored)
                self._json_response(note)
    
    # Update status
    if path.startswith("/api/tasks/") and path.endswith("/status"):
        for t in stored:
            if t["id"] == path.split("/")[3]:
                t["status"] = data["status"]
                _save_tasks(stored)
                self._json_response({"ok": True, "status": data["status"]})
```

Use `uuid.uuid4().hex[:8]` for short, unique IDs. The `_json_response()` helper sets Content-Type and CORS headers.

### Proxmox VM Controls

The Proxmox tab now has **inline VM control buttons** — Start, Shutdown, and Stop on every VM in the list and in the VM detail modal.

### Architecture

1. **API endpoint**: `GET /api/pve-action/{vmid}/{action}` in `server.py`
2. **Auth**: PVE token loaded from vault via `_load_pve_auth()` function
3. **Type detection**: Reads `type` field (qemu/lxc) from the observability snapshot
4. **Proxmox call**: `POST /nodes/pve1/{type}/{vmid}/status/{action}`

### Actions

| Action | Button Label | Confirmation | Use Case |
|--------|-------------|-------------|----------|
| `start` | ▶ Start | No | Start a stopped VM |
| `shutdown` | ⏻ Graceful Shutdown | Yes (`confirm()`) | Safe stop for running VMs |
| `stop` | ⏹ Force Stop | Yes (`confirm()`) | Kill a hung VM |
| `reboot` | (not in UI) | — | Available via API |

### VM List Display

Each VM in the list shows the appropriate buttons based on its status:

- **Stopped** → ▶ Start button (green)
- **Running** → ⏻ Shutdown (amber) + ⏹ Stop (red)
- **Unknown** → no buttons (status badge only)

### Server-side (`server.py`)

Add the route BEFORE the static-file handler:

```python
# ─── Proxmox VM action ─────────────────────────────────
if path.startswith("/api/pve-action/"):
    parts = path.split("/")
    if len(parts) >= 5:
        vmid = parts[3]
        action = parts[4].split("?")[0]
        try:
            vmid_int = int(vmid)
            ok, msg = _pve_action(vmid_int, action)
            self.wfile.write(json.dumps({"ok": ok, "message": msg}).encode())
        except ValueError:
            self.wfile.write(json.dumps({"ok": False, "message": f"Invalid VMID: {vmid}"}).encode())
    return
```

Use:

```python
import subprocess, os

def _load_pve_auth():
    """Load PVE token from vault using full path (background processes lack PATH)."""
    vault_cmd = os.path.expanduser("~/.local/bin/hermes-vault")
    token = subprocess.run([vault_cmd, "get", "PROXMOX_API_TOKEN"],
        capture_output=True, text=True, timeout=5).stdout.strip()
    url = subprocess.run([vault_cmd, "get", "PROXMOX_URL"],
        capture_output=True, text=True, timeout=5).stdout.strip()
    return token, url

def _pve_action(vmid, action):
    """Execute a Proxmox action on a VM/CT. Returns (success_bool, message_str)."""
    import urllib.request, ssl
    valid = {"start", "stop", "shutdown", "reboot"}
    if action not in valid:
        return False, f"Invalid action: {action}"

    # Read snapshot for VM type
    snap = json.loads(SNAPSHOT_PATH.read_text())
    vms = snap.get("proxmox", {}).get("vms", [])
    vm_type = "qemu"
    for vm in vms:
        if vm.get("vmid") == vmid:
            vm_type = vm.get("type", "qemu")
            break

    url = f"{_PVE_URL}/nodes/pve1/{vm_type}/{vmid}/status/{action}"
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(url, data=b"",
        headers={"Authorization": _PVE_TOKEN}, method="POST")
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        return True, f"{action.capitalize()} command sent to VM {vmid}"
```

**Pitfall — vault path in background processes:** The background Python process may not have `~/.local/bin/` on PATH. Always use the absolute path `os.path.expanduser("~/.local/bin/hermes-vault")` when calling `hermes-vault` from a systemd service or `terminal(background=true)` process. Using just `"hermes-vault"` resolves from the interactive shell's PATH, not the background process's environment.

**Pitfall — Next.js binary path in systemd user service:** `node` is at `~/.hermes/node/bin/node` on this host, NOT `/usr/bin/node`. Always use `%h/.hermes/node/bin/node` in `ExecStart` paths when writing systemd user services for Next.js/Node.js apps. The `%h` placeholder expands to the user's home directory. The `next` CLI is at `%h/mission-control-v4/node_modules/next/dist/bin/next` (not `node_modules/.bin/next` — that symlink can confuse systemd's EXEC resolution). Full service unit pattern:

```ini
[Unit]
Description=MC V4 — Mission Control Next.js dashboard
After=network-online.target

[Service]
Type=exec
WorkingDirectory=%h/mission-control-v4
ExecStart=%h/.hermes/node/bin/node %h/mission-control-v4/node_modules/next/dist/bin/next start --port 3000 --hostname 0.0.0.0
Restart=always
RestartSec=5
Environment=NODE_ENV=production
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

**Pitfall — LiteLLM systemd service path:** `litellm` binary is at `~/.local/bin/litellm` (installed globally via pip, not in a venv). The systemd service should use `%h/.local/bin/litellm` directly. If using a venv's python, verify the venv has litellm installed first — the hermes-agent venv does NOT have it. Use `%h/.local/bin/litellm --config %h/.litellm/config.yaml --port 4000 --host 0.0.0.0 --num_workers 2`.

**Pitfall — Calendar page renders `[object Object]` or crashes:** The `/api/cron` endpoint returns `schedule` as an object (`{kind: "cron", expr: "0 4 * * 0", display: "0 4 * * 0"}`), not a string. The TypeScript `CronJob` interface must type `schedule` as `any` and add `schedule_display?: string`. Rendering `{job.schedule}` directly causes a React crash ("Objects are not valid as a React child"). Use `job.schedule_display || job.schedule?.display || "—"` instead. Similarly, `last_run_at` can be `null` — `new Date(null)` returns epoch (01/01/1970), so the ternary `job.last_run_at ? new Date(job.last_run_at).toLocaleString("en-GB") : "never"` correctly guards against this.

### Client-side (`index.html`)

The `pveAction(vmid, action)` function:

```javascript
async function pveAction(vmid, action) {
  const isDestructive = action === 'stop' || action === 'shutdown';
  if (isDestructive && !confirm(`Are you sure you want to ${action} VM ${vmid}?`)) return;

  openModal(`Action VM ${vmid}`, '<div>Loading...</div>');

  try {
    const r = await fetch(`/api/pve-action/${vmid}/${action}`);
    const d = await r.json();
    document.getElementById('modalBody').innerHTML = `
      <div style="text-align:center;padding:20px;">
        <div style="font-size:48px;">${d.ok ? '✅' : '❌'}</div>
        <div style="font-size:16px;color:${d.ok ? 'var(--green)' : 'var(--red)'}">${d.message}</div>
        <button onclick="closeModal();setTimeout(fetchStatus,500)"
          style="margin-top:16px;padding:8px 20px;">OK, refresh</button>
      </div>`;
  } catch(e) {
    // Show error
  }
}
```

The VM list rendering in `render()` generates inline buttons per VM:

```javascript
const isRunning = vm.status === 'running';
const isStopped = vm.status === 'stopped';
h += `<div style="display:flex;align-items:center;gap:4px;">
  ${isStopped ? `<button onclick="pveAction(${vm.vmid},'start')" ...>▶ Start</button>` : ''}
  ${isRunning ? `<button onclick="pveAction(${vm.vmid},'shutdown')" ...>⏻ Shutdown</button>` : ''}
  ${isRunning ? `<button onclick="pveAction(${vm.vmid},'stop')" ...>⏹ Stop</button>` : ''}
  <span class="agent-status ...">${vm.status}</span>
</div>`;
```

## Live-Rollout Checklist

When making MC v4 changes live:

1. **Build frontend** — `cd ~/mission-control-v4 && npx next build` (catches TypeScript errors, produces optimized bundle)
2. **Copy built assets** — production build is ready, no copy needed
3. **Restart systemd services** — `sudo systemctl restart mc-backend mc-frontend`
4. **Verify locally** — `curl -s http://localhost:3000/ | grep "Mission"` and `curl -s http://localhost:3000/api/tasks | head -c 50`
5. **Update dev-site** — edit `~/dev-site/src/pages/mission-control.astro` if URL changed, build with `npx astro build`, deploy with `npx vercel --prod --token $(cat ~/.vercel/auth.json | python3 -c "import json,sys; print(json.load(sys.stdin)['token'])")`
6. **Update AGENTS.md and README.md** in `~/mission-control-v4/`
7. **Update persistent memory** — replace old MC entry with new details
8. **Verify tunnel** — `curl -s https://<tunnel-url>/api/`

### Stage 0: Systemd User Service (Hermes VM — Legacy)

See the service unit section above for the original single-host deployment.

### Stage 1: Hermes Host + Basic Auth (Current — Preferred)

The MC server runs **on the Hermes host** (where the collector writes data) with Basic Auth in Python — no nginx, no separate web LXC needed.

**Architecture:**
```
Internet → localhost.run tunnel → Hermes Host 192.168.1.121:8081 (Python MC server with Basic Auth)
```

**Why this approach:**
- The collector runs on Hermes host → snapshot file exists → live data
- No SSH access issues (no separate LXC to manage)
- No nginx needed (auth is in Python)
- No sudo required — runs as user process with watchdog cron

**Setup:**
1. The MC server (`server.py`) already runs on the Hermes host (port 8081) with `_check_auth()` + `_require_auth()` in `do_GET()`
2. Tunnel via localhost.run:
   ```bash
   ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 \
     -R 80:localhost:8081 nokey@localhost.run
   ```
3. Watchdog cron (every 5m) keeps it alive: `hermes cron` with `mc-watchdog.sh`
4. Access: `https://<hash>.lhr.life` with Basic Auth credentials

**Creds:** `mc` / `MissionCtrl2026!` (set via `MC_USER`/`MC_PASS` env vars)

### Stage 2: Web LXC + nginx (Deprecated — Data Sync Issue)

**⚠️ DEPRECATED:** The web LXC approach has a fundamental data-source mismatch. The collector runs on the Hermes host and writes `observability.json` there. The MC server on web LXC looks for this file locally and finds nothing, returning all zeros.

To make this work, you'd need to add a data-sync step (scp/rsync in the collector cron) or change the MC server to fetch data from an API on the Hermes host. Neither has been implemented.

The deployment details are preserved in `references/web-lxc-deployment.md` for reference (pct push, nginx config, PVE env vars) but do NOT use this as the primary deployment method.

**Architecture (for reference):**
```
Internet -> localhost.run tunnel -> Hermes VM (SSH -R 80:192.168.1.200:80)
                                 -> Web LXC 192.168.1.200:80 (nginx)
                                 -> Web LXC localhost:8081 (Python MC server — NO DATA)
```

## Data Sources (Summary)

| Data | Source | Method |
|------|--------|--------|
| Token counts | `~/.hermes/logs/agent.log` | Regex parse (python) |
| API latency | `~/.hermes/logs/agent.log` | Regex parse (python) |
| API error rate | `~/.hermes/logs/agent.log` | Regex parse (python) |
| Error counts (24h) | `~/.hermes/logs/agent.log` | Line count (ERROR) |
| System uptime | `/proc/uptime` | Python read |
| Memory usage | `/proc/meminfo` | Python read |
| Disk usage | `df /` | subprocess |
| Gateway status | `systemctl --user is-active hermes-gateway` | subprocess |
| Skills count | `~/.hermes/skills/` | os.walk |
| Skills breakdown | `~/.hermes/skills/` (via `/api/skills`) | Dir walk by category |
| Cron jobs | `~/.hermes/cron/jobs.json` | JSON parse |
| Cron detail | `~/.hermes/cron/jobs.json` (via `/api/cron`) | JSON parse |
| Sessions (today/total) | `hermes sessions list --json` | subprocess |
| DeepSeek balance | `~/.hermes/data/deepseek-history.json` | JSON parse |
| Error details (last 10) | `agent.log` via collector | Regex `ERROR|Traceback` lines (see `references/error-api-metrics-collection.md`) |
| API provider breakdown | `agent.log` via collector | Regex `provider=` from API call lines (see `references/error-api-metrics-collection.md`) |
| Worker metrics | SSH matth@192.168.1.137 | `~/scripts/worker-metrics.sh` |
| Bot pools | `~managed-agent/configs/*-bot-pool.json` | JSON parse |
| Key pool | `~managed-agent/configs/llm-key-pool.json` | JSON parse |
| Customers | `~managed-agent/customers/` | Directory scan |

## Related Skills

- **`managed-agent-service`** — Provisions, configures, and manages the Hermes Agent / OpenClaw instances that the OpenClaw tab monitors. The dashboard and the provisioning service are designed as a closed feedback loop: provision via `managed-agent-service`, monitor via `mission-control-dashboard`.
- **`static-site-deployment`** — Covers alternative deployment methods (Surge.sh, Cloudflare Tunnel, GitHub Pages) and localhost.run tunnel troubleshooting.
- **`system-architecture-documentation`** — Maintains the ARCHITECTURE.md that the dashboard's "System Architecture" view references.

### Tasks Tab (MC v4 — Vanilla HTML/JS)

**Added in MC v4 (2026-05-27).** The Tasks tab provides a filterable action-item board with inline expand/collapse, status updates, and persistent notes.

**User context:** "Under tasks I cannot drill and add notes to tasks waiting for me." — Fixed in MC v4. See `references/tasks-notes-drilldown-pattern.md` for the Python version implementation.

**V4 Next.js version:** The tasks page at `src/app/tasks/page.tsx` was rewritten from a hardcoded array to fetch from `/api/tasks` (proxy to Python backend). Tasks are expandable with full description, status buttons, and an inline note input. See `references/v4-nextjs-tasks-api-pattern.md` for the React-specific implementation (state management, note input pattern, filter mapping, pitfalls).

**Tab contents:**
- Filter bar (5 buttons: All, Pending, In Progress, Done, High Priority)
- "New Task" button → inline form (title, description, priority, category)
- Task list: cards with expandable detail panels
- Detail panel: status buttons, description, tags, notes section with inline input

**Architecture:**
- Persistent JSON store at `~/.hermes/data/mc-tasks.json`
- Auto-generated tasks: 7 observability signals (API errors, stopped VMs, low balance, etc.)
- User tasks: via POST /api/tasks
- Merge strategy: auto tasks re-created each call but preserve user notes/status
- Sort: priority (high first), then creation date (newest first)

### Deep Drill-Down System (MC v4)

**Added in MC v4 (2026-05-27).** Replaced individual `showXDetail()` functions with a unified `GET /api/drill/:key` endpoint.

**User context:** "I cannot drill down on the overview tab." — Fixed by routing all 6 Overview cards and all 6 Hermes Self cards through `showDeepDrill(key)`.

**Available drill keys:** `tokens`, `cost`, `api`, `system`, `worker`, `cron`, `skills`, `errors`, `sessions`, `pve`, `ocla_customers`

Each returns `{title, headers, rows}` — a single JS function renders it as an info-table in the modal. No more hardcoded JS functions per drill type.

## Reference Files

- `references/live-data-pattern.md` — Reusable static+live dashboard architecture pattern
- `references/error-api-metrics-collection.md` — Error log parsing, API provider breakdown, `/api/errors` endpoint pattern
- `references/proxmox-api-collection.md` — PVE API endpoints, auth, data mapping, VM labels, pitfalls
- `references/web-lxc-deployment.md` — Full deployment details for the web LXC host (VM 200): static IP, nginx config, service unit, file transfer via pct push, tunnel, PVE auth env vars
- `references/mc-v4-design-brief.md` — V4.0 design brief + full build log: Next.js + Tailwind, API proxy pattern, components, Lonely Octopus palette, Tailwind v4 setup, retro/pixel CSS utilities
- `references/notes-index-updater-pattern.md` — No-agent Discord cron pattern for maintaining a pinned link directory in #notes
- `references/tasks-notes-drilldown-pattern.md` — Tasks tab drill-down + notes UX pattern (user-reported gap, fixed)
- `references/v4-nextjs-drill-down-pattern.md` — V4 React-specific drill-down pattern (arrow function conversion, `data!` assertion, Modal component)
- `references/v4-nextjs-tasks-api-pattern.md` — V4 Next.js Tasks page: API-backed expand/collapse, inline notes, status management, TypeScript pitfalls, per-task note input state
## V4.0 (Built — 2026-05-26)

See `references/mc-v4-design-brief.md` for the complete V4 design spec, architecture diagram, API proxy pattern, component library, colour palette, Tailwind v4 setup, and build notes.

**What changed from V3:**
- Frontend rebuilt in **Next.js 16 + Tailwind CSS v4** (TypeScript)
- **Single-page Python HTML replaced** with React component tree (Sidebar, StatusCard, Modal, AgentAvatar, PixelProgressBar)
- **API proxy pattern** — Next.js route handler at `src/app/api/[[...slug]]/route.ts` forwards requests to the Python backend, injecting Basic Auth credentials. This keeps the Python server protected while the frontend doesn't expose auth.
- **Lonely Octopus brand palette** applied: deep purple (`#6B21A8`), bright purple (`#A855F7`), lavender (`#E905FF`), white + light gray backgrounds
- **Linear + retro gaming** visual style: pixel grid backgrounds, pixel borders, pixel progress bars, pixel art agent avatars
- **What stayed the same:** Python collector cron (every 5 min), Python API server (`server.py` on port 8081), all existing drill-down endpoints, Basic Auth, Proxmox VM actions

**Location:** `~/mission-control-v4/`
**Running:** Port 3000 (`npx next dev -p 3000`) · **`http://192.168.1.121:3000`** (network-accessible)
**API backend:** Python server on port 8081 (unchanged, still requires Basic Auth)

### File-Reading API Routes (Next.js, bypassing catch-all proxy)

When a Manage tab needs to read a file from disk (e.g. MEMORY.md, USER.md), create a specific Next.js API route handler. These take precedence over the `/api/[[...slug]]` catch-all because Next.js matches more specific routes first.

**Pattern (`src/app/api/memory-file/route.ts`):**
```typescript
import { NextResponse } from "next/server";
import { readFileSync } from "fs";
import { homedir } from "os";

export async function GET() {
  try {
    const path = `${homedir()}/.hermes/memories/MEMORY.md`;
    const content = readFileSync(path, "utf-8");
    return NextResponse.json({ content, path, size: content.length });
  } catch (e) {
    return NextResponse.json({ content: "File not found.", size: 0 });
  }
}
```

This reads directly from the filesystem (same machine) — no proxy, no auth header needed. The page component then fetches `/api/memory-file` and renders the content.

**User corrections to manage tabs (2026-05-26):** See the V4.1 tab table above for corrected data source mappings. These are deliberate user-directed changes, not placeholders.

**Location:** `~/mission-control-v4/`\n**Running:** Port 3000 (`npx next dev -p 3000`) · **`http://192.168.1.121:3000`** (network-accessible)\n**API backend:** Python server on port 8081 (unchanged, still requires Basic Auth)\n\n### V4.1 — 12 Tabs (Monitor + Manage)\n\nOn 2026-05-26, the sidebar was split into two sections and **8 new Manage tabs** were added:\n\n**MONITOR** (system observability)\n| Tab | Route | Purpose |\n|-----|-------|---------|\n| Overview | `/` | KPI cards, agents grid, services list, activity timeline |\n| Hermes Self | `/hermes` | Gateway, sessions, latency, errors, system info |\n| OpenClaw | `/openclaw` | Bot pools, key pool, provisioning, customers |\n| Proxmox | `/proxmox` | CPU/mem/VMs, start/stop/reboot controls |\n\n**MANAGE** (operations & knowledge)\n| Tab | Route | Purpose |\n|-----|-------|---------|\n| Tasks | `/tasks` | Filterable task list with priority, assignee, due dates |\n| Content | `/content` | Resource grid by status (published/draft/review) |\n| Calendar | `/calendar` | Weekly event view with type-coded sidebars |\n| Projects | `/projects` | Progress cards with pixel progress bars |\n| Memory | `/memory` | Persistent memory entries (user + agent) |\n| Docs | `/docs` | Document browser with category filter |\n| Team | `/team` | Agent + human cards with online status dots |\n| Visual | `/visual` | KPI grid, skill bars, service clusters, activity flow |\n\n**Key user corrections (2026-05-26):** The manage tab data sources were corrected based on direct user feedback. Calendar was redirected to show cron jobs from `/api/cron`. Memory was redirected to show actual MEMORY.md + USER.md files from disk via dedicated API routes. Team was redirected to show the agents roster with live status from the dashboard API. Visual was redirected to become an "Agent Office" visual map with station cards and connection lines. Tasks was redirected to be a comprehensive "all tasks owner" filtered board.

**Component summary:**\n- `Sidebar.tsx` — Two nav groups (`NavGroup` component), Monitor (4) + Manage (8), scrollable with sticky header/footer\n- `StatusCard.tsx` — Metric card with icon, value, label, subtext, status dot, and `onClick`\n- `Modal.tsx` — Reusable drill-down modal with Escape-key close and overlay click dismiss\n- `PixelProgressBar.tsx` — 8px tall retro bar with pixel border + fill\n- `AgentAvatar.tsx` — Pixel-art character block with status indicator\n\nAll Manage pages currently use **sample data** — they're UI shells ready to wire to real backends. The data is defined as typed constants in each page component.\n\nSee `references/manage-tabs-architecture.md` for data shapes, component patterns, and wiring guide.

## Save Stats — Snapshot to Discord #notes (2026-05-26)

The OpenClaw page has a **💾 Save Stats** button that captures current OpenClaw + OpenCrawl
stats and posts a formatted snapshot to the `#notes` Discord channel.

### API Route (`src/app/api/save-stats/route.ts`)

A dedicated Next.js POST handler reads `DISCORD_BOT_TOKEN` from `~/.hermes/.env` directly
(not via the proxy backend), formats the stats as markdown, and posts to the Discord API.

Key details:
- Uses an inline `loadDotenv()` helper (vanilla TypeScript, not `python-dotenv`) to parse the `.env` file
- Channel ID `1508966625494437928` is hardcoded — the notes channel is permanent
- 2000-char Discord message limit applies
- Returns `{ ok, messageId, channel }` to the frontend
- `loadDotenv` must handle `KEY=VALUE` parsing with comments/blank-line skipping and quote stripping

### Button Component

The "💾 SAVE STATS" button sits next to the OpenClaw status banner. Uses `saving`/`saved` state:
- **Saving:** button disabled, shows "⬡ SAVING..."
- **Saved:** green glow for 3 seconds ("✅ SAVED")
- **Default:** "💾 SAVE STATS"

Snapshot format sent to Discord includes OpenClaw (ready, customers, bot pools, key pool, provisioning) and OpenCrawl (reachable, mem, disk, services, uptime, docker, ollama) as a structured bullet list.

## Ported OpenClaw Skills (2026-05-26)

On 2026-05-26, **31 skills** were ported from the [OpenClaw prompts & skills](https://github.com/seedprod/openclaw-prompts-and-skills) repository into `~/.hermes/skills/`, bringing the total from 127 to 158 skills.

| Category | Skills |
|----------|--------|
| `utilities/` (12) | weather, summarize, model-usage, session-logs, skill-creator, gifgrep, clawhub, mcporter, local-places, goplaces, food-order, ordercli |
| `media/` (13) | video-frames, sag (ElevenLabs TTS), sherpa-onnx-tts, openai-image-gen, openai-whisper, camsnap, spotify-player, blucli |
| `social-media/` (7) | slack, discord, bird (Twitter/X), wacli (WhatsApp), voice-call, gemini |
| `software-development/` (3) | github, tmux |
| `productivity/` (1) | trello |
| `security/` (1) | 1password |
| `creative/` (1) | nano-banana-pro |

Backup saved to `~/skill-backup-20260526-230855/`.

**Pitfall — OpenClaw skills are designed for macOS/Claude Code CLI.** Some reference tools (AppleScript, Things, iMessage) that won't work on Linux. The ported subset above is Linux-compatible. The full repo (52 skills) is available at `/tmp/openclaw-prompts-and-skills/` if needed.

## Current Tunnel (2026-05-27)

The MC dashboard is currently accessible at **`https://17fb2efa61d7e3.lhr.life`** (no auth) via localhost.run tunnel from the Hermes host. Direct access at `http://192.168.1.121:3000` on the LAN.

**No Basic Auth** — removed because the browser's fetch() calls failed silently with Basic Auth enabled. The tunnel URL is unique/random, so auth is not needed.

**⚠️ Critical: The URL changes every time the tunnel restarts.** There is no way to get a permanent URL from anonymous localhost.run — a paid account or a custom domain + Cloudflare tunnel is needed for a fixed endpoint.

**⚠️ Next.js dev server fails to start when port 3000 is still in use.** After killing the old process with `fuser -k 3000/tcp`, wait 2 seconds and verify the port is free (`ss -tlnp | grep 3000`) before starting the new server. A stale process from a previous terminal session that wasn't properly cleaned up causes `EADDRINUSE`. Use the production build (`next build` then `npm start -- -p 3000`) for stability — avoids turbopack HMR issues and ensures TypeScript compilation errors are caught at build time.

### Tunnel Restart Cascade (when making server changes)

When you modify the server (e.g. change auth config, add routes), the following restart sequence is required. **Missing steps produces stale tunnel or dead API:**

1. **Kill the server process** — `kill $(pgrep -f 'server.py') 2>/dev/null`
2. **Kill the tunnel** — `kill $(pgrep -f 'ssh.*localhost.run') 2>/dev/null`
3. **Wait** — brief sleep or verify port is free: `ss -tlnp | grep 8081`
4. **Start the server** — `cd ~/mission-control && python3 src/server.py &` (or via systemd)
5. **Verify server is up** — `curl -s http://localhost:8081/api | python3 -m json.tool`
6. **Start the tunnel** — `ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -R 80:localhost:8081 nokey@localhost.run`
7. **Wait for URL** — the tunnel prints to stdout after 15–45s. Check process output: `process(action='log', session_id='...')`
8. **Verify tunnel** — `curl -s https://<new-url>/api/tasks | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['total'], 'tasks')"`

**Pitfall — tunnel still points at old server if tunnel isn't killed.** If you only kill the server but not the tunnel, the tunnel stays connected to the (dead) port and returns connection refused. Always kill both, start server first, then tunnel.

**Pitfall — the browser caches the failed Basic Auth response.** After removing auth, the browser may still show "ERR_INVALID_AUTH_CREDENTIALS" from a cached 401 response. Clear the browser's cache/site data for the tunnel domain, or use an incognito window. The old URL with embedded credentials (`https://user:pass@host/`) format is also deprecated — Chrome/Firefox strip credentials from sub-resource requests.

### Previous Tunnel URLs (for reference)
- 2026-05-26: `https://57b96bad7380f1.lhr.life`
- 2026-05-27 (session 1): `https://0002b6c7262e99.lhr.life` (with Basic Auth — REMOVED)
- 2026-05-27 (session 2): `https://17fb2efa61d7e3.lhr.life` (Next.js V4)

### Stage 1: Temporary Tunnel Preview (Instant, No Auth)

On 2026-05-26 the skills count in the observability collector increased from ~127 to ~158 due to the OpenClaw skills port. The collector's `/api/skills` endpoint and the dashboard's "Skills" drill-down modal will now report 158 skills across 32 categories.

No collector changes were needed — it dynamically scans `~/.hermes/skills/` on each request.
