# Second Proxmox Node — Discovery and Setup (Session 2026-05-29)

## Discovery

Brought online after a power cut. Found by scanning for port 8006:

```bash
for ip in $(seq 1 254); do
  timeout 1 bash -c "echo >/dev/tcp/192.168.1.$ip/8006" 2>/dev/null && echo "192.168.1.$ip"
done
```

Result: **192.168.1.5** (both ports 22 and 8006 open)

## Node Details

- **IP:** 192.168.1.5
- **Hostname:** `pve` (default Proxmox node name)
- **Node name in API:** `pve` (node1 is `pve1`)
- **Ports:** 22 (SSH), 8006 (Proxmox web UI + API)
- **Hardware:** Same rack, different hardware from node1
- **Status:** Brought online, needs updating and validation

## Access

- SSH key from Hermes host was **not** accepted (Permission denied)
- API token from node1 (`hermes2@pve`) does **not** work cross-node pre-cluster
- Requires root password or SSH key deployment

## Next Steps (Pending)

- [ ] System update (`apt update && apt dist-upgrade`)
- [ ] Validate hardware (CPU, RAM, disks)
- [ ] Check network connectivity between node1 (192.168.1.6) and node2 (192.168.1.5)
- [ ] Verify readiness to cluster

## VMs on Node2

None discovered yet — the node was just brought online with no VMs migrated/created.
