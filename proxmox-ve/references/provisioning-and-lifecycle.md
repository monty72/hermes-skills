# Proxmox — Provisioning & Lifecycle Management

*Full reference absorbed from the former `proxmox-host-creation` skill.*

## Authentication

### API Token (preferred)
```bash
Authorization: PVEAPIToken=<userid>@<realm>!<tokenid>=<token-value>
# Example
curl -sk https://192.168.1.6:8006/api2/json/version \
  -H 'Authorization: PVEAPIToken=hermes2@pve!api=19b5fd1b-...'
```

**Token creation** (on Proxmox shell):
```bash
pveum user add <name>@pve
pveum acl modify / -user <name>@pve -role Administrator
pveum user token add <name>@pve api --privsep 0
```
Correct ACL syntax: `pveum acl modify / -user <user>@<realm> -role Administrator`
NOT: `pveum user modify <userid> -role Administrator -path /`

**Caveats:** `!` in token triggers bash history expansion — use single quotes in curl. Token permissions propagate slowly (1-3s delay). API tokens from node1 don't work on node2 pre-cluster.

### User/Password (fallback)
```bash
curl -sk -X POST 'https://<host>:8006/api2/json/access/ticket' \
  --data-urlencode 'username=root@pam' \
  --data-urlencode 'password=<password>'
```
Response: `ticket` (cookie) + `CSRFPreventionToken` (header).

## VM/CT Lifecycle

```text
POST /nodes/{node}/{type}/{vmid}/status/{action}
```
Where `type` = `qemu` or `lxc`, `action` = `start|stop|shutdown|reboot`.

## API Exploration

```bash
# Node status
curl -sk "$HOST/api2/json/nodes/pve1/status" -H "Authorization: $TOKEN" | python3 ...

# Storage pools
curl -sk "$HOST/api2/json/nodes/pve1/storage" -H "Authorization: $TOKEN"

# All VMs/CTs
curl -sk "$HOST/api2/json/cluster/resources?type=vm" -H "Authorization: $TOKEN"

# LXC templates
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

**Use `--data-urlencode`** for all params (especially net0 with commas). Returns task UPID. Wait for readiness:
```bash
curl -sk "$HOST/api2/json/nodes/pve1/tasks/<UPID>/status" -H "Authorization: $TOKEN"
curl -sk "$HOST/api2/json/nodes/pve1/lxc/<vmid>/interfaces" -H "Authorization: $TOKEN"
```

## Bootstrapping SSH into a Fresh Container

No SSH keys set, no password. Use `pct exec` from Proxmox host:
```bash
ssh root@<proxmox-ip> "
  pct exec <VMID> -- mkdir -p /root/.ssh
  pct push <VMID> /root/.ssh/id_ed25519 /root/.ssh/authorized_keys
  pct exec <VMID> -- chmod 600 /root/.ssh/authorized_keys
"
```
`pct push` handles uid mapping. `scp` into container won't work without keys.

## Setting Up nginx

```bash
cat > /etc/nginx/sites-available/<sitename> << 'EOF'
server { listen 80; server_name _; root /var/www/<sitename>; index index.html; }
EOF
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/<sitename> /etc/nginx/sites-enabled/
systemctl restart nginx
```

Pipe via `pct exec`:
```bash
cat << 'EOF' | pct exec <VMID> -- tee /path/to/file > /dev/null
...
EOF
```

## Startup Configuration (onboot)

```bash
# QEMU VM
curl -sk -X PUT "$HOST/api2/json/nodes/pve1/qemu/<VMID>/config" \
  -H "Authorization: $TOKEN" --data-urlencode 'onboot=1' --data-urlencode 'startup=order=2'

# LXC
curl -sk -X PUT "$HOST/api2/json/nodes/pve1/lxc/<VMID>/config" \
  -H "Authorization: $TOKEN" --data-urlencode 'onboot=1' --data-urlencode 'startup=order=4'
```

**Verify via direct config** (not cluster cache):
```bash
curl -sk "$HOST/api2/json/nodes/pve1/qemu/<VMID>/config" -H "Authorization: $TOKEN"
```

**Lock contention:** If config is locked (`can't lock file /run/lock/lxc/pve-config-<VMID>.lock`), wait and retry.

## Creating a VM from a Cloud Image

Pattern: `download → qm create → importdisk → set → cloud-init → resize → start`

```bash
qm create <VMID> --name <name> --memory <MB> --cores <N> --cpu host \
  --net0 virtio,bridge=vmbr0 --agent enabled=1 --ostype l26
qm importdisk <VMID> /path/to/ubuntu-24.04-server-cloudimg-amd64.img local-lvm
qm set <VMID> --scsihw virtio-scsi-pci --scsi0 local-lvm:vm-<VMID>-disk-0 --boot order=scsi0
qm set <VMID> --ide2 local-lvm:cloudinit  # NOT local:cloudinit
qm set <VMID> --ciuser <user> --sshkeys <(echo 'ssh-ed25519 AAAA...') --ipconfig0 ip=dhcp
qm resize <VMID> scsi0 50G
qm start <VMID>
```

**Kali Linux:** ships as `.tar.xz` containing `disk.raw`. Convert: `qemu-img convert -f raw -O qcow2 disk.raw kali.qcow2`.

**Key pitfalls:** `--ide2 local:cloudinit` fails with "does not support content-type 'images'" — use `local-lvm`. `--sshkeys` takes content, not a path. QEMU guest agent -- `systemctl enable` fails (no [Install]), use `systemctl start` only.

## Multi-Node & Cluster Management

### Finding a Second Node on LAN
```bash
for ip in $(seq 1 254); do
  timeout 1 bash -c "echo >/dev/tcp/192.168.1.$ip/8006" 2>/dev/null && echo "192.168.1.$ip"
done
```

### Full Node Onboarding
1. **Inject SSH key** — Use `sshpass` (API `PUT /access/users/root@pam` rejects `ssh-keys`)
2. **Fix repos** — Disable enterprise, enable no-subscription
3. **Dist-upgrade** — `DEBIAN_FRONTEND=noninteractive apt-get dist-upgrade -y -qq`
4. **Network check** — `ping -c 2 <existing-node-ip>` (sub-ms = ready for cluster)

### Cluster Creation
```bash
# Step 1: Create on node1
ssh root@<node1-ip> 'pvecm create <clustername>'

# Step 2: Fix hostname conflicts
ssh root@<node2-ip> 'echo "new-hostname" > /etc/hostname; hostname new-hostname'

# Step 3: Join node2 (uses expect for interactive prompts)
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
chmod +x /tmp/pvecm.exp && /tmp/pvecm.exp
```

**Heterogeneous** (AMD + Intel): Cluster supports different CPUs. For live migration, set CPU type to `x86-64-v2-AES`.

## PVE 8→9 Upgrade (Debian 12→13)

```bash
# Switch repos
ssh root@<node-ip> 'cat > /etc/apt/sources.list << EOF
deb http://ftp.uk.debian.org/debian trixie main contrib
deb http://ftp.uk.debian.org/debian trixie-updates main contrib
deb http://security.debian.org trixie-security main contrib
EOF'
ssh root@<node-ip> 'sed -i "s/bookworm/trixie/g" /etc/apt/sources.list.d/pve-no-subscription.list'

# Dist-upgrade
ssh root@<node-ip> 'DEBIAN_FRONTEND=noninteractive apt-get dist-upgrade -y -qq'

# Handle lvm2 conffile prompt (common failure)
ssh root@<node-ip> 'DEBIAN_FRONTEND=noninteractive apt-get install -y -o Dpkg::Options::="--force-confnew" lvm2'

# Clean up
ssh root@<node-ip> 'DEBIAN_FRONTEND=noninteractive apt-get dist-upgrade -y -qq --allow-downgrades && apt-get autoremove --purge -y -qq && reboot'
```

## Power-Outage Recovery
1. Check which VMs are stopped: `curl .../cluster/resources?type=vm`
2. Start stopped VMs
3. Find VMs after DHCP IP change (scan IP range)
4. Check services came up
5. Pin DHCP lease (static reservation)

## Modifying Running VM Config

```bash
# Change RAM (requires reboot)
curl -sk -X PUT "$HOST/api2/json/nodes/pve1/qemu/106/config" \
  -H "Authorization: $TOKEN" --data-urlencode 'memory=8192'

# Always snapshot first!
curl -sk -X POST "$HOST/api2/json/nodes/pve1/qemu/106/snapshot" \
  -H "Authorization: $TOKEN" \
  --data-urlencode 'snapname=pre-memory-upgrade' \
  --data-urlencode 'vmstate=0'
```

## Hermes Backup via Proxmox

```python
body = json.dumps({
    "id": "hermes-backup",
    "schedule": "sun 04:00",
    "node": "pve1", "vmid": "200",
    "mode": "snapshot", "storage": "local",
    "compress": "zstd", "prune-backups": "keep-last=4",
    "enabled": 1,
}).encode()
req = urllib.request.Request(f"{base}/cluster/backup", data=body, ...)
```

## Key Pitfalls

1. Container IP takes 3-8s (DHCP) — don't SSH immediately
2. Unprivileged containers: `unprivileged=1` unless device access needed
3. `curl -sk` required — Proxmox self-signed cert
4. `!` in API tokens — use single quotes in bash
5. `PUT /access/users/root@pam` rejects `ssh-keys` — root is pam realm, use sshpass
6. API tokens don't work cross-node pre-cluster — use root password
7. Ghost containers require `pvesh delete` from root@pam shell
8. `pct exec` doesn't work with TTY commands (passwd, vi) — use `chpasswd`
9. LXC can't be exec'd via API (`POST .../exec` returns 501) — use `pct exec`
10. Storage content type mismatch — `local` can't store images, use `local-lvm`
11. `--sshkeys` is content, not a path — use process substitution
12. Web container: `rm -f /etc/nginx/sites-enabled/default` before enabling site
13. Default container storage is 4GB — bump for Docker
14. `onboot` cluster cache is stale — verify via direct VM config
15. Stopping pve-cluster breaks ALL access — recovery requires password SSH or console
