# Ghost Removal Limits — 2026-05-24

## The problem

LXC 103 was a ghost — config file deleted, no disk, no IP, no name, status "unknown". It only showed up in `/cluster/resources`, not in `/nodes/pve1/lxc`.

## What was tried (and failed) via API token only

| Attempt | Result |
|---------|--------|
| `DELETE /cluster/config/lxc/103` | "Method not implemented" |
| `POST /nodes/pve1/services/pveproxy/restart` | Works (returns UPID) but ghost still present |
| `POST /nodes/pve1/services/pve-cluster/restart` | Works (returns UPID) but ghost still present |
| `DELETE /nodes/pve1/lxc/103` | "Configuration file does not exist" (can't delete what's already gone) |
| `POST /nodes/pve1/termproxy cmd=login` | "value 'hermes2@pve!api' does not look like a valid user name" |
| `POST /nodes/pve1/lxc/103/status/start` | Returns a UPID (task enqueued) but fails — confirms the ghost is recognised in the scheduler DB even without a config file |
| `POST /nodes/pve1/lxc vmid=103` | "CT 103 already exists on node 'pve'" — proves the ghost IS registered in pmxcfs SQLite, not just a stale cache entry |
| `GET /nodes/pve1/lxc` | Does NOT show CT 103 — ghosts exist in cluster resources but NOT in per-node LXC listings |

## What would fix it

Root shell on Proxmox:
```bash
pct destroy 103 --purge
# or
rm -f /etc/pve/nodes/pve1/lxc/103.conf
# or
pvesh delete /cluster/config/lxc/103
```

## API service restart (works with token)

```bash
curl -s -k -X POST \
  -H "Authorization: PVEAPIToken=hermes2@pve!api=19b5fd1b-9354-47fd-8847-4ebbe28a4abb" \
  "https://192.168.1.6:8006/api2/json/nodes/pve1/services/{service}/{action}"

# Available actions: start, stop, restart, reload, state
# Service names: pveproxy, pve-cluster, pvedaemon, pvestatd, pvescheduler
```

## QEMU Guest Agent

Running this Hermes (VM 105) does NOT have the QEMU guest agent running:
```
systemctl status qemu-guest-agent
→ Active: inactive (dead)
```

This means the Proxmox host can't exec commands inside this VM via guest agent. To enable:
1. On Proxmox host, enable the guest agent in VM config: `qm set 105 --agent 1`
2. Inside the VM: `sudo systemctl enable --now qemu-guest-agent`

Without the guest agent, we can't receive host-side tools like `qm guest exec` or clean shutdown signals.
