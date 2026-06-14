---
name: system-operations
description: "Run and monitor self-hosted infrastructure — run systemd user services with auto-restart and boot persistence, and run comprehensive health checks across the Hermes Agent stack (provider balances, LiteLLM, Home Assistant, Discord gateway, cron jobs, system resources)."
category: devops
tags: [systemd, health, monitoring, service-management, diagnostics, self-hosted]
---

# System Operations — Service Management & Health Monitoring

## Overview

This umbrella skill covers the operational side of running a self-hosted Hermes Agent stack: managing long-lived processes as systemd user services (with auto-restart, boot persistence, journald logging) and running comprehensive health checks across all infrastructure tiers.

## Sections at a Glance

| Section | Reference File | Covers |
|---------|---------------|--------|
| 1. systemd User Service Lifecycle | `references/systemd-services.md` | Creating/enabling/starting/stopping services, unit file template, exec path debugging, exit code diagnosis |
| 2. Full-Stack Health Check | `references/health-checks.md` | 10 dimensions: Hermes status, provider balance, system resources, LiteLLM proxy, Mission Control, cron jobs, HA, Discord, agent logs, no-agent cron verifier |
| 3. Common Service Patterns | `references/systemd-services.md#examples-in-production` | LiteLLM proxy, MC V4 dashboard — exact ExecStart paths |

## Quick Reference — systemd User Services

```bash
# Create the unit file
mkdir -p ~/.config/systemd/user
vim ~/.config/systemd/user/my-service.service

# After editing
systemctl --user daemon-reload

# Control
systemctl --user enable my-service.service   # auto-start on boot
systemctl --user start my-service.service    # start now
systemctl --user status my-service.service   # check state
systemctl --user restart my-service.service  # stop + start

# Logs
journalctl --user -u my-service.service --no-pager -n 50
```

### Unit File Template
```ini
[Unit]
Description=My Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=%h/path/to/project
ExecStart=%h/.local/bin/binary --args
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

### Exec Path Debugging — Most Common Failure
```bash
# systemd can't find binaries the way your shell can
which node   # /home/user/.local/bin/node → symlink to /home/user/.hermes/node/bin/node
# Use %h/.hermes/node/bin/node in ExecStart (NOT ~, NOT bare 'node')

which litellm  # /home/user/.local/bin/litellm
# Use %h/.local/bin/litellm
```

### Exit Code Diagnosis
| Code | Meaning | Cause |
|------|---------|-------|
| 203 (EXEC) | Binary not found | Wrong path, broken symlink |
| 127 | Command not found | Shebang interpreter missing |
| 1 | App crashed | Check journalctl for app-level error |

**Key rules:** `~` doesn't work in ExecStart — use `%h`. PATH is minimal — use absolute paths. `.bashrc`/`.profile` are NOT sourced. `daemon-reload` required after every edit.

## Quick Reference — Health Check

Run these in parallel where possible:

### 1. Hermes Agent Status
```bash
hermes status
```

### 2. Provider Balance (DeepSeek primary)
```bash
curl -s --max-time 5 https://api.deepseek.com/user/balance \
  -H "Authorization: Bearer $(hermes-vault get DEEPSEEK_API_KEY)"
```
Thresholds: >$2.00 healthy, $1-2 low, $0.5-1 warning, <$0.5 critical.

### 3. System Resources
```bash
df -h / && free -h && uptime && nproc
```
Disk <80%, RAM available, load < nproc = healthy.

### 4. LiteLLM Proxy (192.168.1.121:4000)
```bash
curl -s --max-time 5 http://192.168.1.121:4000/health
```
Check `healthy_count` vs `unhealthy_count`.

### 5. Mission Control Dashboard (ports 3000/8081)
```bash
curl -s --max-time 3 http://localhost:8081/ 2>/dev/null | head -3
curl -s --max-time 3 http://localhost:3000/ 2>/dev/null | head -3
```

### 6. Cron Jobs
Check `cronjob action=list` for `last_status: "error"` jobs.

### 7. Home Assistant
```bash
curl -s --max-time 5 -H "Authorization: Bearer $HA_TOKEN" http://192.168.1.146:8123/api/
```
Cross-check with HA energy bridge cron status.

### 8. Discord Gateway
```bash
journalctl --user -u hermes-gateway --no-pager -n 20 | grep -iE 'discord|error|warn|connected'
```

### 9. Agent Log Scan
```bash
grep -iE 'error|warn|fail|timeout' ~/.hermes/logs/agent.log | tail -10
```

### Report Template
```
Hermes      ████████░░  80%
System      ██████████  100%
LLM Funds   ██████████  100%
Cron        ████████░░  83%
HA          ████████░░  80%

### 🟢 Good | 🟡 Minor | 🔴 Needs Attention
```

## Key Pitfalls

1. **Reboot transients:** If uptime < 10 min, cron errors may self-resolve on next cycle
2. **PowerShell vs systemd:** Old processes on a port prevent systemd from binding — kill them first
3. **HA unreachable from CLI ≠ HA down:** Cross-check with cron status
4. **agent.log errors may be stale:** `Unknown provider` errors likely from cron jobs, not current session
5. **Discord reconnection backoff:** 30s → 120s → 240s → 300s. No news is normal cycling
6. **no-agent cron health:** Exit 0 + empty stdout = success. Non-zero = failure (check DHCP drift or SSH keys)
7. **SSH-based health scripts:** Stale IPs after DHCP change silently break the script

## Reference Files

- `references/systemd-services.md` — Full systemd user service reference: lifecycle, pitfalls, production examples (LiteLLM, MC V4), ExecStart path debugging
- `references/health-checks.md` — Full health check reference: all 10 dimensions with exact commands, thresholds, no-agent cron verifier pattern
