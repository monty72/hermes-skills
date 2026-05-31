# OpenCrawl Worker Setup Checklist

Full reproducible commands to set up a Hermes worker from a fresh Proxmox VM.

## Prerequisites

- Ubuntu 24.04 LTS VM with SSH access
- Hermes installed at ~/.hermes-worker/ (via pip)
- LiteLLM proxy running on the main host (192.168.1.121:4000)
- Skills dirs: ~/.hermes-worker-skills/{main,crawling,general,devops}

## Initial Setup

```bash
# 1. Upgrade Hermes to latest
~/.hermes-worker/bin/pip install --upgrade hermes-agent

# 2. Copy config into HERMES_HOME
cp ~/.hermes-worker-config/config.yaml ~/.hermes-worker/config.yaml

# 3. Copy the API server script from skill
cp ~/.hermes/skills/autonomous-ai-agents/opencrawl-worker-delegation/scripts/hermes-worker-api.py \
  ~/scripts/hermes-worker-api.py
chmod +x ~/scripts/hermes-worker-api.py

# 4. Create systemd user service
mkdir -p ~/.config/systemd/user
cp ~/.hermes/skills/autonomous-ai-agents/opencrawl-worker-delegation/templates/hermes-worker.service \
  ~/.config/systemd/user/hermes-worker.service

# 5. Enable linger
sudo loginctl enable-linger $USER

# 6. Enable and start
systemctl --user daemon-reload
systemctl --user enable hermes-worker
systemctl --user start hermes-worker

# 7. Open UFW
sudo ufw allow from 192.168.1.0/24 to any port 8081 comment 'Hermes Worker API'
```

## Verification

```bash
curl -s http://localhost:8081/health
curl -s -X POST http://localhost:8081/task -H 'Content-Type: application/json' -d '{"task":"Run: hostname; uptime -p"}'
```

## Health Check Cron (Main Agent Side)

```bash
cp ~/.hermes/skills/autonomous-ai-agents/opencrawl-worker-delegation/scripts/worker-health-check.sh ~/.hermes/scripts/worker-health-check.sh
chmod +x ~/.hermes/scripts/worker-health-check.sh
```

Create via cronjob tool: cronjob(action='create', name='OpenCrawl health check', schedule='every 30m', script='worker-health-check.sh', no_agent=True, deliver='origin')

## Common Pitfalls

- Config MUST be in ~/.hermes-worker/config.yaml, not ~/.hermes-worker-config/config.yaml
- UFW blocks port 8081 by default - must explicitly allow from LAN
- hermes mcp serve won't work (mcp_serve not bundled) - use HTTP API pattern
- LiteLLM proxy on LAN accepts unauthenticated requests from local IPs
