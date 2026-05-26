---
name: proxmox-host-creation
description: "Provision and manage Proxmox VE LXC containers and VMs via the REST API — create containers, authenticate with API tokens, bootstrap SSH access, install nginx, and host static sites. Covers the full lifecycle from Proxmox API setup to a serving web host."
version: 1.0.0
author: Hermes Agent
---

# Proxmox Host Creation

Use this skill when provisioning machines on a **Proxmox VE** hypervisor via its REST API. This covers:
- Authenticating with API tokens
- Inspecting node resources (storage, templates, network)
- Creating LXC containers from templates
- Bootstrapping SSH access into a fresh container
- Installing nginx and deploying sites to the container
- Setting up the container as a production web host

## Overview

The pattern is: `Proxmox API → create container → bootstrap SSH → install nginx → copy site files → make live`

## Authentication

### API Token (PREFERRED)

```bash
# Token format in Authorization header
Authorization: PVEAPIToken=<userid>@<realm>!<tokenid>=<token-value>

# Example
curl -sk https://<proxmox-host>:8006/api2/json/version \
  -H "Authorization: PVEAPIToken=hermes2@pve!api=19b5fd1b-9354-47fd-8847-4ebbe28a4abb"
```

**Token creation** (run on Proxmox shell):
```
pveum user add <name>@pve
pveum acl modify / -user <name>@pve -role Administrator
pveum user token add <name>@pve api --privsep 0
```

The last command prints a `value` UUID — that's the token secret. The `full-tokenid` is the token ID part.

**IMPORTANT:** The correct command to grant permissions is:
```
pveum acl modify / -user <name>@<realm> -role Administrator
```
The **incorrect** command `pveum user modify <userid> -role Administrator -path /` does NOT work — Proxmox returns "Unknown option: role". The ACL is set via `pveum acl`, not `pveum user`.

### User/Password (Fallback)

```bash
# Get a ticket
curl -sk -X POST https://<host>:8006/api2/json/access/ticket \
  --data-urlencode 'username=root@pam' \
  --data-urlencode 'password=<password>'
```

The ticket response includes `ticket` (cookie) and `CSRFPreventionToken` (header). Use these for subsequent requests.

## API Exploration

```bash
# Set these once
TOKEN="PVEAPIToken=<userid>@pve!<tokenid>=<value>"
HOST="https://192.168.1.6:8006"

# Node status — CPU, memory, swap, kernel version
curl -sk "$HOST/api2/json/nodes/pve1/status" -H "Authorization: $TOKEN"
# Memory parsing example:
curl -sk "$HOST/api2/json/nodes/pve1/status" -H "Authorization: $TOKEN" | python3 -c "
import sys, json
d = json.load(sys.stdin)['data']
mem = d['memory']
print(f'RAM: {mem.get(\"used\",0)/1e9:.1f}GB / {mem.get(\"total\",0)/1e9:.1f}GB')
"

# Storage pools
curl -sk "$HOST/api2/json/nodes/pve1/storage" -H "Authorization: $TOKEN"
# Shows type (lvmthin, dir), content types (rootdir,images,iso,vztmpl,backup), available/total

# Available LXC templates (on 'local' storage)
curl -sk "$HOST/api2/json/nodes/pve1/storage/local/content" -H "Authorization: $TOKEN"
# Filter for .tar.zst files with vztmpl content type

# All VMs/containers on the node
curl -sk "$HOST/api2/json/cluster/resources?type=vm" -H "Authorization: $TOKEN"

# Network bridges
curl -sk "$HOST/api2/json/nodes/pve1/network" -H "Authorization: $TOKEN"
# Filter active bridges: vmbr0 (main LAN), vmbr1, etc.

# DNS
curl -sk "$HOST/api2/json/nodes/pve1/dns" -H "Authorization: $TOKEN"
```

## Creating an LXC Container

```bash
TOKEN="PVEAPIToken=<userid>@pve!<tokenid>=<value>"
HOST="https://<proxmox-ip>:8006"

curl -sk -X POST "$HOST/api2/json/nodes/pve1/lxc" \
  -H "Authorization: $TOKEN" \
  --data-urlencode 'vmid=<id>' \
  --data-urlencode 'ostemplate=local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst' \
  --data-urlencode 'hostname=<name>' \
  --data-urlencode 'memory=1024' \
  --data-urlencode 'swap=512' \
  --data-urlencode 'cores=2' \
  --data-urlencode 'rootfs=local-lvm:4' \
  --data-urlencode 'net0=name=eth0,bridge=vmbr0,ip=dhcp' \
  --data-urlencode 'unprivileged=1'
```

**Important params:**
- `vmid` — unique numeric ID (check existing VMs first, avoid conflicts)
- `ostemplate` — path to the template on `local` storage
- `memory` — MB of RAM (1024 is fine for a web server)
- `rootfs=local-lvm:4` — 4GB disk on the lvmthin pool
- `net0` — use `--data-urlencode` to handle the commas in the value
- `--data-urlencode` must be used for all parameters, NOT `-d`, otherwise commas in `net0` cause parsing errors

**Response:** Returns a task UPID string. The task runs asynchronously.

## Wait for Container to Be Ready

```bash
# Check task status
curl -sk "$HOST/api2/json/nodes/pve1/tasks/<UPID>/status" -H "Authorization: $TOKEN"

# View task log
curl -sk "$HOST/api2/json/nodes/pve1/tasks/<UPID>/log" -H "Authorization: $TOKEN"

# Check container status (wait for "running")
curl -sk "$HOST/api2/json/nodes/pve1/lxc/<vmid>/status/current" -H "Authorization: $TOKEN"

# Get IP address
curl -sk "$HOST/api2/json/nodes/pve1/lxc/<vmid>/interfaces" -H "Authorization: $TOKEN"
# Look for eth0's inet field (the first ip-address with type "inet" that isn't 127.0.0.1)
```

**Container readiness:** The container starts with DHCP. The IP address may take a few seconds to appear after the container starts. Poll interfaces every 3 seconds until the inet IP shows up.

## Bootstrapping SSH Access into a Fresh Container

This is the hardest part. Fresh LXC containers have **no SSH keys** and **no password set**. You cannot SSH in directly.

### Method 1: `pct exec` from Proxmox shell (REQUIRES USER TO RUN COMMANDS)

If you don't have SSH access to the container, ask the user to run commands on their Proxmox root shell via `pct exec <vmid> -- <command>`:

```bash
# Set root password
pct exec 200 -- passwd root
# (interactive — enter password twice)

# Install nginx
pct exec 200 -- apt-get update -qq
pct exec 200 -- apt-get install -y -qq nginx curl

# Copy SSH key for future access
pct exec 200 -- mkdir -p /root/.ssh
pct exec 200 -- bash -c "echo '<your-public-key>' > /root/.ssh/authorized_keys"
pct exec 200 -- chmod 600 /root/.ssh/authorized_keys
pct exec 200 -- sed -i 's/^#*PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config
pct exec 200 -- systemctl restart sshd

# Create site directory
pct exec 200 -- mkdir -p /var/www/<sitename>
```

### Method 2: SSH with password (if password is set)

```bash
# Once the container has a password set, SSH in with:
ssh -o StrictHostKeyChecking=no root@<container-ip>
```

### Method 3: SSH key (if key was inserted via pct exec)

```bash
ssh -o StrictHostKeyChecking=no \
  -o PasswordAuthentication=no \
  -o PreferredAuthentications=publickey \
  -i ~/.ssh/id_ed25519 \
  root@<container-ip> "<command>"
```

### Common SSH failure modes

| Error | Cause | Fix |
|-------|-------|-----|
| `Permission denied (publickey,password)` | No key set OR key not accepted | Use `pct exec` to verify the key was written correctly |
| `ssh_askpass: exec()` warning | SSH client trying password auth | Add `-o PasswordAuthentication=no` |
| `Connection refused` | SSH server not running in container | `pct exec <vmid> -- systemctl restart sshd` |
| Host key changed | Container recreated | `ssh-keygen -R <ip>` |

**Key insight:** If SSH keeps refusing your key after `pct exec` added it, the problem is usually:
1. `/root/.ssh` has wrong permissions (must be 700)
2. `authorized_keys` has wrong permissions (must be 600)
3. `PubkeyAuthentication` is disabled in sshd_config
4. sshd hasn't been restarted after config change

## Setting Up nginx on the Container

Once you have access (via `pct exec` or SSH):

```bash
# Configure nginx
cat > /etc/nginx/sites-available/<sitename> << 'EOF'
server {
    listen 80;
    server_name _;
    root /var/www/<sitename>;
    index index.html;
    location / { try_files $uri $uri/ =404; }
}
EOF

# Enable site
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/<sitename> /etc/nginx/sites-enabled/

# Restart
systemctl restart nginx

# Verify
curl -s http://localhost/
```

### Method 4: Piping config files via heredoc + pct exec tee

For small config files (nginx configs, scripts), pipe via standard input:

```bash
cat << 'EOF' | pct exec <VMID> -- tee /path/to/file > /dev/null
server {
    listen 80;
    server_name _;
    root /var/www/childminding;
    index index.html;
    location / { try_files $uri $uri/ =404; }
}
EOF
```

This avoids the quoting issues of `pct exec <VMID> -- bash -c 'cat > /path << 'EOF''...` and works cleanly with heredocs.

## Copying Site Files

You can copy files from the Hermes VM to the container if SSH key access is working:

```bash
# Copy single files
scp -o StrictHostKeyChecking=no /path/to/index.html root@<container-ip>:/var/www/<sitename>/

# Copy entire directory
scp -o StrictHostKeyChecking=no -r /path/to/site/* root@<container-ip>:/var/www/<sitename>/
```

### Copying Files When SSH is Blocked (pct push)

If SSH key access isn't working and the file is too large for `pct exec` piping (e.g. >60KB HTML with inline SVG), use **pct push** from the Proxmox host:

```bash
# Step 1: Stage the file on the Proxmox host
# If Hermes VM serves the file on HTTP, pull it from there:
curl -s http://<hermes-vm-ip>:<port>/<path> > /tmp/<filename>

# Or copy from a remote host:
scp user@remote:/path/to/file /tmp/<filename>

# Step 2: Push into the container
pct push <VMID> /tmp/<filename> /var/www/<sitename>/<filename>

# Step 3: Verify
curl -s http://<container-ip>/<path>
```

**Architecture pattern for Hermes VM + Proxmox:**
- **Hermes VM** (192.168.1.6) serves files via Flask on port 8000
- **Proxmox host** (same IP) can reach Hermes VM's HTTP server on localhost:8000
- **Web container** (192.168.1.229) cannot reach Hermes VM's ports directly
- **Copy path**: Hermes VM (port 8000) → Proxmox shell (curl localhost:8000) → pct push → container
- When the HTML file is too large for a single `pct exec` command, use the pct push pattern instead of trying to base64-encode and pipe it through stdin.

## Orphan Resource Cleanup

Proxmox occasionally accumulates orphaned resources that waste disk space or clutter the resource list. This section covers detection and cleanup.

### Ghost Container / Phantom VM

A **ghost container** appears in the cluster resource list (`/cluster/resources?type=vm`) with `status: "unknown"` and no name, but its config file no longer exists (`Configuration file 'nodes/pve1/lxc/<VMID>.conf' does not exist`).

**Detection:**

```bash
TOKEN="PVEAPIToken=<userid>@pve!<tokenid>=<value>"
HOST="https://<proxmox-ip>:8006"

# List all VMs/CTs — look for entries with no name and unknown status
curl -sk "$HOST/api2/json/cluster/resources?type=vm" -H "Authorization: $TOKEN"

# Check if a specific VMID is a ghost by trying its config
curl -sk "$HOST/api2/json/nodes/pve1/lxc/<VMID>/config" -H "Authorization: $TOKEN"
# Returns: "Configuration file does not exist"

# A ghost has no disk, no RAM, no CPU usage — purely cosmetic
```

**Cause:** The container was deleted (config file removed) but the pmxcfs cluster database still caches the entry.

**Removal (requires root@pam shell):**

The API token cannot remove ghost entries. The config file is already gone, but the cluster database still references the VMID. Fix from the Proxmox host shell:

```bash
# Method 1 — pvesh (cleanest)
pvesh delete /cluster/config/lxc/<VMID>

# Method 2 — direct file removal (equivalent)
rm -f /etc/pve/nodes/pve1/lxc/<VMID>.conf
```

**Why the API can't do it:** Deleting a container via API (`DELETE /nodes/pve1/lxc/<VMID>`) only works if the config file exists. A ghost has no config file, so the API returns 404. The API token user (`@pve` realm) cannot access the Proxmox shell. Only `root@pam` can run `pvesh` or modify `/etc/pve/` directly.

**Workaround attempts that don't work:**
- Restarting `pveproxy` or `pve-cluster` services (doesn't clear the cache)
- Re-creating the container with the same VMID then deleting it (creation fails with "CT <VMID> already exists")
- Using the termproxy `login` endpoint (requires a `@pam` user, not `@pve`)

### Stale ISOs and Templates

**Detection:**

```bash
TOKEN="PVEAPIToken=<userid>@pve!<tokenid>=<value>"
HOST="https://<proxmox-ip>:8006"

# List all content on local storage (ISOs + templates)
curl -sk "$HOST/api2/json/nodes/pve1/storage/local/content" -H "Authorization: $TOKEN"

# To inspect in Python:
curl -sk "$HOST/api2/json/nodes/pve1/storage/local/content" -H "Authorization: $TOKEN" | python3 -c "
import sys, json
items = json.load(sys.stdin).get('data', [])
for item in sorted(items, key=lambda x: x.get('volid','')):
    volid = item.get('volid','')
    size_mb = round(item.get('size',0)/1024/1024, 1)
    ctype = item.get('content','')
    print(f'  [{ctype}] {volid} ({size_mb} MB)')
"
```

**What to look for:**
- **Duplicate/superseded ISOs** — e.g., `ubuntu-24.04.1` AND `ubuntu-24.04.4` — delete the older one
- **Unlabeled templates** — `rootfs.tar.xz` without a distro tag — likely orphaned
- **ISOs you no longer need** — stale test installers, old distro versions

**Deletion (via API):**

```bash
TOKEN="PVEAPIToken=<userid>@pve!<tokenid>=<value>"
HOST="https://<proxmox-ip>:8006"

# Delete an ISO
curl -sk -X DELETE "$HOST/api2/json/nodes/pve1/storage/local/content/local:iso/<filename>" \
  -H "Authorization: $TOKEN"

# Delete an old template
curl -sk -X DELETE "$HOST/api2/json/nodes/pve1/storage/local/content/local:vztmpl/<filename>" \
  -H "Authorization: $TOKEN"
```

**Path encoding:** The `<content>` value is `local:iso/<filename>` or `local:vztmpl/<filename>`. The full volid (e.g., `local:iso/ubuntu-24.04.1-desktop-amd64.iso`) becomes the path segment in the URL.

### Snapshot Cleanup

**Check all VMs/CTs for snapshots:**

```bash
TOKEN="PVEAPIToken=<userid>@pve!<tokenid>=<value>"
HOST="https://<proxmox-ip>:8006"

for vmid in $(curl -sk "$HOST/api2/json/cluster/resources?type=vm" -H "Authorization: $TOKEN" | \
  python3 -c "import sys,json; [print(v['vmid']) for v in json.load(sys.stdin)['data']]" ); do
  # Try qemu VM
  snap=$(curl -sk "$HOST/api2/json/nodes/pve1/qemu/$vmid/snapshot" -H "Authorization: $TOKEN" 2>/dev/null)
  snaps=$(echo "$snap" | python3 -c "import sys,json; d=json.load(sys.stdin).get('data',[]); [print(s['name']) for s in d if s.get('name','current')!='current']" 2>/dev/null)
  if [ -n "$snaps" ]; then
    echo "VM $vmid snapshots: $snaps"
  fi
  # Try LXC
  snap=$(curl -sk "$HOST/api2/json/nodes/pve1/lxc/$vmid/snapshot" -H "Authorization: $TOKEN" 2>/dev/null)
  snaps=$(echo "$snap" | python3 -c "import sys,json; d=json.load(sys.stdin).get('data',[]); [print(s['name']) for s in d if s.get('name','current')!='current']" 2>/dev/null)
  if [ -n "$snaps" ]; then
    echo "LXC $vmid snapshots: $snaps"
  fi
done
```

The `current` entry is always present and is NOT a user snapshot — it's the live state reference. Only named snapshots (e.g., `before-upgrade`, `backup-2026-05-01`) count as user snapshots.

## Hermes Backup Setup

After deploying a Hermes container, configure these backups via the API:

### Proxmox vzdump Backup Job

Create a scheduled snapshot backup for the Hermes container:

```python
import urllib.request, json, ssl
token = "PVEAPIToken=hermes2@pve!api=19b5fd1b-9354-47fd-8847-4ebbe28a4abb"
base = "https://192.168.1.6:8006/api2/json"
ctx = ssl._create_unverified_context()
body = json.dumps({
    "id": "hermes-backup",
    "schedule": "sun 04:00",
    "node": "pve1",
    "vmid": "200",
    "mode": "snapshot",
    "storage": "local",
    "compress": "zstd",
    "prune-backups": "keep-last=4",
    "enabled": 1,
}).encode()
req = urllib.request.Request(f"{base}/cluster/backup", data=body,
    headers={"Authorization": token, "Content-Type": "application/json"})
resp = urllib.request.urlopen(req, context=ctx, timeout=10)
```

### Hermes-internal Cron Jobs

These run via the `cronjob` tool and should be recreated on new profiles:

1. **Weekly Gateway Restart** (`0 4 * * 0`) — restarts the gateway to avoid memory leaks
2. **Daily Cheapest-Model Check** (`0 8 * * *`) — checks if a cheaper OpenAI model exists and switches
3. **Weekly Full Backup** (`0 4 * * 0`, no_agent=True, script: `hermes-backup.sh`) — pushes skills to GitHub, creates local tarball of `~/.hermes/` + `~/.hermes-vault/`, prunes old backups (keeps 8)

### SSH Key Setup for Web Container

To push backup tarballs to the web container (VMID 200) from the Hermes host:

1. **Generate key** — `ssh-keygen -t rsa -b 4096 -f ~/.ssh/proxmox -N ""`
2. **Inject into container** — on the Proxmox host, run:
   ```bash
   pct exec 200 -- mkdir -p /root/.ssh
   pct exec 200 -- bash -c "echo '<pubkey>' > /root/.ssh/authorized_keys"
   pct exec 200 -- chmod 600 /root/.ssh/authorized_keys
   pct exec 200 -- chmod 700 /root/.ssh
   pct exec 200 -- systemctl restart sshd
   ```
3. **Configure SSH** in `~/.ssh/config`:
   ```
   Host proxmox-backup
       HostName 192.168.1.6
       User root
       IdentityFile ~/.ssh/proxmox
       StrictHostKeyChecking accept-new
   ```

### Credential Vault

API keys are stored in an encrypted local vault at `~/.hermes-vault/`. Uses AES-256-GCM with a passphrase. CLI: `hermes-vault <get|set|list|delete>`. The passphrase is stored in `~/.hermes/.env.local` for auto-unlock.

**Vault contents (14 keys):** BRAVE_SEARCH_API_KEY, CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_TUNNEL_ACTIVE_SECRET, CLOUDFLARE_TUNNEL_HERMES_DEV_SECRET, CLOUDFLARE_ZONE_MONTYGROUP, DEEPSEEK_API_KEY, GITHUB_TOKEN, HASS_TOKEN, NETZERO_API_TOKEN, PROXMOX_API_TOKEN, PROXMOX_URL, TELEGRAM_BOT_TOKEN, VERCEL_TOKEN, OPENAI_API_KEY

Also stored in the Hermes credential pool (`~/.hermes/auth.json`): deepseek, gemini (both auto-discovered from env vars).

**When provisioning a new Hermes container:** copy `~/.hermes-vault/` and `~/.hermes/.env.local` from the old container. The vault uses PBKDF2 + AES-256-GCM so it's safe to store in backups. Then run `hermes auth reset deepseek` to re-enable the pool.

### Backup Script

Located at `~/.hermes/scripts/hermes-backup.sh` (also symlinked to `~/.local/bin/hermes-backup`):

```bash
#!/bin/bash
# Hermes full backup - run weekly
BACKUP_DIR="/home/matth/hermes-backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
# 1. Push skills to GitHub (git add+commit+push)
# 2. Create tarball of ~/.hermes/ + ~/.hermes-vault/ (excludes git, node_modules, logs, sessions)
# 3. Prune old backups (keep last 8)
```

## Pitfalls

1. **API token must be `@pve` realm, not `@pam`** — `@pam` tokens don't get full access even with ACL modifications. The correct approach is a dedicated `@pve` user with Administrator role on `/`.

2. **Fresh containers have no SSH access** — you MUST use `pct exec` from the Proxmox shell to bootstrap. Always tell the user what commands to run. Provide the exact copy-paste block.

3. **`--data-urlencode` is required for `net0`** — the commas in `net0=name=eth0,bridge=vmbr0,ip=dhcp` break if passed with `-d`. Always use `--data-urlencode` for ALL params.

4. **Check existing VMIDs first** — use `curl -sk "$HOST/api2/json/cluster/resources?type=vm"` to find used VMIDs. Avoid conflicts (common in multi-user setups).

5. **Container IP takes time to appear** — DHCP lease acquisition after `pct start` can take 3-8 seconds. Don't try to SSH immediately.

6. **Unprivileged containers** — set `unprivileged=1` unless the container needs device access. Unprivileged is more secure and standard for web hosts.

7. **You can't install packages from Hermes VM onto the container** — all provisioning must go through `pct exec` or SSH. Don't try `apt-get` from outside.

8. **`curl -sk` disables SSL verification** — required for Proxmox's self-signed cert. Without `-k` you'll get certificate errors.

- **Token values are UUIDs** — they look like `19b5fd1b-9354-47fd-8847-4ebbe28a4abb`. The token string in the Authorization header is `<full-tokenid>=<value>` with an equals sign between them.
- **API tokens cannot delete ghost CTs, run shell commands, or access the pmxcfs directly** — see `references/api-token-limitations.md` for the full capability matrix.

10. **The ACL command for Proxmox** — correct syntax is `pveum acl modify / -user <user>@<realm> -role Administrator`. The older `pveum user modify` syntax with `-role` and `-path` options is incorrect.

11. **Token permissions propagate slowly** — after creating a token with Administrator role, there can be a 1-3 second delay before the API returns full data. If you see "Permission check failed", wait a moment and retry.

12. **`pct exec` won't work with commands that need TTY** — things like `passwd`, `vi`, or anything interactive. For `passwd`, provide the password via `chpasswd` piped input or set it during container creation with `password=<value>`.

13. **Web container nginx default config** — the default Debian nginx has a sites-enabled/default that takes priority. Always `rm -f /etc/nginx/sites-enabled/default` before enabling your site config.

14. **Container default storage is small** — `rootfs=local-lvm:4` creates a 4GB rootfs. Check your site size: a single 55KB HTML file with inline SVGs is fine, but if deploying multiple sites or Docker, bump to `rootfs=local-lvm:8` or higher.

15. **The `!` character in API token values explodes in bash** — `PVEAPIToken=hermes2@pve!api=19b5fd1b-...` contains a `!` which is history expansion in bash and will truncate the token after `!api`. To use the token in curl from bash, either:
    - Use single quotes for the header: `-H 'Authorization: PVEAPIToken=hermes2@pve!api=...'`
    - Or pass it via environment variable + Python (`urllib.request`) where string handling is safe
    - Or use `set +H` to disable history expansion before the curl call
    - When using `python3 -c` from terminal tool, pass the header value in Python directly via `urllib.request.Request(url, headers={"Authorization": token})` rather than through shell interpolation

16. **SSH key injection into containers via Proxmox API requires the user's cooperation** — there is no `POST /nodes/pve1/lxc/{vmid}/exec` endpoint for LXC containers in most Proxmox versions (returns HTTP 501). This means:
    - You cannot `mkdir` or write files inside a container via the API
    - You cannot install packages via the API
    - You MUST ask the user to run `pct exec` commands on the Proxmox host shell for any container bootstrapping
    - The Proxmox API users endpoint (`/access/users/root@pam`) accepts SSH keys via PUT with `Content-Type: application/x-www-form-urlencoded` but the key must match a strict regex pattern — raw `ssh-rsa AAAA...` lines may be rejected

17. **Proxmox backup jobs can be created via the API** — create vzdump schedules with:
    ```python
    import urllib.request, json, ssl
    token = "PVEAPIToken=hermes2@pve!api=..."
    base = "https://proxmox:8006/api2/json"
    ctx = ssl._create_unverified_context()
    body = json.dumps({
        "id": "hermes-backup",
        "schedule": "sun 04:00",
        "node": "pve1",
        "vmid": "200",
        "mode": "snapshot",
        "storage": "local",
        "compress": "zstd",
        "prune-backups": "keep-last=4",
        "enabled": 1,
    }).encode()
    req = urllib.request.Request(f"{base}/cluster/backup", data=body,
        headers={"Authorization": token, "Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, context=ctx, timeout=10)
    ```
    Note: the `!` in the token is safe inside Python strings — no bash explosion issue.
