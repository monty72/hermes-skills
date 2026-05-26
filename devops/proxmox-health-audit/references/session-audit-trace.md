# Session Audit Trace — 2026-05-24

## Setup

Proxmox host: 192.168.1.6 (pve1)
API token: PVEAPIToken=hermes2@pve!api=19b5fd1b-9354-47fd-8847-4ebbe28a4abb

## What was found

- **7 VMs/CTs** total: Win11 (100, stopped), Docker01 (101, LXC stopped), HomeAssistant (102, running), **CT 103 (ghost — no config, no name, unknown status)**, OpenCrawl (104, stopped), Hermes (105, running), web (200, LXC running)
- **2 storage pools**: `local` (dir, 37% used) and `local-lvm` (lvmthin, 15% used)
- **17 items in local storage**: 8 ISOs (24.9 GB), 8 CT templates (607 MB), 1 unlabeled rootfs.tar.xz (73 MB)
- **Snapshots**: none user-created — all VMs only have `current`
- **Duplicate ISOs**: ubuntu-24.04.1 + ubuntu-24.04.4 (both present)
- **Firewall**: no rules (all open)

## How ghost CTs appear in the API

```json
{
  "node": "pve",
  "id": "lxc/103",
  "vmid": 103,
  "status": "unknown",
  "type": "lxc"
}
```

No `name` field, no IP, no disk. Config check returns:
```json
{"message": "Configuration file 'nodes/pve1/lxc/103.conf' does not exist"}

# Also checked qemu side — same result:
{"message": "Configuration file 'nodes/pve1/qemu-server/103.conf' does not exist"}
```

## Commands used during audit

```bash
# Token setup
PVE_TOKEN="PVEAPIToken=hermes2@pve!api=19b5fd1b-9354-47fd-8847-4ebbe28a4abb"
BASE="https://192.168.1.6:8006/api2/json"
CURL="curl -s --max-time 10 -k -H \"Authorization: ${PVE_TOKEN}\""

# Full cluster resource list
${CURL} "${BASE}/cluster/resources?type=vm"

# Storage discovery
${CURL} "${BASE}/storage"
${CURL} "${BASE}/nodes/pve1/storage"

# Storage content (full list)
${CURL} "${BASE}/nodes/pve1/storage/local/content"
${CURL} "${BASE}/nodes/pve1/storage/local-lvm/content"

# Config verification (ghost detection)
${CURL} "${BASE}/nodes/pve1/lxc/103/config"
${CURL} "${BASE}/nodes/pve1/qemu/103/config"

# Snapshot check (for each VMID)
${CURL} "${BASE}/nodes/pve1/qemu/<VMID>/snapshot"
${CURL} "${BASE}/nodes/pve1/lxc/<VMID>/snapshot"

# Node hardware
${CURL} "${BASE}/nodes/pve1/status"
${CURL} "${BASE}/nodes/pve1/disks/list"
${CURL} "${BASE}/nodes/pve1/network"
${CURL} "${BASE}/nodes/pve1/firewall/rules"
```

## Key observations

1. CT 103 had been deleted improperly — config file removed manually before `pct destroy` completed its cleanup. The cluster resource database still held the entry.
2. No `backup` content type items existed on `local` storage — no backup schedule is configured.
3. The `local-lvm` thin pool had no orphaned disks — every `vmid` field matched an existing VM/CT.
4. Docker01 (LXC 101) was a bulkier container (2 CPU, 4GB RAM, 50GB disk) — good candidate for decommission if Docker workloads moved elsewhere.
5. OpenCrawl (VM 104) was provisioned with 8 vCPU and 16GB RAM — oversized relative to the rest of the homelab.

## Update — 2026-05-24: Ghost removal attempt

Tried to remove CT 103 from cluster resources via the API. Failed — the DELETE endpoint returns "not implemented" and service restarts (pveproxy, pve-cluster) don't clear the stale entry. The `termproxy` login endpoint rejects API token users. Root shell on the Proxmox host is required.

### Cleanup performed

| Item | Size | Reason |
|------|------|--------|
| `ubuntu-24.04.1-desktop-amd64.iso` | 5.9 GB | Superseded by 24.04.4 |
| `Fedora-Everything-netinst-x86_64-39-1.5.iso` | 686 MB | Old fedora |
| `kali-linux-2024.4-installer-amd64.iso` | 4 GB | Old version |
| `rootfs.tar.xz` | 73 MB | Unlabeled, probably orphaned |
| **Total freed** | **~14 GB** | |

### Remaining ISOs (all keepers)
- Win11_24H2, debian-13.5.0, debian-bookworm, ubuntu-24.04.4, virtio-win

### Storage after cleanup
- `local`: 13 items remaining
- `local-lvm`: 15% used (131 GB / 876 GB)

