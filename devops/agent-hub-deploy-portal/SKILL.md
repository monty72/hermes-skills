---
name: agent-hub-deploy-portal
title: Agent Hub — Managed Deploy Portal
description: Full React + Vite portal for one-click agent deployments (Hermes, OpenCrawl). Multi-step wizard, skills marketplace, deployment dashboard, Flask API backend.
version: 2.0.0
author: Hermes Agent
platforms: [linux]
---

# Agent Hub Deploy Portal

## Overview

A complete managed-agent deployment portal: React SPA frontend + Flask API backend + SQLite. Enables one-click deployment of Hermes Agent, OpenCrawl, and custom agents onto customer infrastructure (Docker, Proxmox, VPS, Edge).

## Project Structure

```
~/hermes-deploy-portal/
├── api.py                    # Flask API server (port 5011)
├── serve.py                  # Production proxy: serves SPA + proxies /api
├── requirements.txt          # flask, flask-cors
├── data/
│   ├── schema.sql            # SQLite schema (7 tables, indexes)
│   └── deploy.db             # SQLite database (created by init)
├── scripts/
│   └── init_db.py            # DB init with seed data
├── src/
│   ├── App.tsx               # State-based page routing (no react-router)
│   ├── main.tsx              # Entry point
│   ├── index.css             # Full dark design system (CSS vars)
│   ├── types.ts              # TS types (Agent, SkillPack, Deployment, etc.)
│   ├── api-client.ts         # Centralized HTTP client — all API calls
│   ├── data.ts               # Async fetchers with mock fallback
│   └── components/
│       ├── Sidebar.tsx        # Navigation (Dashboard, Deploy, Deployments, Marketplace, Settings)
│       ├── Dashboard.tsx      # Stats + active deployments table (live from API)
│       ├── DeployWizard.tsx   # Multi-step wizard orchestrator
│       ├── DeploymentsList.tsx # Expandable list with status filters (live from API)
│       ├── SkillsMarketplace.tsx # Browse/search/filter skills (live from API)
│       ├── Settings.tsx       # Config sections
│       └── WizardSteps/
│           ├── Step1Agents.tsx
│           ├── Step2Skills.tsx
│           ├── Step3Target.tsx
│           └── Step4Review.tsx
├── index.html
├── package.json
├── vite.config.ts
└── tsconfig.json
```

## Frontend Architecture

### Design System

Dark theme in `index.css` with CSS custom properties. All tokens overridable for white-label.

| Token | Value | Usage |
|---|---|---|
| `--bg-primary` | `#07070d` | Page background (deep black) |
| `--bg-surface` | `#12121f` | Card surfaces |
| `--accent-purple` | `#a855f7` | Primary action color, selected states |
| `--accent-cyan` | `#22d3ee` | Secondary / info accents |
| `--accent-green` | `#22c55e` | Running/success states |
| `--accent-red` | `#ef4444` | Error states |
| Font | Inter (UI) + JetBrains Mono (code) | |

### Routing

State-based routing in `App.tsx` via a `Page` enum — no react-router dependency. Five pages: dashboard, deploy, deployments, marketplace, settings.

### API Client

`src/api-client.ts` — centralized HTTP client. All calls go through a `request<T>()` function. API_BASE is configurable:

```typescript
// In dev: Vite proxy handles /api → localhost:5011
// In prod: env var VITE_API_URL or fallback to host-relative
const API_BASE = import.meta.env.VITE_API_URL ||
  (import.meta.env.PROD ? 'http://192.168.1.200' : '')
```

### Data Layer

`src/data.ts` exports async fetchers that try the API first, fall back to embedded mock data on failure. Components use `useEffect` + `useState` patterns:

```typescript
const [deployments, setDeployments] = useState<Deployment[]>([])
const [loading, setLoading] = useState(true)

useEffect(() => {
  fetchDeployments().then(d => { setDeployments(d); setLoading(false) })
}, [])
```

### Vite Config

```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: true,        // Required for localhost.run tunnels
    proxy: { '/api': { target: 'http://localhost:5011', changeOrigin: true } },
  },
})
```

## Backend Architecture (Flask API)

### REST Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | GET | Status + DB check |
| `/api/stats` | GET | Dashboard aggregate stats |
| `/api/agents` | GET | Available agent types |
| `/api/skill-packs` | GET | Skill packs with skills, prices |
| `/api/targets` | GET | Deploy targets with config fields |
| `/api/deployments` | GET | All deployments with latest metrics |
| `/api/deployments/:id` | GET | Single deployment detail + metric history |
| `/api/deployments` | POST | Create deployment (stores in SQLite, generates Ansible/Docker Compose artifacts) |
| `/api/deployments/:id/action` | POST | Start/stop/restart |
| `/api/deployments/:id` | DELETE | Remove deployment + related data |
| `/api/marketplace/skills` | GET | All marketplace skills |
| `/api/marketplace/skills/search` | GET | Filtered search (?q=&category=) |
| `/api/deploy/:id/artifacts` | GET | Generated Ansible inventory + Docker Compose |

### Database Schema

SQLite with 8 tables in `data/schema.sql`:
- `agents`, `skill_packs`, `pack_skills`, `deploy_targets`, `target_config_fields`
- `deployments`, `deployment_agents`, `deployment_skills`, `deployment_metrics`
- `marketplace_skills`

Uses WAL mode and foreign keys. Indexed on status, created_at, and deployment_id+recorded_at.

### Key: `init_db.py` path resolution

The script's `__file__` resolves to `<project>/scripts/init_db.py`, so:

```python
# WRONG — PROJECT_DIR becomes /opt instead of /opt/agent-hub-api
SCRIPT_DIR = os.path.dirname(__file__)         # /opt/agent-hub-api/scripts
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)        # /opt (WRONG!)

# CORRECT — use abspath to strip the script name
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))  # /opt/agent-hub-api/scripts
DB_PATH = os.path.join(PROJECT_DIR, 'data', 'deploy.db')  # /opt/agent-hub-api/data/deploy.db
```

## Deployment Methods

### A. Vercel (SPA only — no API)

```bash
cd ~/hermes-deploy-portal
npm run build
VERCEL_TOKEN=$(python3 -c "import json; print(json.load(open('/home/matth/.vercel/auth.json'))['token'])")
npx vercel deploy --prod --token "$VERCEL_TOKEN" --yes
```

Production URL: https://hermes-deploy-portal.vercel.app

Caveat: SPA on Vercel can't reach the local API. Use method C (Python proxy + tunnel) for end-to-end demos, or set VITE_API_URL to a publicly-accessible API endpoint.

### B. Proxmox LXC (full backend)

Deploy Flask API + SQLite on a Proxmox LXC with nginx reverse proxy.

```bash
# 1. Copy API files to container
ssh pve-host "pct push <VMID> /tmp/api.py /opt/agent-hub-api/api.py"
ssh pve-host "pct push <VMID> /tmp/schema.sql /opt/agent-hub-api/data/schema.sql"
ssh pve-host "pct push <VMID> /tmp/init_db.py /opt/agent-hub-api/init_db.py"

# 2. Install deps + init DB
ssh pve-host "pct exec <VMID> -- pip3 install flask flask-cors -q"
ssh pve-host "pct exec <VMID> -- python3 /opt/agent-hub-api/init_db.py"

# 3. Create systemd service
pct exec <VMID> -- bash -c 'cat > /etc/systemd/system/agent-hub-api.service << "EOF"
[Unit]
Description=Agent Hub Deploy Portal API
After=network.target
[Service]
Type=simple
WorkingDirectory=/opt/agent-hub-api
ExecStart=/usr/bin/python3 /opt/agent-hub-api/api.py
Restart=always
RestartSec=5
Environment=PORT=5011
[Install]
WantedBy=multi-user.target
EOF'

systemctl daemon-reload && systemctl enable agent-hub-api && systemctl start agent-hub-api

# 4. Add nginx reverse proxy (/api/ → localhost:5011)
cat > /etc/nginx/sites-available/agent-hub << "NGINX"
server {
    listen 80;
    server_name agent-hub.yourdomain.com;

    location /api/ {
        auth_basic off;
        proxy_pass http://127.0.0.1:5011/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
NGINX
nginx -t && systemctl reload nginx
```

Pitfall: When nginx has `auth_basic` at the server level, API location blocks need `auth_basic off;` or they inherit HTTP Basic Auth and API calls fail.

### C. Python Proxy + localhost.run tunnel (end-to-end demo)

Serves the SPA and proxies API calls from a single port, exposed via localhost.run.

```bash
# 1. Build the SPA
npm run build

# 2. Start the Flask API
python3 api.py &

# 3. Start the proxy server (serve.py — serves dist/ + proxies /api)
python3 serve.py &    # port 5173

# 4. Create tunnel
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 \
  -R 80:localhost:5173 nokey@localhost.run
# → https://<hash>.lhr.life
```

`serve.py` is a Python HTTP server that serves static files from `dist/` and proxies any `/api/*` request to `http://localhost:5011`. Handles GET, POST, DELETE. Resides at the project root.

## Wizard Flow (Frontend)

4-step deployment wizard in `DeployWizard.tsx`:

1. **Select Agents** — multi-select cards (Hermes, OpenCrawl, Custom)
2. **Choose Skills** — Starter ($49), Pro ($149), Enterprise ($499) packs, or none. Bespoke skills CTA for Enterprise
3. **Deploy Target** — Docker, Proxmox VE, Cloud VPS, Edge/RPi. Contextual config fields per target (SSH keys, API tokens, resource allocation)
4. **Review & Deploy** — summary with name, cost, skills list, target config. Submits POST to `/api/deployments`. Returns generated Ansible inventory + Docker Compose.

## Pitfalls

- **Vite verbatimModuleSyntax** — tsconfig enforces `import type` for type-only imports. `import { AgentOption }` fails; use `import type { AgentOption }`.
- **React 18 JSX transform** — `import React from 'react'` is unused in most component files.
- **Self-referencing mock data** — `SKILL_PACKS[0].skills` inside the array literal fails because the array isn't initialized yet. Define child arrays as separate consts.
- **init_db.py path resolution** — `os.path.dirname(__file__)` on a script in a subdirectory gives the wrong project root when chained. Use `os.path.dirname(os.path.abspath(__file__))` when the script IS in the project root.
- **Vite allowedHosts** — localhost.run tunnel URLs are blocked by Vite's `server.allowedHosts` check. Set `allowedHosts: true` in vite.config.ts when using tunnels.
- **nginx auth_basic inheritance** — If the server block has `auth_basic`, all location blocks inherit it. Add `auth_basic off;` to API proxy locations.
- **pct push no --force** — `pct push <vmid> <src> <dest>` overwrites existing files automatically; no `--force` flag.
- **Vercel Python serverless + SQLite** — Vercel's serverless runtime has an ephemeral/read-only filesystem. Don't try to deploy the Flask API with SQLite on Vercel; use Proxmox or another VPS for the backend.
