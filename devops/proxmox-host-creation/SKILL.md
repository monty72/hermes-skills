---
name: proxmox-host-creation
description: "Provision and manage Proxmox VE LXC containers and VMs via the REST API — create containers, authenticate with API tokens, bootstrap SSH access, install nginx, and host static sites. Covers the full lifecycle from Proxmox API setup to a serving web host."
version: 1.5.0
author: Hermes Agent
platforms: [linux, macos]
---

# Proxmox Host Creation

Use this skill when provisioning machines on a **Proxmox VE** hypervisor via its REST API. This covers:
- Authenticating with API tokens or password
- Managing VM/container lifecycle (start, stop, onboot)
- Inspecting node resources (storage, templates, network)
- Creating LXC containers from templates
- Bootstrapping SSH access into containers
- Setting up nginx and deploying sites
- Adding a second Proxmox node (discovery, onboarding, validation, cluster join)
- Upgrading PVE 8→9 (Debian 12→13, conffile handling)
- Creating a 2-node cluster (hostname conflicts, fingerprint acceptance, heterogeneous HW)
- Power-outage recovery (DHCP drift, services restart)
- Cloud-image VM creation (Ubuntu, Kali, generic)

## Authentication

### API Token (PREFERRED)

```bash
Authorization: PVEAPIToken=<userid>@<realm>!<tokenid>=<token-value>

# Example
curl -sk https://<proxmox-host>:8006/api2/json/version \
  -H "Authorization: PVEAPIToken=hermes2@pve!api=19b5fd1b-9354-47fd-8847-4ebbe28a4abb"
```

**Token creation** (run on Proxmox shell):
```bash
pveum user add <name>@pve
pveum acl modify / -user <name>@pve -role Administrator
pveum user token add <name>@pve api --privsep 0
```

The last command prints a `value` UUID — that's the token secret. The `full-tokenid` is the token ID part.

**IMPORTANT:** Correct ACL syntax is `pveum acl modify / -user <name>@<realm> -role Administrator`. The incorrect `pveum user modify <userid> -role Administrator -path /` returns "Unknown option: role".

### User/Password (Fallback)

```bash
curl -sk -X POST https://<host>:8006/api2/json/access/ticket \
  --data-urlencode 'username=root@pam' \
  --data-urlencode 'password=<password>'
```

Response includes `ticket` (cookie) and `CSRFPreventionToken` (header). Use these for subsequent requests.

## VM/CT Actions via API

```text
POST /nodes/{node}/{type}/{vmid}/status/{action}
```

Where `type` is `qemu` or `lxc` and `action` is one of: `start`, `stop`, `shutdown`, `reboot`.

### Python pattern

```python
import urllib.request, ssl

def pve_action(vmid, action, token, pve_url, vm_type="qemu"):
    valid = {"start", "stop", "shutdown", "reboot"}
    if action not in valid:
        return False
    ctx = ssl._create_unverified_context()
    url = f"{pve_url}/nodes/pve1/{vm_type}/{vmid}/status/{action}"
    req = urllib.request.Request(url, data=b"",
        headers={"Authorization": token}, method="POST")
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10):
            return True
    except Exception:
        return False
```

**Type detection:** Determine `type` from `/cluster/resources?type=vm` — each resource has a `type` field of `"qemu"` or `"lxc"`.

### Curl examples

```bash
TOKEN="PVEAPIToken=hermes2@pve!api=19b5fd1b-..."
HOST="https://192.168.1.6:8006"

# Start a stopped VM
curl -sk -X POST "$HOST/api2/json/nodes/pve1/qemu/106/status/start" \
  -H "Authorization: $TOKEN" -d ''

# Graceful shutdown
curl -sk -X POST "$HOST/api2/json/nodes/pve1/qemu/105/status/shutdown" \
  -H "Authorization: $TOKEN" -d ''
```

## API Exploration

```bash
# Node status
curl -sk "$HOST/api2/json/nodes/pve1/status" -H "Authorization: $TOKEN" | python3 -c "
import sys, json
d = json.load(sys.stdin)['data']
m = d['memory']
print(f'RAM: {m.get(\"used\",0)/1e9:.1f}GB / {m.get(\"total\",0)/1e9:.1f}GB')
print(f'CPU: {d[\"cpu\"]*100:.1f}%')
print(f'Uptime: {d[\"uptime\"]//3600}h {(d[\"uptime\"]%3600)//60}m')
print(f'Disk: {d[\"rootfs\"][\"used\"]/1e9:.1f}GB / {d[\"rootfs\"][\"total\"]/1e9:.1f}GB')
print(f'PVE: {d.get(\"pveversion\",\"?\")}')
print(f'Kernel: {d[\"kversion\"]}')
"

# Storage pools
curl -sk "$HOST/api2/json/nodes/pve1/storage" -H "Authorization: $TOKEN"

# All VMs/containers (with status summary)
curl -sk "$HOST/api2/json/cluster/resources?type=vm" -H "Authorization: $TOKEN" | python3 -c "
import sys, json
vms = sorted(json.load(sys.stdin)['data'], key=lambda x: x.get('vmid',0))
for v in vms:
    name = v.get('name','?')
    vid = v.get('vmid','?')
    st = v.get('status','?')
    if st == 'running':
        mem = v.get('mem',0)/1e6
        cpu = v.get('cpu',0)*100
        print(f'  [{vid:<4}] {name:<15} RUNNING  CPU:{cpu:5.1f}%  RAM:{mem:6.0f}MB')
    else:
        print(f'  [{vid:<4}] {name:<15} {st.upper()}')
"

# Available LXC templates
curl -sk "$HOST/api2/json/nodes/pve1/storage/local/content" -H "Authorization: $TOKEN"

# Network bridges
curl -sk "$HOST/api2/json/nodes/pve1/network" -H "Authorization: $TOKEN"
```

## Creating an LXC Container

```bash
curl -sk -X POST "$HOST/api2/json/nodes/pve1/lxc" -H "Authorization: $TOKEN" \
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
- `vmid` — unique numeric ID (check existing VMs first)
- `ostemplate` — path to template on `local` storage
- `rootfs=local-lvm:4` — 4GB disk on lvmthin pool; bump for Docker or multi-site
- `net0` — use `--data-urlencode` for commas in value; `-d` will break parsing
- `--data-urlencode` is required for all params, NOT `-d`

**Response:** Returns a task UPID string. Task runs asynchronously.

### Wait for readiness

```bash
# Check task status
curl -sk "$HOST/api2/json/nodes/pve1/tasks/<UPID>/status" -H "Authorization: $TOKEN"

# Check container status
curl -sk "$HOST/api2/json/nodes/pve1/lxc/<vmid>/status/current" -H "Authorization: $TOKEN"

# Get IP address (DHCP may take 3-8s)
curl -sk "$HOST/api2/json/nodes/pve1/lxc/<vmid>/interfaces" -H "Authorization: $TOKEN"
# Look for eth0's inet field (first ip-address with type "inet" != 127.0.0.1)
```

## Bootstrapping SSH Access into a Fresh Container

Fresh LXC containers have **no SSH keys** and **no password set**. You cannot SSH in directly.

### Method 1: `pct exec` from Proxmox shell (requires user cooperation)

```bash
# Set root password
pct exec 200 -- passwd root

# Install nginx
pct exec 200 -- apt-get update -qq
pct exec 200 -- apt-get install -y -qq nginx curl

# Copy SSH key (handles unprivileged uid mapping correctly)
# Stage key on Proxmox host first:
scp -o StrictHostKeyChecking=no ~/.ssh/id_ed25519 root@<proxmox-ip>:/root/.ssh/

# Then push (pct push handles uid mapping - do NOT write to /var/lib/lxc directly)
ssh -o StrictHostKeyChecking=no root@<proxmox-ip> "
  pct exec <VMID> -- mkdir -p /root/.ssh
  pct push <VMID> /root/.ssh/id_ed25519 /root/.ssh/authorized_keys
  pct exec <VMID> -- chmod 600 /root/.ssh/authorized_keys
  pct exec <VMID> -- chmod 700 /root/.ssh
"
```

### Method 2: SSH with password (if already set)

```bash
ssh -o StrictHostKeyChecking=no root@<container-ip>
```

### Common SSH failure modes

| Error | Cause | Fix |
|-------|-------|-----|
| `Permission denied (publickey,password)` | No key set OR key not accepted | Use `pct exec` to verify the key was written correctly |
| `ssh_askpass: exec()` warning | SSH client trying password auth | Add `-o PasswordAuthentication=no` |
| `Connection refused` | SSH server not running | `pct exec <vmid> -- systemctl restart sshd` |
| Host key changed | Container recreated | `ssh-keygen -R <ip>` |

## Setting Up nginx

```bash
cat > /etc/nginx/sites-available/<sitename> << 'EOF'
server {
    listen 80;
    server_name _;
    root /var/www/<sitename>;
    index index.html;
    location / { try_files $uri $uri/ =404; }
}
EOF
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/<sitename> /etc/nginx/sites-enabled/
systemctl restart nginx
```

### Piping configs via heredoc + pct exec tee

```bash
cat << 'EOF' | pct exec <VMID> -- tee /path/to/file > /dev/null
server {
    listen 80;
    ...
}
EOF
```

## Copying Site Files

```bash
# Single files
scp -o StrictHostKeyChecking=no index.html root@<container-ip>:/var/www/<sitename>/

# Entire directory
scp -o StrictHostKeyChecking=no -r site/* root@<container-ip>:/var/www/<sitename>/
```

### When SSH is blocked — pct push from Proxmox host

```bash
# Stage file on Proxmox host
curl -s http://<hermes-vm>:<port>/<path> > /tmp/<filename>

# Push (handles uid mapping)
pct push <VMID> /tmp/<filename> /var/www/<sitename>/<filename>
```

## Startup Configuration (onboot / Boot Order)

Configure VMs/containers to auto-start when the Proxmox host boots. Essential for homelabs with power cuts.

### QEMU VMs

```bash
# Enable auto-start
curl -sk -X PUT "$HOST/api2/json/nodes/pve1/qemu/<VMID>/config" \
  -H "Authorization: $TOKEN" \
  --data-urlencode 'onboot=1'

# With staggered boot order
curl -sk -X PUT "$HOST/api2/json/nodes/pve1/qemu/<VMID>/config" \
  -H "Authorization: $TOKEN" \
  --data-urlencode 'onboot=1' \
  --data-urlencode 'startup=order=2'

# Disable
curl -sk -X PUT "$HOST/api2/json/nodes/pve1/qemu/<VMID>/config" \
  -H "Authorization: $TOKEN" \
  --data-urlencode 'onboot=0' \
  --data-urlencode 'startup='
```

### LXC Containers

Replace `qemu` with `lxc` in the URL path:
```bash
curl -sk -X PUT "$HOST/api2/json/nodes/pve1/lxc/<VMID>/config" \
  -H "Authorization: $TOKEN" \
  --data-urlencode 'onboot=1' \
  --data-urlencode 'startup=order=4'
```

**Lock contention:** If the container just started, the config may be locked (`can't lock file '/run/lock/lxc/pve-config-<VMID>.lock'`). Wait a few seconds and retry.

### Verification — config endpoint not cluster cache

The `/cluster/resources?type=vm` API **caches** the `onboot` value. Always verify against the direct config:

```bash
curl -sk "$HOST/api2/json/nodes/pve1/qemu/<VMID>/config" \
  -H "Authorization: $TOKEN" | python3 -c "
import sys, json
d = json.load(sys.stdin)['data']
print(f'onboot: {d.get(\"onboot\",0)}')
print(f'startup: {d.get(\"startup\",\"not set\")}')
"
```

### Staggered Boot Order Strategy

| Order | Type | Purpose |
|-------|------|---------|
| 1 | Core services | DNS, DHCP, HA |
| 2 | Stateful infra | Databases, message queues |
| 3 | Compute workers | Docker hosts, Hermes workers |
| 4+ | Stateless apps | Web servers, dev VMs |

On this homelab (Proxmox 192.168.1.6): 102 HA(order=1), 106 Kali/Neo(order=2), 104 OpenCrawl(order=3), 200 web(order=4), 105 Hermes(onboot=1, no explicit order).

## Multi-Node Discovery

When bringing a second Proxmox node online, DHCP may assign an unexpected IP. Scan the LAN for it.

### 1. Scan for port 8006 (Proxmox API) — no nmap needed

```bash
# Fast /24 scan using bash /dev/tcp
for ip in $(seq 1 254); do
  timeout 1 bash -c "echo >/dev/tcp/192.168.1.$ip/8006" 2>/dev/null && echo "192.168.1.$ip"
done
```

Takes ~60s for full /24. Optimise by scanning likely ranges first.

### 2. Identify the node

```bash
# Authenticate with root password (cross-node API tokens don't work pre-cluster)
curl -sk -X POST 'https://<node-ip>:8006/api2/json/access/ticket' \
  --data-urlencode 'username=root@pam' \
  --data-urlencode 'password=<password>'
```

Response includes `ticket` (cookie) and `CSRFPreventionToken` - use these for subsequent API calls.

### 3. Hardware validation

```bash
ssh root@<node-ip> '
  echo "=== CPU ==="
  lscpu | grep -E "Model name|CPU\(s\)|Thread|Core"
  echo "=== RAM ==="
  free -h
  echo "=== Disks ==="
  lsblk -d -o NAME,SIZE,MODEL,ROTA
  echo "=== Storage ==="
  pvesm status
  echo "=== PVE ==="
  pveversion
'
```

### 4. Full Node Onboarding

**Step 1 — Inject SSH key**

The Proxmox API endpoint `PUT /access/users/root@pam` rejects `ssh-keys` as an unknown property (root is a `pam` realm user; only `@pve` realm users accept SSH keys in their schema). Use sshpass instead:

```bash
sudo apt-get install -y sshpass
sshpass -p '<root-password>' ssh-copy-id -o StrictHostKeyChecking=accept-new root@<node-ip>
ssh root@<node-ip> 'hostname && pveversion'
```

**Step 2 — Fix repositories**

Fresh installs ship with enterprise repo enabled (requires subscription key):

```bash
ssh root@<node-ip> '
  sed -i "s/^deb/#deb/" /etc/apt/sources.list.d/pve-enterprise.list 2>/dev/null || true
  sed -i "s/^deb/#deb/" /etc/apt/sources.list.d/ceph.list 2>/dev/null || true
  echo "deb http://download.proxmox.com/debian/pve bookworm pve-no-subscription" \
    > /etc/apt/sources.list.d/pve-no-subscription.list
  apt-get update -qq
'
```

**Step 3 — Full dist-upgrade** (200+ packages common on fresh installs)

```bash
ssh root@<node-ip> 'DEBIAN_FRONTEND=noninteractive apt-get dist-upgrade -y -qq'
```

Check progress: `ssh root@<node-ip> 'tail -3 /var/log/dpkg.log'`

**Step 4 — Network connectivity to existing node**

```bash
ssh root@<node-ip> "ping -c 2 -W 2 <existing-node-ip>"
```

Sub-second ping = same switch, ready for cluster join.

**Step 5 — Set onboot for VMs** (see Startup Configuration section above)

## Cluster Creation (Multi-Node)

Create a Proxmox cluster between nodes, including heterogeneous hardware (AMD + Intel). A cluster turns several standalone hypervisors into one management plane with HA, live migration, and a single web UI.

### Pre-requisites

- Both nodes reachable on the same L2 network (sub-ms ping)
- Root passwords known for both nodes
- PVE versions should match (upgrade lower version first — see PVE 8→9 Upgrade below)
- Decide on a cluster name (e.g. `homelab`, `production`)

### Step 1: Create the cluster on Node 1

```bash
ssh root@<node1-ip> 'pvecm create <clustername>'
```

Generates corosync keys in `/etc/pve/corosync.conf`. Verify with `pvecm status` — should show 1 node, quorate.

### Step 2: Fix hostname conflicts

Fresh Proxmox installs default to hostname `pve`. If both nodes are `pve`, the cluster join fails with `hostname lookup 'pve' failed`. Rename Node 2:

```bash
ssh root@<node2-ip> '
  echo "<new-hostname>" > /etc/hostname
  hostname <new-hostname>
  echo "<node2-ip> <new-hostname>" >> /etc/hosts
  hostname -f   # verify resolves
'
```

### Step 3: Join Node 2 to the cluster

`pvecm add` is interactive — it prompts for API certificate fingerprint acceptance and root password. SSH key auth alone isn't enough; the API client needs fingerprint confirmation.

**Expect script (reliable for non-interactive SSH):**

```bash
ssh root@<node2-ip> 'apt-get install -y expect -qq'

cat > /tmp/pvecm.exp << 'EXPECT'
#!/usr/bin/expect -f
set timeout 60
spawn pvecm add <node1-ip> --force
expect {
    "Are you sure" { send "yes\r"; exp_continue }
    "assword" { send "<root-password>\r"; exp_continue }
    eof { puts "DONE"; exit 0 }
    timeout { puts "TIMEOUT"; exit 1 }
}
EXPECT
chmod +x /tmp/pvecm.exp
/tmp/pvecm.exp
```

**Why `--force`:** If Node 2 has existing configured VMs/containers, `pvecm add` refuses with `"this host already contains virtual guests"`. `--force` overrides this check.

**Lock contention:** Stale locks at `/var/lock/pvecm.lock` from failed attempts block subsequent joins. Remove with `rm -f /var/lock/pvecm.lock`.

**Monitor progress:** The join process: password auth → fingerprint prompt → API version check → joins request → stops local pve-cluster → syncs database → regenerates certificates → restarts pveproxy/pvedaemon → "successfully added node 'X' to cluster."

### Step 4: Verify cluster health

```bash
# From either node
pvecm status

# From the API
curl -sk "https://<node1>:8006/api2/json/cluster/status" \
  -H "Authorization: PVEAPIToken=..." | python3 -c "
import sys, json
data = json.load(sys.stdin)['data']
for item in data:
    if 'name' in item and 'ip' in item:
        print(f\"  {item['name']} @ {item['ip']}  type={item['type']} status={item.get('status')}\")
    elif 'quorate' in item:
        print(f\"  Quorum: {'Yes' if item['quorate'] else 'No'}\")
"
```

Expected: 2 nodes listed, `quorate: Yes`.

### Heterogeneous hardware considerations

Proxmox clusters **fully support** different CPU vendors, RAM sizes, and storage:

| Concern | Reality |
|---------|---------|
| **Different CPUs** (AMD vs Intel) | ✅ Works. For **live migration** between them, set VM CPU type to `x86-64-v2-AES` |
| **Different RAM sizes** (e.g. 64GB vs 31GB) | ✅ HA only starts VMs on nodes with enough free RAM |
| **Different storage** | ✅ Use local storage per node or shared Ceph/NFS |
| **PVE version gap** (e.g. 9.2 vs 8.4) | ⚠️ Cluster requires matching major versions; upgrade first |

### What clustering unlocks

- **HA** — if one node dies, VMs restart on the other
- **Live migration** — move VMs between nodes with zero downtime
- **Single pane of glass** — manage both nodes from one web UI
- **Quorum** — 2 nodes need a 3rd witness (RPi, LXC, QDevice) for proper HA to avoid split-brain

## PVE 8→9 Major Upgrade (Debian 12 → 13)

A major PVE upgrade moves the entire OS from Debian 12 (bookworm) to Debian 13 (trixie). Typically 200+ packages and a kernel bump (6.8.x → 7.0.x). Do this **before** joining to a cluster to keep versions matching.

### Step 1: Switch repos from bookworm → trixie

```bash
ssh root@<node-ip> '
  cat > /etc/apt/sources.list << EOF
deb http://ftp.uk.debian.org/debian trixie main contrib
deb http://ftp.uk.debian.org/debian trixie-updates main contrib
deb http://security.debian.org trixie-security main contrib
EOF

  sed -i "s/bookworm/trixie/g" /etc/apt/sources.list.d/pve-no-subscription.list 2>/dev/null || true
  apt-get update -qq
'
```

### Step 2: Run the dist-upgrade

```bash
ssh root@<node-ip> 'DEBIAN_FRONTEND=noninteractive apt-get dist-upgrade -y -qq'
```

**Check progress:** `ssh root@<node-ip> 'tail -3 /var/log/dpkg.log'`

### Step 3: Handle conffile prompts (most common failure)

`DEBIAN_FRONTEND=noninteractive` doesn't always suppress conffile prompts. The typical blockers:

**`lvm2` — `/etc/lvm/lvm.conf`:** The package maintainer's version ships with Proxmox-specific `global_filter` settings. If the default action is `N` (keep old), dpkg hangs. Fix:

```bash
ssh root@<node-ip> 'DEBIAN_FRONTEND=noninteractive apt-get install -y \
  -o Dpkg::Options::="--force-confnew" lvm2'
```

This accepts the new config, which unlocks all dependent PVE packages (pve-manager, qemu-server, pve-container, etc.).

**Other conffile prompts:** Run `dpkg --configure -a --force-confdef --force-confold` to push through any remaining prompts with the "keep old" default.

### Step 4: Clean up and reboot

```bash
ssh root@<node-ip> '
  DEBIAN_FRONTEND=noninteractive apt-get dist-upgrade -y -qq --allow-downgrades
  apt-get autoremove --purge -y -qq
  reboot
'
```

Check after reboot: `pveversion` should show PVE 9.x and `uname -r` should show 7.x kernel.

### Step 5: Fix GRUB (if prompted)

Some PVE 8→9 upgrades warn about removable bootloader config:

```bash
echo "grub-efi-amd64 grub2/force_efi_extra_removable boolean true" | debconf-set-selections -v -u
apt-get install --reinstall -y grub-efi-amd64
```

On systems with `systemd-boot` instead of GRUB, this message is cosmetic — the bootloader update already ran via `/etc/kernel/postinst.d/zz-proxmox-boot`.

## Post-Power-Outage Recovery

After a power cut: Proxmox boots before VMs. VMs with `onboot=1` start in order, but **DHCP leases may change** (e.g. .137 → .138).

### Step 1: Check which VMs are stopped

```bash
curl -sk "$HOST/api2/json/cluster/resources?type=vm" -H "Authorization: $TOKEN" | python3 -c "
import sys, json
vms = sorted(json.load(sys.stdin)['data'], key=lambda x: x.get('vmid',0))
for v in vms:
    print(f'  VM {v.get(\"vmid\",\"?\"):<5} {v.get(\"name\",\"?\"):<20} status={v.get(\"status\",\"?\"):<8} type={v.get(\"type\",\"?\")}')
"
```

### Step 2: Start stopped VMs

```bash
for vmid in 104 106; do
  curl -sk -X POST "$HOST/api2/json/nodes/pve1/qemu/$vmid/status/start" -H "Authorization: $TOKEN" -d ''
done
```

### Step 3: Find VMs after DHCP IP change

If SSH fails with "No route to host", the IP changed:

```bash
for ip in $(seq 130 150); do
  ping -c 1 -W 1 "192.168.1.$ip" >/dev/null 2>&1 && \
    ssh -o ConnectTimeout=2 user@192.168.1.$ip 'hostname' 2>/dev/null
done
```

After finding the new IP, update: SSH config, cron jobs, skill references (like `opencrawl-worker-delegation`), and any scripts/inventory.

### Step 4: Check services came up

```bash
ssh user@<new-ip> 'systemctl --user is-active hermes-gateway'
ssh user@<new-ip> 'systemctl --user is-active hermes-worker && curl -s http://localhost:8081/health'
```

### Step 5: Pin DHCP lease (prevent future drift)

Assign a static IP via cloud-init, netplan, or a static DHCP reservation on your router.

## Orphan Resource Cleanup

### Ghost Container / Phantom VM

Appears in cluster resources with `status: "unknown"` and no name. Config file no longer exists.

**Detection:**
```bash
curl -sk "$HOST/api2/json/nodes/pve1/lxc/<VMID>/config" -H "Authorization: $TOKEN"
# Returns: "Configuration file does not exist"
```

**Removal (requires root@pam shell - API token can't do this):**
```bash
pvesh delete /cluster/config/lxc/<VMID>
```

### Stale ISOs and Templates

```bash
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

**Delete:**
```bash
curl -sk -X DELETE "$HOST/api2/json/nodes/pve1/storage/local/content/local:iso/<filename>" -H "Authorization: $TOKEN"
curl -sk -X DELETE "$HOST/api2/json/nodes/pve1/storage/local/content/local:vztmpl/<filename>" -H "Authorization: $TOKEN"
```

## Creating a VM from a Cloud Image (Cloud-Init)

For QEMU/KVM VMs when LXC won't cut it (Docker, custom kernels, full isolation).

**Pattern:** `download → create skeleton → import disk → cloud-init → resize → boot → verify`

### Download image

```bash
wget 'https://cloud-images.ubuntu.com/releases/noble/release/ubuntu-24.04-server-cloudimg-amd64.img' \
  -O /root/ubuntu-24.04-server-cloudimg-amd64.img
file /root/ubuntu-24.04-server-cloudimg-amd64.img  # Should say: QEMU QCOW Image
```

### Create VM

```bash
qm create <VMID> --name <name> --memory <MB> --cores <N> --cpu host \
  --net0 virtio,bridge=vmbr0 --agent enabled=1 --ostype l26

qm importdisk <VMID> /path/to/cloud-image.img local-lvm

qm set <VMID> \
  --scsihw virtio-scsi-pci \
  --scsi0 local-lvm:vm-<VMID>-disk-0 \
  --boot order=scsi0

qm set <VMID> --ide2 local-lvm:cloudinit
```

**Content type trap:** `--ide2 local:cloudinit` fails with "storage 'local' does not support content-type 'images'". Always use `local-lvm` for the cloudinit drive.

### Cloud-init config

```bash
qm set <VMID> \
  --ciuser <username> \
  --sshkeys <(echo 'ssh-ed25519 AAAA...') \
  --ipconfig0 ip=dhcp
```

**SSH key trap:** `--sshkeys` accepts the key CONTENT, not a file path. Use process substitution. If you use `--sshkey /root/.ssh/authorized_keys`, it injects the **Proxmox host's** keys, not the agent's.

### Resize, boot, find IP

```bash
qm resize <VMID> scsi0 50G
qm start <VMID>

# Find IP:
nmap -sn <subnet>/24 | grep -B 2 '<MAC>'
# Or via guest agent:
qm guest exec <VMID> -- ip addr show
```

### Post-boot: Install QEMU Guest Agent

```bash
ssh <user>@<vm-ip> "sudo apt-get update && sudo apt-get install -y qemu-guest-agent && sudo systemctl start qemu-guest-agent"
```

**Note:** Don't `systemctl enable` — it has no [Install] section. udev auto-activates on reboot.

### Kali Linux Cloud Image

Kali ships as `.tar.xz` containing `disk.raw` (not a direct `.qcow2`). PEP 668 blocks system pip (use pipx).

```bash
tar xf kali-linux-2026.1-cloud-genericcloud-amd64.tar.xz
qemu-img convert -f raw -O qcow2 disk.raw kali.qcow2
rm disk.raw

qm create 106 --name kali --memory 4096 --cores 4 --cpu host \
  --net0 virtio,bridge=vmbr0 --agent enabled=1 --ostype l26
qm importdisk 106 kali.qcow2 local-lvm
qm set 106 --scsihw virtio-scsi-pci --scsi0 local-lvm:vm-106-disk-0 --boot order=scsi0
qm set 106 --ide2 local-lvm:cloudinit --ciuser root \
  --sshkeys <(echo 'ssh-ed25519 AAAA...') --ipconfig0 ip=dhcp
qm resize 106 scsi0 50G
qm start 106
```

## Hermes Backup Setup

### Proxmox vzdump backup job

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

### Credential vault

API keys at `~/.hermes-vault/` (AES-256-GCM, passphrase in `~/.hermes/.env.local`). CLI: `hermes-vault <get|set|list|delete>`.

## Modifying Running VM Config (RAM, CPU, etc.)

Change VM resources on a running or stopped VM via the Proxmox API. Works with both `qemu` and `lxc` types.

```bash
TOKEN="PVEAPIToken=hermes2@pve!api=..."
HOST="https://192.168.1.6:8006"

# Change RAM (e.g. 4GB → 8GB on VM 106)
curl -sk -X PUT "$HOST/api2/json/nodes/pve1/qemu/106/config" \
  -H "Authorization: $TOKEN" \
  --data-urlencode 'memory=8192'

# Change CPU cores
curl -sk -X PUT "$HOST/api2/json/nodes/pve1/qemu/106/config" \
  -H "Authorization: $TOKEN" \
  --data-urlencode 'cores=4'
```

**RAM changes require a VM reboot to take effect** — the config is updated immediately but the running VM won't see new resources until the next boot.

### Snapshot Policy: Always Snapshot Before Destructive Changes

Before any change that requires a reboot or modifies core system resources (RAM, CPU, disk resize, network change, OS upgrade), **take a Proxmox snapshot first**. This is the user's preferred safety pattern — ensures instant rollback if the change causes boot failure or instability.

```bash
# Take a snapshot
curl -sk -X POST "$HOST/api2/json/nodes/pve1/qemu/106/snapshot" \
  -H "Authorization: $TOKEN" \
  --data-urlencode 'snapname=pre-memory-upgrade' \
  --data-urlencode 'vmstate=0' \
  --data-urlencode 'description=Snapshot before 4GB→8GB RAM upgrade'

# Verify snapshot exists
curl -sk "$HOST/api2/json/nodes/pve1/qemu/106/snapshot" \
  -H "Authorization: $TOKEN" | python3 -m json.tool

# Rollback if something goes wrong
curl -sk -X POST "$HOST/api2/json/nodes/pve1/qemu/106/snapshot/pre-memory-upgrade/rollback" \
  -H "Authorization: $TOKEN" -d ''

# Clean up the snapshot after confirming stability (e.g. 24h later)
curl -sk -X DELETE "$HOST/api2/json/nodes/pve1/qemu/106/snapshot/pre-memory-upgrade" \
  -H "Authorization: $TOKEN"
```

**Snapshot naming convention:** `pre-<description-of-change>` — e.g. `pre-memory-upgrade`, `pre-kernel-update`, `pre-os-upgrade`.

**When to snapshot:**
| Trigger | Snapshot needed? |
|---------|----------------|
| RAM/CPU change + reboot | ✅ Yes |
| Disk resize (online) | ⚠️ Only if resize risks data |
| Kernel/OS upgrade | ✅ Yes |
| Config change (HDMI, boot order, no reboot) | ❌ No |
| Adding a new disk (hotplug) | ❌ No |

### Post-change verification

After applying a config change and rebooting:

```bash
# 1. VM back and running
curl -sk "$HOST/api2/json/nodes/pve1/qemu/106/status/current" \
  -H "Authorization: $TOKEN" | python3 -c "
import sys, json; d=json.load(sys.stdin)['data']
print(f'Status: {d.get(\"status\")}')
print(f'RAM (config): {d.get(\"maxmem\",0)/1024/1024:.0f}MB')
print(f'Uptime: {d.get(\"uptime\",0)//3600}h')
"

# 2. SSH reachable + services running
ssh -o ConnectTimeout=10 -o BatchMode=yes root@<vm-ip> 'free -h | grep Mem'

# 3. Confirm Telegram/Discord gateway reconnected (if applicable)
ssh -o ConnectTimeout=10 root@<vm-ip> 'systemctl is-active hermes-gateway'
```

## Pitfalls

1. **Container IP takes time** --- DHCP after `pct start` takes 3-8s. Don't SSH immediately.

2. **Unprivileged containers** --- set `unprivileged=1` unless the container needs device access.

3. **Can't install packages from outside** — all provisioning goes through `pct exec` or SSH.

4. **`curl -sk` required** — Proxmox's self-signed cert needs `-k`.

5. **API token `!` in bash** — `PVEAPIToken=user@pve!id=value` contains `!` (history expansion). Use single quotes in curl: `-H 'Authorization: PVEAPIToken=...'`. Safe in Python strings.

6. **`PUT /access/users/root@pam` rejects `ssh-keys`** — PVE 8.x returns `"ssh-keys: property is not defined in schema"`. Root is a `pam` realm user; only `@pve` users accept SSH keys in their schema. Use sshpass + ssh-copy-id instead.

7. **API tokens from node1 don't work on node2 pre-cluster** — Token is scoped to the `pve` realm on a specific cluster. Until nodes are clustered, use root password.

8. **Ghost containers (unknown status)** — Config file removed but pmxcfs still caches the entry. API can't delete them; requires `pvesh delete` from root@pam shell.

9. **Token permissions propagate slowly** — 1-3s delay after creation. If you see "Permission check failed", wait and retry.

10. **`pct exec` doesn't work with TTY commands** — `passwd`, `vi`, etc. are interactive. Use `chpasswd` piped input or set during creation.

11. **LXC containers can't be exec'd via API** — `POST /nodes/pve1/lxc/{vmid}/exec` returns 501 in most PVE versions. Must use `pct exec` from the Proxmox shell.

12. **Storage content type mismatch** — `local` storage doesn't support `images` content type. Cloudinit drives and VM disks must use `local-lvm`.

13. **`--sshkeys` is content, not a path** — Use process substitution: `--sshkeys <(echo 'ssh-ed25519 AAAA...')`.

14. **Web container nginx default** — `rm -f /etc/nginx/sites-enabled/default` before enabling your site config.

15. **Container default storage is small** — `rootfs=local-lvm:4` = 4GB. Bump for Docker or multi-site deployments.

16. **Vault path in background processes** — Use absolute path `~/.local/bin/hermes-vault` via `os.path.expanduser()`. Background tasks may not have `~/.local/bin/` on PATH.

17. **`onboot` cluster cache is stale** — The `/cluster/resources` API caches `onboot: 0` even after setting it. Verify via the direct VM config endpoint instead.

18. **Stopping pve-cluster breaks all access** — If you `systemctl stop pve-cluster` on a node, the Proxmox API, web UI, and SSH key auth all stop working (pmxcfs provides the access control layer). Recovery requires password-based SSH or physical console to restart `systemctl start pve-cluster`.

19. **`pvecm add` stale lock** — Failed join attempts leave `/var/lock/pvecm.lock`. Remove with `rm -f /var/lock/pvecm.lock` before retrying.
