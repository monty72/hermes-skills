# Hermes Agent — Disaster Recovery Procedures

## Recovery Scenario 1: Container dies, Proxmox snapshot exists

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

## Recovery Scenario 2: Full machine loss, rebuild from scratch

### Step 1: Provision a new machine

Create a Debian 12 LXC via Proxmox (or any Debian/Ubuntu machine):

```bash
# From Proxmox host shell
pct create 300 local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst \
  --hostname hermes --memory 2048 --swap 512 --cores 2 \
  --rootfs local-lvm:8 --net0 name=eth0,bridge=vmbr0,ip=dhcp \
  --unprivileged 1 --password '<temp-password>'
pct start 300
```

### Step 2: Install Hermes Agent

```bash
# SSH into the new container
ssh root@<new-ip>

# Install Hermes
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# Verify
hermes doctor
```

### Step 3: Restore skills from GitHub

```bash
# Remove the default skills (will be replaced)
rm -rf ~/.hermes/skills

# Clone your backed-up skills
git clone https://github.com/monty72/hermes-skills.git ~/.hermes/skills
```

### Step 4: Restore vault and config

The vault (`~/.hermes-vault/`) and `.env.local` are the most critical files — they contain all API keys.

**If you have a tarball backup:**
```bash
ls -lt ~/hermes-backups/
tar xzf ~/hermes-backups/hermes-full-*.tar.gz -C /
```

**If you have access to the old machine's filesystem:**
```bash
cp -r /mnt/old-root/home/matth/.hermes-vault/ ~/
cp /mnt/old-root/home/matth/.hermes/.env.local ~/.hermes/
```

**If you only have Proxmox vzdump backups:**
```bash
zstdcat /var/lib/vz/dump/vzdump-lxc-200-*.tar.zst | tar xf - \
  --occurrence ./home/matth/.hermes-vault/ \
  --occurrence ./home/matth/.hermes/.env.local
```

### Step 5: Configure Hermes

```bash
hermes config set model.default gpt-5.4-nano
hermes config set model.provider openai
hermes config set model.base_url ""
# Set fallback in config.yaml:
# fallback_providers: '[{"provider":"deepseek","model":"deepseek-v4-pro"}]'
```

### Step 6: Restore API keys to credential pool

```bash
hermes-vault list
hermes auth reset deepseek
```

### Step 7: Recreate cron jobs

1. **Weekly gateway restart** — Schedule: `0 4 * * 0`, Action: Restart Hermes gateway via systemd
2. **Daily cheapest-model check** — Schedule: `0 8 * * *`, Checks OpenAI for cheaper models
3. **Weekly full backup** — Schedule: `0 4 * * 0`, Script: `hermes-backup.sh`, `no_agent: true`

### Step 8: Start the gateway

```bash
hermes gateway install
hermes gateway start
```

### Step 9: Verify

```bash
hermes doctor
hermes auth list
hermes cron list
hermes gateway status
```

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
