# Hermes Agent — Backup & Disaster Recovery

## Overview

Three backup layers protect your Hermes Agent setup:

| Layer | What | When | Retention |
|-------|------|------|-----------|
| ☁️ GitHub | All 121 skills (`monty72/hermes-skills`) | On every backup run | Forever (git history) |
| 💾 Local tarball | Full `~/.hermes/` + `~/.hermes-vault/` | Sunday 4am | Last 8 |
| ⚙️ Proxmox vzdump | VMID 200 (web container) snapshot | Sunday 4am | Last 4 |

## Cron Jobs

These are managed via Hermes's built-in cron system (`cronjob` tool or `hermes cron` CLI):

| Name | Schedule | Purpose |
|------|----------|---------|
| `weekly-gateway-restart` | `0 4 * * 0` (Sun 4am) | Keep gateway healthy |
| `cheapest-model-check` | `0 8 * * *` (daily 8am) | Auto-switch to cheapest OpenAI model |
| `hermes-full-backup` | `0 4 * * 0` (Sun 4am) | Push skills to GitHub + create tarball |

The backup script lives at `~/.hermes/scripts/hermes-backup.sh` (also linked at `~/.local/bin/hermes-backup`).

## Recovery Procedure

### Scenario 1: Container dies, Proxmox snapshot exists

1. **Restore from Proxmox UI** — Datacenter → Backup → select the hermes-backup job → Restore
2. **Or via CLI on Proxmox host:**
   ```bash
   # List available backups
   ls -lt /var/lib/vz/dump/

   # Restore the latest
   pct restore 200 /var/lib/vz/dump/vzdump-lxc-200-*.tar.zst --storage local-lvm
   pct start 200
   ```
3. **Verify** — `hermes doctor` and `hermes gateway status`

### Scenario 2: Full machine loss, need to rebuild from scratch

#### Step 1: Provision a new machine

Create a Debian 12 LXC via Proxmox (or any Debian/Ubuntu machine):

```bash
# From Proxmox host shell
pct create 300 local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst \
  --hostname hermes --memory 2048 --swap 512 --cores 2 \
  --rootfs local-lvm:8 --net0 name=eth0,bridge=vmbr0,ip=dhcp \
  --unprivileged 1 --password '<temp-password>'
pct start 300
```

#### Step 2: Install Hermes Agent

```bash
# SSH into the new container
ssh root@<new-ip>

# Install Hermes
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# Verify
hermes doctor
```

#### Step 3: Restore skills from GitHub

```bash
# Remove the default skills (will be replaced)
rm -rf ~/.hermes/skills

# Clone your backed-up skills
git clone https://github.com/monty72/hermes-skills.git ~/.hermes/skills
```

#### Step 4: Restore vault and config

The vault (`~/.hermes-vault/`) and `.env.local` are the most critical files — they contain all API keys.

**If you have a tarball backup:**

```bash
# Find the latest backup
ls -lt ~/hermes-backups/

# Extract
tar xzf ~/hermes-backups/hermes-full-*.tar.gz -C /
```

**If you have access to the old machine's filesystem:**

```bash
# Copy from old disk image (if still mounted)
cp -r /mnt/old-root/home/matth/.hermes-vault/ ~/
cp /mnt/old-root/home/matth/.hermes/.env.local ~/.hermes/
```

**If you only have Proxmox vzdump backups:**

```bash
# Extract the vzdump archive to access vault files
# Vzdump files are at /var/lib/vz/dump/ on the Proxmox host
zstdcat /var/lib/vz/dump/vzdump-lxc-200-*.tar.zst | tar xf - \
  --occurrence ./home/matth/.hermes-vault/ \
  --occurrence ./home/matth/.hermes/.env.local
```

#### Step 5: Configure Hermes

```bash
# Set the model and provider
hermes config set model.default gpt-5.4-nano
hermes config set model.provider openai
hermes config set model.base_url ""

# Set fallback
# In config.yaml, set:
# fallback_providers: '[{"provider":"deepseek","model":"deepseek-v4-pro"}]'
```

#### Step 6: Restore API keys to credential pool

```bash
# Check vault has the keys
hermes-vault list

# Reset the credential pool so Hermes re-reads from vault
hermes auth reset deepseek
```

#### Step 7: Recreate cron jobs

These need to be set up in a Hermes session using the cronjob tool:

1. **Weekly gateway restart:**
   - Schedule: `0 4 * * 0`
   - Action: Restart Hermes gateway via systemd

2. **Daily cheapest-model check:**
   - Schedule: `0 8 * * *`
   - Checks OpenAI for cheaper models and auto-switches

3. **Weekly full backup:**
   - Schedule: `0 4 * * 0`
   - Script: `hermes-backup.sh` (from the skills repo at `devops/hermes-backup/scripts/hermes-backup.sh`)
   - `no_agent: true` mode

#### Step 8: Start the gateway

```bash
hermes gateway install   # First time only — installs the systemd service
hermes gateway start
```

#### Step 9: Verify everything

```bash
hermes doctor
hermes auth list
hermes cron list
hermes gateway status
```

## What's Backed Up

### Included in tarball:
- `~/.hermes/config.yaml` — all settings
- `~/.hermes/.env` — API keys (placeholders only, real keys in vault)
- `~/.hermes/.env.local` — vault passphrase + additional keys
- `~/.hermes/skills/` (without .git directory)
- `~/.hermes/auth.json` — credential pool state
- `~/.hermes/state.db` — session database
- `~/.hermes-vault/` — encrypted key storage
- `~/.local/bin/hermes-vault` — vault CLI
- `~/.ssh/proxmox*` — Proxmox SSH keys

### NOT included in tarball (excluded to save space):
- `~/.hermes/hermes-agent/` — Hermes source code (reinstallable)
- `~/.hermes/node_modules/`
- `~/.hermes/lsp/`
- `~/.hermes/logs/`
- `~/.hermes/sessions/`
- `~/.hermes/cache/`

### In GitHub only:
- 121 skill files (all SKILL.md + references + scripts + templates)
- NOT included: vault, credentials, `.env`, `config.yaml`, auth state

## Critical Files

| File | What it does | Backup source |
|------|-------------|---------------|
| `~/.hermes-vault/` | All encrypted API keys | Tarball only |
| `~/.hermes/.env.local` | Vault passphrase + Brave API key | Tarball only |
| `~/.hermes/.env` | API keys (placeholders) | Tarball |
| `~/.hermes/config.yaml` | All settings | Tarball |
| `~/.hermes/auth.json` | Credential pool state | Tarball |
| `~/.hermes/state.db` | Session history | Tarball |

## Restoring from Scratch — Quick Cheat Sheet

```bash
# 1. Install Hermes
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# 2. Clone skills
rm -rf ~/.hermes/skills && git clone https://github.com/monty72/hermes-skills.git ~/.hermes/skills

# 3. Extract backup (if you have it)
# tar xzf ~/hermes-backups/hermes-full-*.tar.gz -C /

# 4. Copy vault + .env.local from backup
# cp /backup/location/.hermes-vault/ ~/.hermes-vault/ -r
# cp /backup/location/.hermes/.env.local ~/.hermes/.env.local

# 5. Configure model
hermes config set model.default gpt-5.4-nano
hermes config set model.provider openai

# 6. Start gateway
hermes gateway install
hermes gateway start
```
