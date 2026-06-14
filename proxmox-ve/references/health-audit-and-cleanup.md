# Proxmox — Health Audit & Cleanup

*Full reference absorbed from the former `proxmox-health-audit` skill.*

## Quick Health Check (Fast Path)

Run this for any "check Proxmox" request — no API token needed with root SSH:

```bash
ssh root@<proxmox-ip> "
echo '=== SYSTEM ==='; uptime -p
echo '=== CPU ==='; nproc; cat /proc/loadavg
echo '=== MEMORY ==='; free -h
echo '=== DISK ==='; df -h | grep -E '^/dev|pve|zfs' | head -10
echo '=== SERVICES ==='; systemctl is-active pveproxy pvedaemon pvestatd corosync 2>/dev/null
echo '=== VMS ==='; qm list 2>/dev/null
echo '=== CTs ==='; pct list 2>/dev/null
echo '=== VERSION ==='; pveversion; apt list --upgradable 2>/dev/null | head -10
"
```

**Interpretation:** Load < 1.0/core = healthy. Swap ~ 0 = OK. Disk < 80% = healthy. Services: pveproxy/pvedaemon `active`; corosync `inactive` on single-node (normal). Stopped VMs = flag to user.

## Full Audit (Orphaned Resources)

Run when asked about orphans, cleanup, ghosts, stale ISOs.

### Auth Setup

```bash
PVE_TOKEN="PVEAPIToken=<userid>@pve!<tokenid>=<value>"
HOST="https://<proxmox-ip>:8006"
CURL="curl -s --max-time 10 -k -H \"Authorization: ${PVE_TOKEN}\""
```

### Scan Sequence

**1. Cluster Resource Overview:**
```bash
${CURL} "${HOST}/api2/json/cluster/resources?type=vm"
```
Look for: `status: "unknown"` (ghosts), missing `"name"` field, multiple stopped VMs.

**2. Verify Ghosts:**
```bash
${CURL} "${HOST}/api2/json/nodes/pve1/lxc/<VMID>/config"
# Returns 404 "does not exist" = confirmed ghost
```

**3. Storage Content:**
```bash
${CURL} "${HOST}/api2/json/nodes/pve1/storage/local/content"    # ISOs + templates
${CURL} "${HOST}/api2/json/nodes/pve1/storage/local-lvm/content"  # VM disks
```

**4. Duplicate ISO Detection:** Group ISOs by distro name — older patch versions can be pruned.

**5. Snapshot Check:**
```bash
${CURL} "${HOST}/api2/json/nodes/pve1/qemu/<VMID>/snapshot"
```
Non-`"current"` entries are user snapshots consuming disk.

**6. Storage Capacity:**
```bash
${CURL} "${HOST}/api2/json/nodes/pve1/storage"
```
`used_fraction` < 0.5 = healthy, 0.5-0.8 = monitor, > 0.8 = warning.

**7. Firewall Check:**
```bash
${CURL} "${HOST}/api2/json/nodes/pve1/firewall/rules"
```
Empty array = host-wide open.

## Cleanup Operations

### Remove a Ghost CT
```bash
# API (may return "not implemented" for config-less phantoms):
${CURL} -X DELETE -k -H "Authorization: ${PVE_TOKEN}" "${HOST}/api2/json/cluster/config/lxc/<VMID>"

# From root@pam shell (reliable):
pvesh delete /cluster/config/lxc/<VMID>
pct destroy <VMID> --purge
```
**Ghost limitation:** API token can't always remove ghosts. Service restart (`pveproxy`, `pve-cluster`) won't clear stale cluster resource entries. Requires root@pam shell.

### Remove Stale ISO
```bash
${CURL} -X DELETE -k -H "Authorization: ${PVE_TOKEN}" \
  "${HOST}/api2/json/nodes/pve1/storage/local/content/local:iso/<filename>"
```

### Remove Unattached Disk (⚠️ DANGEROUS — confirm twice)
```bash
${CURL} -X DELETE -k -H "Authorization: ${PVE_TOKEN}" \
  "${HOST}/api2/json/nodes/pve1/storage/local-lvm/content/local-lvm:vm-<VMID>-disk-<N>"
```

## VM Diagnostics — Running but Unreachable

A VM showing `status: running` but not responding on network. Common causes:

| Cause | Diagnosis | Fix |
|-------|-----------|-----|
| No OS installed | `blkid /dev/mapper/pve-vm--*--0p*` shows partitions but no FSTYPE | Attach install ISO |
| Missing QEMU guest agent | `qm guest cmd <VMID> network-get-interfaces` returns error | Install qemu-guest-agent |
| Network not configured | `ip neigh` shows no MAC in ARP table | Configure NIC inside VM |
| No serial console | `qm terminal <VMID>` returns "unable to find serial console" | Add serial console device |

### Host-Side Disk Mounting (Injection)

When SSH is impossible, mount the VM's disk from Proxmox host:

```bash
# 1. Stop the VM
qm stop <VMID>

# 2. Activate partitions
kpartx -a /dev/mapper/pve-vm--<VMID>--disk--0
ls -la /dev/mapper/pve-vm--<VMID>--disk--0p*

# 3. Identify root FS
blkid /dev/mapper/pve-vm--<VMID>--disk--0p*

# 4a. Mount ext4/xfs
mount /dev/mapper/pve-vm--<VMID>--disk--0p<N> /mnt/vm<VMID>

# 4b. Mount btrfs (Fedora) — needs subvol specification
mount -o subvol=root /dev/mapper/pve-vm--<VMID>--disk--0p3 /mnt/vm<VMID>

# 5. Modify files (e.g., inject SSH key)
mkdir -p /mnt/vm<VMID>/home/<user>/.ssh
cat ~/.ssh/<key>.pub >> /mnt/vm<VMID>/home/<user>/.ssh/authorized_keys

# 6. SELinux (Fedora/RHEV): `restorecon` from host won't work on foreign mount.
# User must run inside VM after boot: `sudo restorecon -R ~/.ssh`

# 7. Unmount and restart
umount /mnt/vm<VMID>
kpartx -d /dev/mapper/pve-vm--<VMID>--disk--0
qm start <VMID>
```

## Repository Management (No-Subscription)

Stock Proxmox includes enterprise repos that return 401 without subscription.

```bash
# Check repo files (both .list and .sources formats)
ls /etc/apt/sources.list.d/

# .list files — comment the deb line
sed -i 's/^deb/#deb/' /etc/apt/sources.list.d/pve-enterprise.list

# .sources files (deb822 format) — REMOVE, don't comment
rm /etc/apt/sources.list.d/ceph.sources /etc/apt/sources.list.d/pve-enterprise.sources

# Fix pve-no-subscription typo or misplaced component
sed -i 's/pve-no-subscrxiption/pve-no-subscription/' /etc/apt/sources.list
sed -i 's/ pve-no-subscription//g' /etc/apt/sources.list  # remove from wrong lines
# Then add back ONLY on the Proxmox repo line
```

## Upgrade Safety

Running `apt dist-upgrade` on Proxmox is safe while VMs are running — SSH session survives service restarts. However:
- ⚠️ System MAY auto-reboot after dist-upgrade — verify with `uname -r` before/after
- New kernel doesn't take effect until reboot

## Report Format

```
## 🧹 Proxmox Audit — Results

### ✅ Healthy
- VM 102 (HomeAssistant) — running, 32GB
- LXC 200 (web) — running, 4GB

### ⚠️ Orphans Found
- lxc/103 — ghost (config missing, no disk)

### 📦 Storage
- local: 17 items, 25.5 GB (ISOs + templates)
- local-lvm: 15% used (131 GB / 876 GB)

### 💡 Suggested Cleanup
- Remove ghost CT 103
- Remove ubuntu-24.04.1 (superseded by 24.04.4) → saves ~6 GB
```

## Key Pitfalls

1. Ghost CTs can't always be removed via API token — `DELETE /cluster/config/lxc/<VMID>` may return "not implemented". Fix from root@pam shell: `pvesh delete /cluster/config/lxc/<VMID>` or `pct destroy <VMID> --purge`
2. `local-lvm` content uses `rootdir` for LXC and `images` for QEMU — both are content types, not separate storage pools
3. `cluster/resources` may show `type: "lxc"` with `status: "unknown"` even after config file was manually removed
4. Token permission issues — re-create with `pveum acl modify / -user <user>@pve -role Administrator` if API returns empty data
5. Always confirm deletions (ISOs, templates, unattached disks) with user — except confirmed ghosts with no recoverable data
6. Snapshot names: always includes `"current"` entry — that's not a user snapshot
7. Verify before asserting system state — always check `uname -r` after upgrade before saying "no reboot happened"
