---
name: proxmox-ve
description: "Full lifecycle management for Proxmox VE hypervisors — provisioning VMs and LXC containers (cloud-image, template-based), cluster creation, health auditing, orphan cleanup, SSH bootstrapping, upgrade management, and power-outage recovery."
category: devops
tags: [proxmox, ve, hypervisor, lxc, qemu, cluster, auditing, provisioning]
---

# Proxmox VE — Full Lifecycle Management

## Overview

This umbrella skill covers the complete Proxmox VE lifecycle: provisioning VMs/LXCs, managing the cluster, auditing health, cleaning up orphans, upgrading nodes, and recovering from power outages. It consolidates two formerly separate skills: `proxmox-host-creation` (provisioning, cluster, lifecycle) and `proxmox-health-audit` (health checks, orphan detection, cleanup).

## Sections at a Glance

| Section | Reference File | Covers |
|---------|---------------|--------|
| 1. Authentication & API Setup | `references/provisioning-and-lifecycle.md#authentication` | API tokens, password fallback, token management |
| 2. Provisioning — LXC Containers | `references/provisioning-and-lifecycle.md#creating-an-lxc-container` | Creating from templates, VM lifecycle, SSH bootstrapping |
| 3. Provisioning — Cloud-Image VMs | `references/provisioning-and-lifecycle.md#creating-a-vm-from-a-cloud-image-cloud-init` | Ubuntu, Kali, generic cloud images with cloud-init |
| 4. Provisioning — Hermes Backup Jobs | `references/provisioning-and-lifecycle.md#hermes-backup-setup` | Proxmox vzdump backup jobs via API |
| 5. Cluster Management | `references/provisioning-and-lifecycle.md#cluster-creation-multi-node` | Cluster creation, node joining, heterogeneous hardware |
| 6. PVE Upgrades | `references/provisioning-and-lifecycle.md#pve-89-major-upgrade-debian-12--13` | PVE 8→9, conffile handling, GRUB fixes |
| 7. Power-Outage Recovery | `references/provisioning-and-lifecycle.md#post-power-outage-recovery` | DHCP drift, service restart, static IP pinning |
| 8. VM/CT Configuration Changes | `references/provisioning-and-lifecycle.md#modifying-running-vm-config-ram-cpu-etc` | RAM/CPU changes, snapshot policy |
| 9. Quick Health Check | `references/health-audit-and-cleanup.md#quick-health-check` | System status, resources, VM state, services |
| 10. Full Audit — Orphans & Cleanup | `references/health-audit-and-cleanup.md#full-audit-for-orphaned-resources` | Ghost VMs/CTs, unattached disks, stale ISOs, snapshot sprawl |
| 11. Ghost Removal & Stale Resource Cleanup | `references/health-audit-and-cleanup.md#cleanup-operations` | CT/phost removal, ISO pruning, unattached disk deletion |
| 12. VM Diagnostics — Unreachable VMs | `references/health-audit-and-cleanup.md#vm-diagnostics--running-but-unreachable` | No OS, missing guest agent, network not configured |
| 13. Repository Management | `references/health-audit-and-cleanup.md#repository-management-no-subscription` | Disabling enterprise repos, deb822 format handling |

## Quick Reference — Authentication

```bash
# API token (preferred)
Authorization: PVEAPIToken=<userid>@<realm>!<tokenid>=<token-value>

# User/password (fallback, pre-cluster)
curl -sk -X POST 'https://<host>:8006/api2/json/access/ticket' \
  --data-urlencode 'username=root@pam' \
  --data-urlencode 'password=<password>'
```

**API token creation** (run on Proxmox shell):
```bash
pveum user add <name>@pve
pveum acl modify / -user <name>@pve -role Administrator
pveum user token add <name>@pve api --privsep 0
```

**Curl shorthand:**
```bash
TOKEN="PVEAPIToken=hermes2@pve!api=..."
HOST="https://192.168.1.6:8006"
CURL="curl -sk -H 'Authorization: ${TOKEN}'"
```

## Quick Reference — Health Check (Fast Path)

```bash
ssh root@<proxmox-ip> "
echo '=== SYSTEM ==='; uptime -p
echo '=== CPU ==='; nproc; cat /proc/loadavg
echo '=== MEMORY ==='; free -h
echo '=== DISK ==='; df -h | grep -E '^/dev|pve|zfs' | head -10
echo '=== SERVICES ==='; systemctl is-active pveproxy pvedaemon corosync 2>/dev/null
echo '=== VMs ==='; qm list 2>/dev/null
echo '=== CTs ==='; pct list 2>/dev/null
echo '=== VERSION ==='; pveversion; apt list --upgradable 2>/dev/null | head -10
"
```

**Interpretation:** Load < 1.0/core = healthy. Swap ~ 0 = no memory pressure. Disk < 80% = healthy. Services: pveproxy/pvedaemon should be `active`; corosync `inactive` on single-node (normal). Stopped VMs = flag to user. Pending upgrades safe to run without reboot (except kernel changes).

## Key Rules (from experience)

- **Snapshot before destructive changes** — always take a Proxmox snapshot before RAM/CPU/disk/OS changes, following the naming convention `pre-<description-of-change>`
- **API tokens only work within a cluster** — pre-cluster nodes need root password auth
- **Ghost containers (status: unknown, no config)** cannot be removed via the API — requires `pvesh delete /cluster/config/lxc/<VMID>` from root@pam shell
- **`onboot` cluster cache is stale** — always verify via the direct VM config endpoint, not cluster/resources
- **`--sshkeys` takes key content, not a file path** — use process substitution: `--sshkeys <(echo 'ssh-ed25519 AAAA...')`
- **Cloud-init drive needs `local-lvm` storage** — `local` doesn't support content type 'images'
- **Stopping pve-cluster breaks all access** (API, web UI, SSH key auth) — recovery requires password SSH or console
- **`pvecm add` stale lock** — remove `/var/lock/pvecm.lock` before retrying failed joins

## Scripts

- `scripts/provision-web-container.sh` — Full LXC provisioning script from the absorbed `proxmox-host-creation` skill
