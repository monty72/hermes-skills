# Full-Stack Health Check — Full Reference

*Absorbed from the consolidated `system-health-check` skill.*

## All 10 Dimensions

### 1. Hermes Agent Status
```bash
hermes status
```
Check: model, provider, gateway status (running, PID), sessions count, cron count.

### 2. Provider Balance (DeepSeek primary)
```bash
curl -s --max-time 5 https://api.deepseek.com/user/balance \
  -H "Authorization: Bearer $(hermes-vault get DEEPSEEK_API_KEY)"
```
Parse `balance_infos[0].total_balance`. Thresholds: >$2 healthy, $1-2 low, $0.5-1 warning, <$0.5 critical.

### 3. System Resources
```bash
df -h / && free -h && uptime && nproc
```
Disk <80% = fine. RAM available. Load < nproc = healthy.

### 4. LiteLLM Proxy (192.168.1.121:4000)
```bash
curl -s --max-time 5 http://192.168.1.121:4000/health
```
Returns `healthy_endpoints` array. All healthy = passing.

### 5. Mission Control Dashboard
```bash
curl -s --max-time 3 http://localhost:8081/ 2>/dev/null | head -3
curl -s --max-time 3 http://localhost:3000/ 2>/dev/null | head -3
```
Also: `ps aux | grep -E 'mission-control|next.*dev|:3000|:8081' | grep -v grep`

### 6. Cron Jobs
```bash
cronjob action=list
```
Check for: `last_status: "error"` (investigate), `last_status: null` (first run pending).

For errored jobs: `tail -5 ~/.hermes/logs/cron-<job-name>.log`

### 7. Home Assistant (192.168.1.146:8123)
```bash
curl -s --max-time 5 -H "Authorization: Bearer $HA_TOKEN" http://192.168.1.146:8123/api/
```
Cross-check with HA energy bridge cron `last_status` — better indicator than direct curl.

### 8. Discord / Gateway Connectivity
```bash
journalctl --user -u hermes-gateway --no-pager -n 20 | grep -iE 'discord|error|warn|connected' | tail -10
```
Red flags: `PrivilegedIntentsRequired`, `reconnect discord error`, exit code 1/FAILURE.

### 9. Agent Log Scan
```bash
tail -30 ~/.hermes/logs/agent.log 2>/dev/null | grep -iE 'error|warn|fail|timeout|exception|traceback' | tail -10
```
Cross-reference with gateway log for misconfigured provider errors.

### 10. no_agent Cron Job Health Verifier

For `no_agent: true` cron jobs (watchdog scripts):
- Exit 0 + empty stdout = success (silent pass)
- Exit non-zero = failure — check script path, SSH keys, target IPs

Common failures:
- **Stale IPs** — DHCP change breaks hardcoded SSH IPs
- **SSH key availability** — cron runs as shell, key must be accessible
- **Script missing on target** — verify with `ssh user@host "cat ~/scripts/health-report.sh"`

Recovery: fix the issue, then `cronjob action=run job_id=<id>` for immediate retry.

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

## Key Pitfalls

1. **Reboot transient:** When uptime <10 min, cron errors may self-resolve next cycle
2. **Gateway restart needed after Discord config changes:** Enable intents + `systemctl --user restart hermes-gateway`
3. **HA unreachable from CLI ≠ HA down:** Cross-check with cron status (better indicator)
4. **agent.log errors may be stale:** `Unknown provider` errors are from cron jobs, not current session
5. **Discord reconnection backoff:** 30s → 120s → 240s → 300s — no news is normal cycling
6. **systemd restart shows FAILURE then success:** Check *most recent* journal entry, not the first after restart
