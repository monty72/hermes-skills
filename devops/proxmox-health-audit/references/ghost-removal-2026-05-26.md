# Ghost VT Fix Attempts — 2026-05-26 session

## The problem

LXC 103 was a ghost — config file deleted, no disk, no IP, no name, status "unknown". Appeared only in `/cluster/resources`, not in `/nodes/pve1/lxc`.

## What was tried (via API token)

| Attempt | Result |
|---------|--------|
| `DELETE /cluster/config/lxc/103` | "Method not implemented" |
| `POST /nodes/pve1/services/pveproxy/restart` | Works but ghost persists |
| `POST /nodes/pve1/services/pve-cluster/restart` | Works but ghost persists |
| `DELETE /nodes/pve1/lxc/103` | "Config file does not exist" |
| `POST /nodes/pve1/lxc/103/status/start` | returns UPID but silently fails |
| `POST /nodes/pve1/lxc vmid=103&ostemplate=...` | "CT 103 already exists on node 'pve'" — proves ghost IS in the pmxcfs SQLite DB |
| `termproxy cmd=login` | "hermes2@pve!api does not look like a valid user name" — API token users can't use the web terminal |

## Root cause

The ghost CT's config file (`/etc/pve/nodes/pve1/lxc/103.conf`) was deleted manually (or by `pct destroy` that completed partially) but the pmxcfs SQLite database still has a row for VMID 103 in its cluster resource table. Service restarts don't rebuild this table — the entry is persistent.

## Fix

Requires root shell on Proxmox host:
```bash
pvesh delete /cluster/config/lxc/103
# or
rm -f /etc/pve/nodes/pve1/lxc/103.conf
# or
pct destroy 103 --purge
```
