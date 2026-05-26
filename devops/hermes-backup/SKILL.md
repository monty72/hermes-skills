---
name: hermes-backup
description: Multi-layer backup strategy for Hermes Agent — GitHub push, local tarball, and Proxmox vzdump scheduling. Covers skills repo, config, vault, and session data.
version: 1.0.0
author: Hermes Agent
---

# Hermes Backup

Multi-layer backup strategy for Hermes Agent data. Three complementary layers provide redundancy and disaster recovery.

## Layers

| Layer | What | Schedule | Location |
|-------|------|----------|----------|
| ☁️ GitHub | Skills repo (121+ skills, SKILL.md + references + scripts) | On backup run | `github.com/monty72/hermes-skills` |
| 💾 Local tarball | Full Hermes config + vault + CLI tools | Sunday 4am (weekly) | `~/hermes-backups/hermes-full-*.tar.gz` (keep 8) |
| ⚙️ Proxmox vzdump | VMID 200 (web container) snapshot | Sunday 4am (weekly) | Proxmox `local` storage (keep 4) |

## Backup Script

Located at `~/.hermes/scripts/hermes-backup.sh` (no-agent cron script):

```bash
#!/bin/bash
# Hermes full backup - run weekly
set -e

BACKUP_DIR="/home/matth/hermes-backups"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="$BACKUP_DIR/hermes-full-$TIMESTAMP.tar.gz"
SKILLS_REPO="/home/matth/.hermes/skills"

# 1. Push skills to GitHub
cd "$SKILLS_REPO"
git add -A
git commit --allow-empty -m "Auto-backup $TIMESTAMP" 2>/dev/null || true
git push origin master 2>&1 || echo "Git push failed"

# 2. Create tarball (exclude heavy/generated dirs)
tar czf "$BACKUP_FILE" \
  --exclude=".hermes/hermes-agent" \
  --exclude=".hermes/node_modules" \
  --exclude=".hermes/skills/.git" \
  --exclude=".hermes/lsp" \
  --exclude=".hermes/logs" \
  --exclude=".hermes/sessions" \
  --exclude=".hermes/cache" \
  -C /home/matth .hermes/ .hermes-vault/ .local/bin/hermes-vault

# 3. Prune old backups (keep last 8)
ls -t "$BACKUP_DIR"/hermes-full-*.tar.gz 2>/dev/null | tail -n +9 | xargs -r rm

echo "Backup complete: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"
```

## Cron Jobs

Two backup-related cron jobs are registered:

| Job | Schedule | Type | Action |
|-----|----------|------|--------|
| `hermes-full-backup` | Sun 4:00 | no-agent script | Runs `hermes-backup.sh` — git push + tarball |
| `cheapest-model-check` | Daily 8:00 | LLM agent | Checks OpenAI/DSeek for cheaper model, auto-switches |

The Proxmox vzdump schedule is configured via the Proxmox API (not a Hermes cron job).

## Proxmox vzdump Setup

```python
import urllib.request, json, ssl

token = "PVEAPIToken=hermes2@pve!api=..."
base = "https://192.168.1.6:8006/api2/json"
ctx = ssl._create_unverified_context()

body = json.dumps({
    "id": "hermes-backup",
    "schedule": "sun 04:00",
    "node": "pve1",
    "vmid": "200",
    "mode": "snapshot",           # no downtime
    "storage": "local",            # /var/lib/vz/dump/
    "compress": "zstd",            # fast compression
    "prune-backups": "keep-last=4", # keep 4 most recent
    "enabled": 1,
}).encode()

req = urllib.request.Request(f"{base}/cluster/backup", data=body,
    headers={"Authorization": token, "Content-Type": "application/json"})
urllib.request.urlopen(req, context=ctx, timeout=10)
```

## What's Included in the Tarball

| Path | Size | Notes |
|------|------|-------|
| `~/.hermes/skills/` | ~16MB | 121 skills, 1,626 files (git-excluded inside tarball) |
| `~/.hermes/config.yaml` | ~14KB | All settings |
| `~/.hermes/.env` | ~23KB | Gateway platform tokens |
| `~/.hermes/.env.local` | ~500B | Vault auto-unlock passphrase + Brave key |
| `~/.hermes-vault/` | ~16KB | Encrypted API keys (AES-256-GCM) |
| `~/.local/bin/hermes-vault` | ~12KB | Vault CLI tool |
| `~/.hermes/state.db` | ~200KB | Session database |
| **Total** | **~127MB** | After compression |

## What's Excluded

- `~/.hermes/hermes-agent/` — source code (can be reinstalled)
- `~/.hermes/node_modules/`, `~/.hermes/lsp/` — heavy dev deps
- `~/.hermes/logs/`, `~/.hermes/sessions/` — transient/temporary
- `~/.hermes/skills/.git/` — git metadata (redundant with GitHub push)

## Verification

Check backup health:

```bash
# List local backups with sizes
ls -lh ~/hermes-backups/

# Test tarball integrity
tar tzf ~/hermes-backups/hermes-full-*.tar.gz | head -20

# Check GitHub push worked
cd ~/.hermes/skills
git log --oneline -5

# Verify vault passphrase still works
source ~/.hermes/.env.local
export PATH="$HOME/.local/bin:$PATH"
hermes-vault list

# Check Proxmox backup job exists
python3 -c "
import urllib.request, json, ssl, os
ctx = ssl._create_unverified_context()
token = os.environ.get('PVE_TOKEN', 'PVEAPIToken=...')
import urllib.request
req = urllib.request.Request('https://192.168.1.6:8006/api2/json/cluster/backup',
    headers={'Authorization': token})
try:
    data = json.loads(urllib.request.urlopen(req, context=ctx, timeout=10).read())
    for j in data.get('data', []):
        print(f\"Job {j.get('id','')}: schedule={j.get('schedule','')} enabled={j.get('enabled','')}\")
except Exception as e:
    print(f'Error: {e}')
"
```

## Recovery

**Full restore from tarball:**
```bash
tar xzf ~/hermes-backups/hermes-full-<timestamp>.tar.gz -C ~/
```

**Partial restore (single file):**
```bash
tar xzf ~/hermes-backups/hermes-full-<timestamp>.tar.gz \
  -C ~/ .hermes/config.yaml
```

After restoring `.env` or `.env.local`, restart the gateway:
```bash
hermes gateway restart
```

After restoring the vault, verify keys:
```bash
source ~/.hermes/.env.local
hermes-vault list
```

## Pitfalls

- **GitHub push protection blocks tokens in commits** — if a skill file contains a real API key, GitHub's secret scanning blocks the push. Use `git filter-branch` or `git rebase -i` to remove the offending commit, then push with `--force` if needed.
- **Gateway tokens must be real in `.env`** — if you strip `TELEGRAM_BOT_TOKEN`, `HASS_TOKEN`, or `BRAVE_SEARCH_API_KEY` from `.env`, the gateway won't connect. Restore from vault before restarting.
- **Proxmox upload (multipart) is unreliable for files >50MB** — the `POST /nodes/{node}/storage/{storage}/upload` endpoint has timeout issues with large uploads over API. Use the local tarball as the primary backup and vzdump as the infrastructure-level backup.
- **No-agent cron scripts must self-source the vault passphrase** — add `source ~/.hermes/.env.local 2>/dev/null` and `export PATH="$HOME/.local/bin:$PATH"` at the top of the script.
- **The skills repo initial commit may contain secrets** — if any skill file had an inline API key before you noticed, filter-branch it out.
