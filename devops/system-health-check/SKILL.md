---
name: system-health-check
description: Run comprehensive health checks across the full Hermes stack — agent status, provider balances, system resources, LiteLLM proxy, Mission Control, cron jobs, Home Assistant, and Discord/gateway connectivity.
category: devops
version: 1.0.0
author: Agent
tags: [health, monitoring, diagnostics, debugging, system]
---

# System Health Check — Full Stack

Run a comprehensive health check covering all critical infrastructure tiers. Designed for a self-hosted Hermes Agent stack with Proxy (LiteLLM), Mission Control dashboard, Home Assistant, and Discord gateway.

## Dimensions (run in parallel where possible)

### 1. Hermes Agent Status
```bash
hermes status
```
Check: model, provider, API keys configured, gateway status (running, PID), sessions count, cron job count.

### 2. Provider Balance (DeepSeek primary)
```bash
curl -s --max-time 5 https://api.deepseek.com/user/balance \
  -H "Authorization: Bearer $(hermes-vault get DEEPSEEK_API_KEY 2>/dev/null)"
```
Parse `balance_infos[0].total_balance`. Report in USD.

Thresholds:
- > $2.00 — healthy
- $1.00–$2.00 — low, warn
- $0.50–$1.00 — warning, urge top-up
- < $0.50 — critical

### 3. System Resources
```bash
df -h /
free -h
uptime
nproc
```
Check: disk usage (< 80% is fine), RAM available, load average (< nproc = healthy), uptime (recent reboot = transient failures expected).

### 4. LiteLLM Proxy (192.168.1.121:4000)
```bash
curl -s --max-time 5 http://192.168.1.121:4000/health
```
Returns JSON with:
- `healthy_endpoints` — array of {model, ratelimit info}
- `unhealthy_endpoints` — array (empty = all good)
- `healthy_count`, `unhealthy_count`

All healthy = passing. Any unhealthy endpoint needs investigation.

### 5. Mission Control Dashboard
Check both tiers:
```bash
# Python backend (port 8081)
curl -s --max-time 3 http://localhost:8081/ 2>/dev/null | head -3

# Next.js frontend (port 3000)
curl -s --max-time 3 http://localhost:3000/ 2>/dev/null | head -3
```
Also check processes exist:
```bash
ps aux | grep -E 'mission-control|next.*dev|:3000|:8081' | grep -v grep
```

### 6. Cron Jobs
```bash
# Via CLI: list all jobs
hermes cron list
# or
cronjob action=list
```
Check for:
- Jobs with `last_status: "error"` — investigate individually
- Jobs with `last_status: null` (never run) — note as pending first run
- Jobs that should be running (e.g. HA energy bridge every 1m, observability every 5m)

For errored jobs, check cron-specific log:
```bash
tail -5 ~/.hermes/logs/cron-<job-name>.log 2>/dev/null
```
Transient errors after reboot are expected (resolve on next cycle).

### 7. Home Assistant (192.168.1.146:8123)
```bash
curl -s --max-time 5 \
  -H "Authorization: Bearer $HA_TOKEN" \
  http://192.168.1.146:8123/api/
```
Returns `{"message": "API running", ...}` on success.
Also check HA energy bridge cron last_status — if it's running every 1m and succeeding, HA is reachable from the cron layer even if the direct curl fails.

### 8. Discord / Gateway Connectivity
```bash
journalctl --user -u hermes-gateway --no-pager -n 20 2>/dev/null | grep -iE 'discord|error|warn|connected' | tail -10
```
Red flags: `PrivilegedIntentsRequired`, `reconnect discord error`, unclosed client sessions, exit code 1/FAILURE.
All clear: no Discord errors in journal, gateway active (running).

### 9. Agent Log Scan
```bash
tail -30 ~/.hermes/logs/agent.log 2>/dev/null | grep -iE 'error|warn|fail|timeout|exception|traceback' | tail -10
```
Cross-reference with gateway log — errors in agent.log about "Unknown provider" or model failures may indicate a cron job (e.g. cheapest-model-check) that misconfigured the provider.

## Report Template

```
Hermes      ████████░░  80%  (issues noted)
System      ██████████  100%
LLM Funds   ██████████  100%
LiteLLM     ██████████  100%
MC v4       ██████████  100%
Cron        ████████░░  83%  (N transient fails)
HA          ████████░░  80%  (notes)
Discord     ████████░░  80%  (notes)

### 🟢 Good
[List everything healthy]

### 🟡 Minor / Transient
[Issues expected to self-resolve]

### 🔴 Needs Attention
[Issues requiring user action]
```

## Pitfalls

- **Reboot transient**: When uptime < 10 min, cron jobs that just ran may show "error" because the system wasn't fully initialized. Give them one cycle to self-resolve before flagging as broken.
- **Gateway restart required after Discord config changes**: Enabling intents in the Discord Developer Portal is not enough — the gateway must be restarted (`systemctl --user restart hermes-gateway`). systemd auto-restarts after a crash but will fail again until intents are enabled.
- **HA unreachable from CLI doesn't mean HA is down**: The cron layer (ha_energy_bridge running every 1m) is a better health indicator for HA. The direct curl may fail due to token resolution or network namespace differences. Cross-check with cron status.
- **agent.log errors may be stale**: The log shows recent writes, not necessarily current-session errors. A "RuntimeError: Unknown provider 'openai'" in the gateway log likely came from the cheapest-model-check cron job, not the current session.
- **Discord reconnection backoff**: After a failure, retry intervals increase: 30s → 120s → 240s → 300s. A gateway showing "Reconnect discord error" at 240s+ intervals is still cycling, not stuck.
- **systemd user service restart sequence**: `systemctl --user restart` can produce a brief "Main process exited, code=exited, status=1/FAILURE" followed by a successful start with a new PID. Check the *most recent* journal entry, not the first after restart.

### 10. no_agent Cron Job Health Verifier

For `no_agent: true` cron jobs (watchdog scripts, health check scripts, data collectors), health is checked differently:
- **Exit code 0 + empty stdout** = success (silent pass) — the cron is working, no news is good news
- **Exit code non-zero** = failure — check the script path and its dependencies

**SSH-based health scripts (common pattern):**
The script SSHs to a VM and runs a remote report. If the SSH fails (exit code non-zero), it alerts.
Pitfalls:
- **Stale IPs**: If a VM's DHCP lease changes, the hardcoded IP in the SSH command breaks silently. Verify with `cronjob action=list` → check `last_status: "error"` jobs → inspect the script for hardcoded IPs.
- **SSH key availability**: Cron scripts run as plain shell — they need the SSH key accessible to the user running the cron. If a key was added to `authorized_keys` but the VM's IP changed, re-add it.
- **Script missing on target**: The remote script (`~/scripts/health-report.sh` etc.) must exist. Verify with `ssh user@host "cat ~/scripts/health-report.sh"`.
- **Recovery**: After fixing, run `cronjob action=run job_id=<id>` to force an immediate cycle.

**Verification:**
```bash
bash ~/.hermes/scripts/<script-name>.sh
echo $?  # 0 = success, non-zero = error
ssh -o ConnectTimeout=5 -o BatchMode=yes user@host "echo connected"
```
