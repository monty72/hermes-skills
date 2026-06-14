# API Token Limitations

The `@pve` realm API token has full access to the Proxmox REST API but CANNOT:

## Shell / System Access

- **Cannot use `termproxy login`** — the terminal proxy (`/nodes/pve1/termproxy?cmd=login`) requires a `@pam` (PAM) user who has a system login on the Proxmox host. API token users (`hermes2@pve!api`) get `"does not look like a valid user name"`.
- **Cannot run `pvesh`, `pct`, `qm` commands** — these are shell-level operations.
- **Cannot modify `/etc/pve/` files directly** — the pmxcfs FUSE filesystem respects the API token's permissions but the file paths are not directly accessible via REST.
- **Cannot start interactive shells** in VMs or containers (VNC/spice proxies).

## Ghost Resource Cleanup

- **Cannot delete a LXC/VM that has no config file** — `DELETE /nodes/pve1/lxc/<VMID>` fails with `"Configuration file does not exist"`.
- **Cannot remove entries from the pmxcfs cluster database** even when the config file is gone. The ghost persists in `cluster/resources` until cleaned via `root@pam` shell with `pvesh delete /cluster/config/lxc/<VMID>`.

## Service Management

The API token CAN restart systemd services on the Proxmox node:

```bash
# Restart pveproxy
curl -s -k -X POST -H "Authorization: PVEAPIToken=..." \
  "https://host:8006/api2/json/nodes/pve1/services/pveproxy/restart"

# Available endpoints: /nodes/<node>/services/<service>/{start,stop,restart,reload}
```

Available methods per service: `state`, `start`, `stop`, `restart`, `reload`.

## Verified Working Operations

| Operation | Works? | Notes |
|-----------|--------|-------|
| List VMs/CTs | ✅ | `/cluster/resources?type=vm` |
| List storage content | ✅ | `/nodes/pve1/storage/local/content` |
| Create LXC | ✅ | `POST /nodes/pve1/lxc` with `--data-urlencode` |
| Delete ISO/template | ✅ | `DELETE /nodes/pve1/storage/local/content/local:iso/<name>` |
| Start/stop VMs | ✅ | `POST /nodes/pve1/<type>/<vmid>/status/start` |
| Read config | ✅ | `GET /nodes/pve1/<type>/<vmid>/config` |
| Modify node description | ✅ | `PUT /nodes/pve1/config` with digest |
| Read hosts file | ✅ | `GET /nodes/pve1/hosts` (read-only) |
| Delete ghost CT | ❌ | Requires `root@pam` shell |
| Create CT with ghost VMID | ❌ | Fails with "CT <vmid> already exists" |
