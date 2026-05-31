---
name: opencrawl-worker-delegation
description: "Delegate tasks to the OpenCrawl worker Hermes Agent API (192.168.1.138:8081) for heavy/compute/scraping work."
version: 2.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [opencrawl, worker, delegation, remote, systemd]
    related_skills: [hermes-agent, hermes-setup-patterns, cloudflare-dns-management]
---

# OpenCrawl Worker Delegation

For heavy tasks (web scraping, batch processing, compute-intensive work, long-running operations), delegate to the OpenCrawl worker agent instead of running locally.

## Architecture

The worker exposes a lightweight Python HTTP server on port 8081 that accepts task requests, spawns `hermes chat -q` for each one, and returns the result. This approach was chosen because:

- `hermes mcp serve` requires an external `mcp_serve` module that is NOT bundled with Hermes and the `mcp-serve` pip package installs as a different top-level name (`mcpserver`), making it incompatible.
- The HTTP API server pattern is self-contained (stdlib only, no extra deps).
- Task isolation — each task gets its own Hermes subprocess, avoiding cross-task state corruption.
- Can be called from the main Hermes agent via curl, SSH, or Python.

## Worker API

The worker runs at **http://192.168.1.138:8081** (DHCP — may change after power loss) managed by systemd (`systemctl --user hermes-worker`).

### Health Check

```bash
curl -s http://192.168.1.138:8081/health
# → {"status": "ok", "worker": "opencrawl"}
```

### Delegate a Task

```bash
curl -s --max-time 300 -X POST http://192.168.1.138:8081/task \
  -H "Content-Type: application/json" \
  -d '{"task": "Your task description here"}'
```

### Response Format

```json
{
  "status": "completed",
  "task": "original task",
  "output": "Hermes agent response text",
  "exit_code": 0,
  "elapsed_seconds": 5.74
}
```

The `-Q` (quiet) flag suppresses Hermes banner on stderr. The `session_id` is returned in `stderr` for traceability.

## Setup (systemd)

The worker runs as a systemd user service. See `templates/hermes-worker.service` for the unit file:

```bash
# Place the template
cp ~/.hermes/skills/autonomous-ai-agents/opencrawl-worker-delegation/templates/hermes-worker.service \
  ~/.config/systemd/user/hermes-worker.service

# Enable linger (survive logout)
sudo loginctl enable-linger matth

# Enable and start
systemctl --user daemon-reload
systemctl --user enable hermes-worker
systemctl --user start hermes-worker

# Check status
systemctl --user status hermes-worker
journalctl --user -u hermes-worker -f
```

### UFW

Allow the API port from your LAN:

```bash
sudo ufw allow from 192.168.1.0/24 to any port 8081 comment 'Hermes Worker API'
```

## Script

The API server source is at `scripts/hermes-worker-api.py` — a stdlib-only Python HTTP server with:
- `GET /health` — readiness probe
- `POST /task` — accepts `{"task": "..."}`, runs `hermes chat -q task`
- 300s timeout per task
- Filters Hermes banner lines from stderr in the response

## When to Delegate

| Do locally | Delegate to worker |
|---|---|
| Quick file reads/writes | Web scraping |
| Git operations | Batch processing |
| Config changes | Long-running scripts |
| Light queries | Heavy compute |
| Cron management | Bulk API calls |

## Worker Specs

- **IP:** 192.168.1.138 (Proxmox VM 104) — was 192.168.1.137 before the power cut that reset DHCP leases
- **OS:** Ubuntu 24.04 LTS
- **Resources:** 8 vCPU, 16GB RAM, 50GB disk
- **Services:** Docker, Ollama (3 models: deepseek-r1:7b, mistral:7b, llama3.2:3b), Open WebUI
- **LLM:** deepseek-v4-flash via LiteLLM proxy at 192.168.1.121:4000
- **Hermes:** v0.15.0+ in ~/.hermes-worker/ (venv-based, NOT on system PATH)
- **Skills synced:** daily at 5AM from main agent via rsync cron
- **Config:** `model.provider: custom`, `model.base_url: http://192.168.1.121:4000/v1`, `model.default: deepseek-v4-flash`
- **Telegram:** OC_Worker (@OCMontyHermes_bot), gateway as systemd user service

## Telemetry & Monitoring

### Gateway logs

```bash
journalctl --user -u hermes-gateway --no-pager -n 20 -f
cat ~/.hermes/logs/gateway.log | tail -20
```

### Bot connectivity check (from anywhere with internet)

```bash
curl -sf "https://api.telegram.org/bot<TOKEN>/getMe"
# → {"ok":true,"result":{"id":...,"is_bot":true,"first_name":"OC_Worker","username":"OCMontyHermes_bot",...}}
```

## Health Monitoring

The main agent has a cron job (`no_agent=true`, every 30m) that runs `scripts/worker-health-check.sh` — SSHes to the worker and runs the health report. Silent on success, alerts on failure. Uses the no_agent pattern: empty stdout on success = no delivery; non-zero exit + error output on failure = alert.

## Post-Power-Outage Recovery

After a power cut, the VM may come back with a new DHCP IP. SSH to the old IP will fail with "No route to host".

### Finding the VM

```bash
# Ping-scan the subnet to find the new IP
for ip in $(seq 130 150); do
  ping -c 1 -W 1 "192.168.1.$ip" >/dev/null 2>&1 && ssh -o ConnectTimeout=2 matth@192.168.1.$ip 'hostname' 2>/dev/null
done
```

The worker's hostname is `opencrawl`. Once found, update this skill's IP reference and any hardcoded IPs in cron jobs or scripts.

### Checking the gateway came up

```bash
ssh matth@<new-ip> "systemctl --user is-active hermes-gateway && cat ~/.hermes/logs/gateway.log | grep 'Connected to Telegram' | tail -1"
```

## References

- `references/setup-checklist.md` — full reproducible setup commands from a fresh VM (config copy, systemd, UFW, cron, verification)

## Pitfalls

- **`hermes mcp serve` won't work** — the `mcp_serve` module is not bundled with Hermes. Use the HTTP API pattern instead.
- **UFW blocks port 8081 by default** — must explicitly allow from LAN.
- **Worker Hermes needs its own config.yaml** in `$HERMES_HOME` — the config from `~/.hermes-worker-config/` must be copied to `~/.hermes-worker/config.yaml` for `hermes chat -q` to find it.
- **No API key needed** for the LiteLLM proxy on the local network — it accepts unauthenticated requests from LAN IPs.
- **300s timeout is baked into the API server** — use `--max-time` on the curl side to match.
- **Task isolation means no session state carries over** — each POST creates a fresh Hermes session. Provide full context in the task description.
- **`hermes: command not found` on venv installs** — If Hermes was installed via `python3 -m venv ~/.hermes-worker`, the binary lives at `~/.hermes-worker/bin/hermes`, NOT on the shell PATH. Run `hermes` commands with the full path: `~/.hermes-worker/bin/hermes gateway install`. Alternatively, source the venv: `source ~/.hermes-worker/bin/activate`.
- **DHCP IP changes after power loss** — The worker VM gets its IP via DHCP. After a power cut it may come back on a different address. Use the post-power-outage recovery section above to find it. Update any hardcoded IPs in cron jobs, scripts, and this skill.
- **Telegram gateway needs `.env`, not `config.yaml`** — The bot token goes in `~/.hermes/.env` as `TELEGRAM_BOT_TOKEN=...`. If you put it in `config.yaml` under a `gateway.platforms.telegram.bot_token` key, the gateway starts but logs "No messaging platforms enabled" and ignores it. See the managed-agent-service skill's Retrofit section for the full pattern.
