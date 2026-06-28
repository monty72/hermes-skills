# MontyGroup Full Architecture — May 2026

> Generated from the May 2026 system-wide architecture audit.
> Three output files were produced for this session:
> 1. `~/dev-site/montygroup-architecture.html` — SVG diagram
> 2. `~/dev-site/ARCHITECTURE.md` — One-page overview
> 3. `~/dev-site/LLD.md` — Full low-level design

## System Inventory (May 2026)

### Hardware Layer
- **Proxmox host:** `192.168.1.6:8006` (64GB RAM, 816GB storage, PVE 9.0.6)
- **Hermes VM:** VM 105, `192.168.1.121`, Debian 13 (trixie), 16 cores, ~16GB RAM
- **Web LXC:** VM 200, `192.168.1.229`, Debian 12, nginx
- **Powerwall 3:** x2 units, `192.168.1.108`, 27 kWh total, 11.5 kW, FW 26.10.3, UK 230V single-phase (G99)
- **Home Assistant:** LXC, `192.168.1.146:8123`, v2026.3.1, 120 components, 123 entities

### Hermes Agent
- **Installation:** `~/.hermes/hermes-agent/`, git clone, v0.14.0-dev
- **Python venv:** `/home/matth/.hermes/hermes-agent/venv/` (Python 3.11)
- **Gateway:** systemd user service, PID 46378, running
- **Connected platforms:** Telegram @MontyHogBot ✅, Home Assistant ✅, Discord ❌ (paused)
- **Model provider:** DeepSeek (`api.deepseek.com/v1`, model `deepseek-chat`)
- **Fallback:** deepseek-v4-pro (auto-escalates on rate limit)
- **Thinking:** disabled
- **Active personality:** kawaii
- **Cron jobs:**
  - Weekly Gateway Restart — Sun 04:00 UTC
  - DeepSeek cost + anomaly — daily 09:00 UTC
- **Scripts:** deepseek-monitor, tunnel-watchdog, HA helper, Tesla OAuth helpers

### Credential Vault
- **Path:** `~/.hermes-vault/vault.json`
- **CLI:** `~/.local/bin/hermes-vault`
- **Encryption:** AES-256-GCM, PBKDF2 600K iterations
- **Passphrase:** in `~/.hermes/.env.local`
- **Stored tokens (12):**
  - DEEPSEEK_API_KEY — $2.71 balance
  - TELEGRAM_BOT_TOKEN — @MontyHogBot
  - HASS_TOKEN — HA at 192.168.1.146:8123
  - PROXMOX_API_TOKEN — hermes2@pve!api
  - PROXMOX_URL — https://192.168.1.6:8006
  - GITHUB_TOKEN — repo scope
  - VERCEL_TOKEN — monty72
  - BRAVE_SEARCH_API_KEY — web search
  - CLOUDFLARE_ACCOUNT_ID — CF account tag
  - CLOUDFLARE_TUNNEL_ACTIVE_SECRET — active tunnel
  - CLOUDFLARE_TUNNEL_HERMES_DEV_SECRET — hermes-dev tunnel
  - CLOUDFLARE_ZONE_MONTYGROUP — zone ID
- **NOTE:** Cloudflare API Bearer token value NOT stored in vault (only token ID documented)

### Managed-Agent Provisioning System
- **Path:** `~/managed-agent/`
- **Scripts:** manage-agent.py, oneshot-provision.py, provision-agent.sh, deprovision-agent.sh, check-health.sh, create-telegram-bot.py, create-discord-bot.py, install-onboarding.py
- **Config templates:** solo.yaml, starter.yaml, pro.yaml, enterprise.yaml
- **Pools:** llm-key-pool.json (EMPTY), telegram-bot-pool.json (EMPTY), discord-bot-pool.json (EMPTY)
- **Customers directory:** EMPTY — no customers provisioned
- **Tiers:** Solo £49, Starter £149, Pro £349, Enterprise £999+
- **Target platforms:** Proxmox LXC, DigitalOcean, Hetzner, customer SSH

### Skills Library
- ~118 skills in categorized directories
- Agent-created: 12 skills (hermes-setup-patterns, provider-usage-tracking, cloudflare-dns, content-site-builder, uk-resource-hub-builder, uk-retail-research, home-assistant-integration, proxmox-health-audit, proxmox-host-creation, uk-energy-research, static-site-deployment, hyprland-debugging)
- Most used: modern-astro-ci-cd-setup (34 uses), tesla-powerwall-local (31), static-site-deployment (28), content-site-builder (26), cloudflare-dns-management (16)

### Dev Site (montygroup.uk)
- **Path:** `~/dev-site/`
- **Repo:** github.com/monty72/montygroup-astro (public)
- **Stack:** Astro 5, TypeScript, Tailwind v4, React 19 islands
- **Pages (14):** Landing, Agile, Bots, Chatbots, Childminding, Energy, Energy Providers, Energy Calculator, EV, Homelab, Matt (portfolio), Mission Control, Skills Marketplace, Skills Browse, Skills Detail
- **CI/CD:** GitHub Actions (ci.yml + deploy.yml) → Vercel auto-deploy
- **Vercel project name:** montygroup-astro
- **DNS:** Cloudflare (montygroup.uk → Vercel CDN, api.montygroup.uk → tunnel)

### API Backends
- **Flask Energy API:** localhost:8000, PID 84791, serves Tesla + Agile + system data
- **Flask Marketplace API:** localhost:5010, PID 92856, SQLite + FTS5 CRUD
- **Cloudflare Tunnel:** `hermes-dev` (ID: 446ffcd9), cloudflared v2026.5.1, PID 81615
- **Tunnel route:** api.montygroup.uk → localhost:8000
- **Second tunnel:** ID c27485f9 (two sets of creds exist)

### Energy Stack
- Tesla Owner API (cloud, token in api.py): ACCESS_TOKEN + REFRESH_TOKEN
- Energy Site ID: 1689543131745218
- Tesla API auth: SSO PKCE flow via tesla_oauth.py scripts
- HA teslemetry integration: present but sensors show "unavailable" (needs re-auth)
- Audi Q6 e-Tron: 94.9 kWh battery, currently showing charging FAULT
- Octopus Agile: imported from API, served via Flask
- NetZero: no HA integration, no local gateway access (pw never found)

### Critical Notes
- Router DNS (192.168.1.254) does NOT resolve montygroup.uk — internal LAN can't access
- Router DNS issue has no workaround found (pihole or unbound suggested but not set up)
- Ghost LXC 103 in Proxmox cluster resource cache — needs root shell `pvesh delete /cluster/config/lxc/103`
- Cloudflare API Bearer token value was never saved to disk
- `~/.hermes/scripts/home_assistant_token.txt` may become stale vs vault
