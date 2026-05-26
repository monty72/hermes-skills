---
name: proxmox-health-audit
description: "Audit Proxmox VE for orphaned resources — ghost VMs/CTs, unattached disks, stale snapshots, redundant ISOs, storage capacity issues, and cluster resource anomalies. Covers detection, cleanup, and preventative housekeeping."
version: 1.0.0
author: Hermes Agent
---

# Proxmox Health Audit

Use this skill when asked to **check Proxmox for problems, orphans, or cleanup opportunities**. Covers:

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
