---
name: proxmox-health-audit
description: "Audit Proxmox VE for orphaned resources — ghost VMs/CTs, unattached disks, stale snapshots, redundant ISOs, storage capacity issues, and cluster resource anomalies. Covers detection, cleanup, and preventative housekeeping."
version: 1.0.0
author: Hermes Agent
---

# Proxmox Health Audit

Use this skill when asked to **check Proxmox for general health, problems, orphans, or cleanup opportunities**. Start with a quick health check, then dive into the full audit if problems are found.

## Quick Health Check

Run this first for any "health check" or "how's it looking" request. It covers system status, resources, VM state, and services — no API token needed if you have root SSH access.

```bash
ssh root@<proxmox-ip> "
echo '=== SYSTEM ==='
echo 'Uptime:'; uptime -p
echo '=== CPU ==='
echo 'Cores:'; nproc
echo 'Load:'; cat /proc/loadavg
echo '=== MEMORY ==='
free -h
echo '=== DISK ==='
df -h | grep -E '^/dev|pve|zfs' | head -10
echo '=== SERVICES ==='
systemctl is-active pveproxy pvedaemon pvestatd corosync 2>/dev/null
echo '=== VMs ==='
qm list 2>/dev/null
echo '=== CONTAINERS ==='
pct list 2>/dev/null
echo '=== UPDATES ==='
pveversion
echo '--- pending ---'
apt list --upgradable 2>/dev/null | head -10
echo '=== ZFS (if any) ==='
zpool list 2>/dev/null || echo 'No ZFS pools'
```

**Interpreting results:**
- **Load < 1.0 per core** → healthy (load 0.23 on 16 cores = very idle)
- **Swap used ≈ 0** → no memory pressure
- **Disk < 80%** → healthy
- **Services:** pveproxy, pvedaemon, pvestatd should all be `active`; corosync is `inactive` on single-node setups (normal)
- **Stopped VMs/CTs** → flag to user, ask if they can be pruned or started
- **Pending upgrades** → safe to run without disconnecting SSH or VMs (only a reboot takes effect, and only for new kernels)

### SSH Key Setup for Proxmox

If you need SSH access to Proxmox but don't have it yet:

```bash
# Show the public key
cat ~/.ssh/<keyname>.pub

# User pastes this into Proxmox root shell:
# echo '<pubkey>' >> ~/.ssh/authorized_keys
```

The key must go to `root@<proxmox-ip>`. Standard SSH hardening applies: `.ssh/` should be 700, `authorized_keys` should be 600.

## VM Diagnostics — Running But Unreachable

A VM may show `status: running` in `qm list` but not respond on the network. Common causes:

**1. No OS installed (disk is partitioned but empty)**
```bash
# Check disk contents
fdisk -l /dev/pve/vm-<VMID>-disk-0 2>/dev/null
blkid /dev/mapper/pve-vm--<VMID>--disk--0-part* 2>/dev/null
```
If `blkid` shows partitions but **no FSTYPE** on any of them, no filesystem exists — the disk was partitioned but never formatted. The VM needs an OS install ISO attached.

**Important:** `blkid` will only show partitions after `kpartx -a /dev/mapper/pve-vm--<VMID>--disk--0` is run. Without kpartx, the partition device nodes don't exist.

---

## VM Disk Recovery — Host-Side Mounting

When a VM is running but unreachable (SSH refused, no network), you can mount its disk from the Proxmox host and modify files directly. This is useful for:

- Injecting SSH keys when key-based auth isn't set up
- Fixing SSH config (`sshd_config`, firewall, SELinux)
- Reading logs to diagnose boot failures
- Fixing configuration files that prevent network boot

### Prerequisites

- Root SSH access to the Proxmox host
- The VM must be **stopped** (btrfs/zfs won't allow concurrent host+guest mount)
- The VM uses LVM-based storage (common default)

### Step-by-Step

**1. Stop the VM (if running)**

```bash
qm stop <VMID>
# Wait for "status: stopped"
qm status <VMID>
```

**2. Find and activate the disk partitions**

```bash
# The disk appears as an LVM logical volume
ls -la /dev/pve/vm-<VMID>-disk-0

# Activate partition mappings with kpartx
kpartx -a /dev/mapper/pve-vm--<VMID>--disk--0

# Verify partitions appeared
ls -la /dev/mapper/pve-vm--<VMID>--disk--0p*
# Should show p1, p2, p3...
```

**3. Identify the root filesystem**

```bash
blkid /dev/mapper/pve-vm--<VMID>--disk--0p*
# Look for:
#   TYPE="ext4" — standard Linux root
#   TYPE="btrfs" — Fedora/openSUSE (uses subvolumes)
#   TYPE="xfs" — RHEL/CentOS
```

**4a. Mount ext4/xfs**

```bash
mkdir -p /mnt/vm<VMID>
mount /dev/mapper/pve-vm--<VMID>--disk--0p<N> /mnt/vm<VMID>
# (N is the root partition number, usually p2 for ext4, p3 for btrfs)
```

**4b. Mount btrfs (Fedora, openSUSE)**

btrfs uses subvolumes. Mount the correct one:

```bash
# First mount the top-level to see subvolumes:
mount /dev/mapper/pve-vm--<VMID>--disk--0p3 /mnt/vm<VMID>
btrfs subvolume list /mnt/vm<VMID>
# Typical Fedora layout:
#   ID 256 ... path home
#   ID 257 ... path root
#   ID 258 ... path root/var/lib/portables

# Unmount and remount with the correct subvol:
umount /mnt/vm<VMID>
mount -o subvol=root /dev/mapper/pve-vm--<VMID>--disk--0p3 /mnt/vm<VMID>

# Now /mnt/vm<VMID> shows the full filesystem (etc, home, usr, var...)
```

**5. Modify files**

```bash
# Inject SSH public key
mkdir -p /mnt/vm<VMID>/home/<user>/.ssh
cat ~/.ssh/<keyfile>.pub >> /mnt/vm<VMID>/home/<user>/.ssh/authorized_keys
chmod 700 /mnt/vm<VMID>/home/<user>/.ssh
chmod 600 /mnt/vm<VMID>/home/<user>/.ssh/authorized_keys
chown -R <UID>:<GID> /mnt/vm<VMID>/home/<user>/.ssh
# (Find the UID from /mnt/vm<VMID>/etc/passwd)
```

**6. Fix SELinux context (Fedora/RHEL)**

**This is the critical step for Fedora VMs.** The SSH key file created from the host has no SELinux context (shows `?` in `ls -laZ`). Without the right context, `sshd` will ignore the key file.

```bash
# On the Proxmox host, this won't work because the foreign FS can't be relabeled:
restorecon -R /mnt/vm<VMID>/home/<user>/.ssh    # ❌ Fails silently or can't apply
chcon -R -t ssh_home_t /mnt/vm<VMID>/home/<user>/.ssh  # ❌ "can't apply partial context"

# The mount is a foreign btrfs — SELinux labels can't be applied from the host.
# Instead, note the issue and handle it inside the VM after boot:
```

**Post-boot fix (user runs on VM console after logging in):**

```bash
sudo restorecon -R ~/.ssh
sudo systemctl restart sshd
```

If the user can log in at the physical/VM console, this one command fixes SSH key auth. After that, SSH key login works immediately.

**7. Unmount and restart**

```bash
umount /mnt/vm<VMID>
kpartx -d /dev/mapper/pve-vm--<VMID>--disk--0
qm start <VMID>
```

### Problem: SELinux on Mounted VM Disks

When editing files on a VM's root filesystem from the Proxmox host, SELinux presents a specific challenge:

| Operation | Host-side result | Fix |
|-----------|-----------------|-----|
| Read files | ✅ Works fine | — |
| Write files | ✅ File content works | — |
| Set SELinux context | ❌ **Can't** — foreign filesystem |
| `chcon` | ❌ `can't apply partial context to unlabeled file` | |
| `restorecon` | ❌ needs mounted /etc/selinux/targeted/contexts | |
| `setfattr -n security.selinux` | ❌ not supported on foreign mount | |

**The only reliable fix:** Let the user log in at the VM console and run `sudo restorecon -R ~/.ssh` from inside the VM.

**Alternative if you can mount the Fedora live ISO:** Boot the VM from a live ISO, mount the root, and run `chroot /mnt restorecon -R /home/<user>/.ssh`. But this requires detaching/resizing the CDROM and is more work than just asking the user.

### Common File Modifications (Host-Side)

| Task | Command |
|------|---------|
| Inject SSH key | `cat key.pub >> /mnt/vm*/home/*/.ssh/authorized_keys` |
| Read boot log | `cat /mnt/vm*/var/log/boot.log` (after boot failed) |
| Check OS version | `cat /mnt/vm*/etc/os-release` |
| Check user UID | `grep <user> /mnt/vm*/etc/passwd` |
| Enable SSH service | `ln -sf /lib/systemd/system/ssh.service /mnt/vm*/etc/systemd/system/multi-user.target.wants/` (or edit presets) |
| Fix sshd_config | Edit `/mnt/vm*/etc/ssh/sshd_config` — check `PubkeyAuthentication`, `PasswordAuthentication`, `AllowUsers` |

**2. QEMU guest agent missing**
```bash
qm guest cmd <VMID> network-get-interfaces 2>&1
# Returns "No QEMU guest agent configured" — guest agent isn't installed
```
Without the guest agent, Proxmox can't report the VM's IP. Find it via ARP/DHCP or check console.

**3. Network not configured in guest OS**
```bash
# Check ARP for the VM's MAC address (get MAC from qm config <VMID>)
ip neigh | grep -i '<mac-addr>'
# If not present, the guest isn't sending ARP probes — no IP configured
```
The Proxmox config may define `net0: virtio=BC:24:11:...` but the guest OS needs its own network setup.

**4. No serial console**
```bash
qm terminal <VMID> 2>&1
# Returns "unable to find a serial console"
```

**Diagnostic workflow:**
```bash
# Step 1: Status
qm status <VMID>
# Step 2: Disk filesystems
blkid /dev/mapper/pve-vm--<VMID>--disk--0-part* 2>/dev/null
# Step 3: Network visibility
ip neigh | grep -i '<mac-addr>'
# Step 4: Guest agent
qm guest cmd <VMID> network-get-interfaces 2>&1
```

Then report findings and suggest next steps (attach ISO, install OS, configure network).

### Upgrade Safety

Running `apt dist-upgrade` on Proxmox is safe while VMs are running:
- The SSH session survives service restarts (pveproxy, pvedaemon)
- VMs keep running through the upgrade
- Even a new kernel install won't take effect until a reboot
- **⚠️ But the system MAY auto-reboot after the dist-upgrade** — always verify: `uname -r` before and after. Don't assert "no reboot happened" without checking.
- A reboot will take down all VMs — schedule for a maintenance window

### Repository Management (No-Subscription)

Fresh/stock Proxmox installs include enterprise repositories (`enterprise.proxmox.com`) that return **401 Unauthorized** without a paid subscription. Disable them to get clean `apt update` runs:

**Check what repo files exist:**
```bash
ls /etc/apt/sources.list.d/
# May show both .list AND .sources files (deb822 format)
```

**Two formats to handle:**

1. **`.list` files** (legacy one-line format) — comment the `deb` line:
   ```
   # deb https://enterprise.proxmox.com/debian/pve trixie pve-enterprise
   ```

2. **`.sources` files** (deb822 newer format) — these must be **removed**, not commented:
   ```bash
   # ❌ Don't comment the URIs: line in deb822 format — it creates "Malformed entry" errors:
   #   sed 's/^URIs: https:\/\/enterprise/.../'   ← BREAKS apt, can't parse the file
   # ✅ Remove the .sources files entirely if .list equivalents exist:
   rm /etc/apt/sources.list.d/ceph.sources /etc/apt/sources.list.d/pve-enterprise.sources
   ```

   To detect deb822 files before removing them:
   ```bash
   cat /etc/apt/sources.list.d/*.sources 2>/dev/null
   # Format looks like:
   #   Types: deb
   #   URIs: https://enterprise.proxmox.com/debian/pve
   #   Suites: trixie
   #   Components: pve-enterprise
   ```

The no-subscription repos at `download.proxmox.com` should already be configured and work without auth.

**Fix the `pve-no-subscription` component warnings:**

Stock installs often add `pve-no-subscription` as a component to **Debian repos** in `/etc/apt/sources.list`, causing `"component misspelt"` warnings (Debian repos don't have that component). Also watch for the common typo `pve-no-subscrxiption`.

```bash
# Step 1: Check current state
cat -n /etc/apt/sources.list

# Step 2: Check for typo in component name
grep -n 'subscrxiption\|subscriotion\|subscrption' /etc/apt/sources.list

# Step 3: Fix typo if found (replace mispelling with correct component name)
sed -i 's/pve-no-subscrxiption/pve-no-subscription/' /etc/apt/sources.list

# Step 4: Remove pve-no-subscription from Debian repos
# The component is only valid for Proxmox repos, not Debian repos.
# Remove it globally first:
sed -i 's/ pve-no-subscription//g' /etc/apt/sources.list

# Step 5: Add it back ONLY on the Proxmox repo line (usually line 8):
#   deb http://download.proxmox.com/debian/pve trixie pve-no-subscription
# Find the Proxmox line number first:
grep -n 'download.proxmox.com' /etc/apt/sources.list
# Then add the component back (adjust line number as needed):
LINENUM=$(grep -n 'download.proxmox.com' /etc/apt/sources.list | cut -d: -f1)
sed -i "${LINENUM}s|deb http://download.proxmox.com/debian/pve trixie$|deb http://download.proxmox.com/debian/pve trixie pve-no-subscription|" /etc/apt/sources.list
```

**Verify clean update:**
```bash
apt update 2>&1 | grep -E '^(Hit|Get|Err:|All|Reading)'
# Should show no errors. Cosmetic warnings about missing Component are harmless.
```

---

## Full Audit (for orphaned resources)

After the quick check, or when specifically asked about **orphans, cleanup, ghosts, stale ISOs, unattached disks**, do the full audit below.

Covers:

- Finding ghost/phantom VMs and CTs (config missing but cluster resource entry exists)
- Detecting unattached or oversized disks (no VM/CT matching a volume)
- Auditing ISO/template storage for redundancy (duplicate distro versions)
- Checking snapshot sprawl
- Summarising storage utilisation and reclaimable space
- Cleaning up confirmed orphans

**Inverse of** `proxmox-host-creation` — that skill *creates* resources; this skill *inspects and prunes* them.

---

## Authentication

Use the same API token approach as `proxmox-host-creation`:

```bash
PVE_TOKEN="PVEAPIToken=<userid>@pve!<tokenid>=<value>"
HOST="https://<proxmox-ip>:8006"
CURL="curl -s --max-time 10 -k -H \"Authorization: ${PVE_TOKEN}\""
```

If no token is known, check:
- `~/.hermes/memories/MEMORY.md` — often stored there from previous provisioning sessions
- Proxmox root shell: `pveum user token list <user>@pve`

---

## Scan Sequence (do in this order)

### 1. Cluster Resource Overview

Start here — get the full picture:

```bash
${CURL} "${HOST}/api2/json/cluster/resources?type=vm"
```

Look for:
- **VMs/CTs with `"status": "unknown"`** — these are ghosts. No config file exists.
- **VMs/CTs with no `"name"` field** or `"name": "?"` — orphan indicators.
- **Multiple stopped VMs** — ask the user if they can be cleaned up.

### 2. Verify Ghosts

For any entry with `"type": "lxc"` and `"status": "unknown"`:

```bash
# Check if config file exists
${CURL} "${HOST}/api2/json/nodes/pve1/lxc/<VMID>/config"
# Returns 404 / "Configuration file does not exist" — confirmed ghost

# Also check qemu (for type=qemu or unknown type)
${CURL} "${HOST}/api2/json/nodes/pve1/qemu/<VMID>/config"
```

**Ghost detection rule:** If the config endpoint returns `"Configuration file 'nodes/pve1/lxc/<VMID>.conf' does not exist"`, the entry is a phantom — orphaned from a deleted container whose config was removed but whose cluster resource record wasn't purged.

### 3. Storage Content (full inventory)

List ALL items on each storage pool:

```bash
# ISO/template/backup storage (usually 'local')
${CURL} "${HOST}/api2/json/nodes/pve1/storage/local/content"

# VM disk storage (usually 'local-lvm')
${CURL} "${HOST}/api2/json/nodes/pve1/storage/local-lvm/content"
```

For `local` storage, classify by `content` field:
- `iso` — ISO installers
- `vztmpl` — LXC container templates
- `backup` — vzdump backups
- `snippets` — custom scripts

For `local-lvm` storage, check that every `vmid` matches an existing VM/CT. Disks with a `vmid` that doesn't appear in the `cluster/resources` output are unattached.

### 4. Duplicate ISO Detection

Group ISOs by distro name (e.g. `ubuntu-24.04.1` vs `ubuntu-24.04.4`, `debian-13.5.0` vs `debian-bookworm`). Older versions can be pruned if the newer one is present and the user doesn't need the older one for compatibility testing.

### 5. Snapshot Check

Check each running/stopped VM for user-created snapshots:

```bash
# For QEMU VMs
${CURL} "${HOST}/api2/json/nodes/pve1/qemu/<VMID>/snapshot"

# For LXC containers
${CURL} "${HOST}/api2/json/nodes/pve1/lxc/<VMID>/snapshot"
```

Default snapshots have `"name": "current"` — that's the live state, not a saved snapshot. Any other name is a user snapshot.

### 6. Storage Capacity Audit

```bash
${CURL} "${HOST}/api2/json/nodes/pve1/storage"
```

Parse the `used_fraction` field:
- `< 0.5` — healthy
- `0.5 - 0.8` — monitor
- `> 0.8` — warning, stale ISOs/templates should be pruned

Also check `swap.free` and `memory.free` from node status:

```bash
${CURL} "${HOST}/api2/json/nodes/pve1/status"
```

### 7. Firewall Check

```bash
${CURL} "${HOST}/api2/json/nodes/pve1/firewall/rules"
```

Empty array = no firewall rules (host-wide open). Flag to the user if they expect strict firewall.

---

## Cleanup Operations

### Remove a Ghost/Phantom CT

```bash
${CURL} -X DELETE -k \
  -H "Authorization: ${PVE_TOKEN}" \
  "${HOST}/api2/json/cluster/config/lxc/<VMID>"
```

If that doesn't work, try via Proxmox shell:

```bash
# On the Proxmox host
pct destroy <VMID> --purge
```

### Remove a Stale ISO

```bash
${CURL} -X DELETE -k \
  -H "Authorization: ${PVE_TOKEN}" \
  "${HOST}/api2/json/nodes/pve1/storage/local/content/local:iso/<filename>"
```

Filter to only ISOs that are truly stale (superseded versions, unlabeled downloads). Always confirm with user before deleting.

### Remove an Unattached Disk (local-lvm)

⚠️ **DANGEROUS** — confirm twice. An unattached disk may contain data from a deleted VM that the user wants to recover.

```bash
${CURL} -X DELETE -k \
  -H "Authorization: ${PVE_TOKEN}" \
  "${HOST}/api2/json/nodes/pve1/storage/local-lvm/content/local-lvm:vm-<VMID>-disk-<N>"
```

### Remove a Stale CT Template

```bash
${CURL} -X DELETE -k \
  -H "Authorization: ${PVE_TOKEN}" \
  "${HOST}/api2/json/nodes/pve1/storage/local/content/local:vztmpl/<filename>"
```

---

## Report Format

Deliver results in this structure when summarising to the user:

```
## 🧹 Proxmox Audit — Results

### ✅ Healthy
- VM 102 (HomeAssistant) — running, 32GB
- LXC 200 (web) — running, 4GB
- ...

### ⚠️ Orphans Found
- lxc/103 — ghost (config missing, no disk)

### 📦 Storage
- local: 17 items, 25.5 GB (ISOs + templates)
- local-lvm: 15% used (131 GB / 876 GB)

### 💡 Suggested Cleanup
- Remove ghost CT 103 → saves cluster listing clutter
- Remove ubuntu-24.04.1 (superseded by 24.04.4) → saves ~6 GB
- Remove rootfs.tar.xz (unlabeled) → saves 73 MB
```

---

## Pitfalls

1. **Ghost CTs can't always be removed via the API token alone.** The `DELETE /cluster/config/lxc/<VMID>` endpoint returns "not implemented" for phantom entries whose config file is already gone. Restarting `pveproxy` or `pve-cluster` via `POST /nodes/pve1/services/<svc>/restart` does NOT clear these ghosts from the cluster resource cache either. Attempting to create a new CT with the ghost's VMID returns "CT <VMID> already exists on node 'pve'". Attempting to start the ghost returns a UPID (the scheduler enqueues it) but it fails silently. (See `references/ghost-removal-limits.md` for a full trace of what was tried.)

   The fix requires root shell on the Proxmox host:
   ```bash
   # On the Proxmox host — accessible method unless the conf already vanished
   pct destroy <VMID> --purge

   # If config is already deleted but ghost remains, clear directly:
   rm -f /etc/pve/nodes/pve1/lxc/<VMID>.conf
   # or via pvesh:
   pvesh delete /cluster/config/lxc/<VMID>
   ```
   The `termproxy`/`spiceshell` `cmd=login` endpoint won't work for API token users either — it rejects PVE realm users (`value 'hermes2@pve!api' does not look like a valid user name`). Only `root@pam` (or another PAM user) can use the login shell.

2. **Service restart via API works but won't clear ghosts.** Confirmed empirically:
   ```bash
   # This works with API tokens:
   POST /nodes/pve1/services/pveproxy/restart
   POST /nodes/pve1/services/pve-cluster/restart
   # But neither removes stale cluster resource entries
   ```

2. **`local-lvm` content uses `rootdir` for LXC disks and `images` for QEMU disks.** Both are "content type" values, not separate storage pools. LXC root filesystems appear as `rootdir`, VM disks as `images`.

3. **`cluster/resources` may show `"type": "lxc"` entries that have vanished.** If a container was destroyed with `pct destroy` but the config file was manually removed first, the cluster resource entry persists. The API returns `status: "unknown"` and no `name` / `node` beyond the bare ID.

4. **Token permission issues.** If the API returns empty or partial data, the token may lack Administrator role on `/`. Re-create with `pveum acl modify / -user <user>@pve -role Administrator`. Permissions propagate within 1-3 seconds.

5. **Multiple Debian/Ubuntu ISOs.** Users often download multiple minor versions (Debian-12.5, 12.7, 13.5; Ubuntu 24.04.1, 24.04.4). The latest patch version of each major release is all that's needed — older ones are safe to prune.

6. **Always confirm deletions.** Never delete ISOs, templates, or unattached disks without user confirmation. The one exception is a confirmed ghost (no config, no disk, unknown status) — those have no recoverable data.

7. **Snapshot names.** Proxmox always includes a `"current"` entry per VM — this is not a saved snapshot. Only non-`current` names represent saved states that consume disk space.

8. **Verify before asserting system state.** After any state-changing operation (reboot, upgrade, config change), verify the outcome before stating it. A Proxmox dist-upgrade may auto-reboot the host — if you say "no reboot happened" without checking `uname -r`, the user loses trust. Always: check first, then report.
