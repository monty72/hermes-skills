# Proxmox API Collection

## Overview

The observability collector gathers Proxmox VE hypervisor data using the PVE API at `192.168.1.6:8006`. It collects node status, CPU/memory, VM/CT inventory, and per-VM resource allocations.

## Authentication

```python
# Token from vault
token = "PVEAPIToken=hermes2@pve!api=19b5fd1b-8518-4a31-9154-e8ad066a86ae"
url = "https://192.168.1.6:8006"
```

The token is stored in the Hermes vault under `PROXMOX_API_TOKEN` (the full `PVEAPIToken=` string including the value).

**Important:** The PVE API uses a self-signed cert. All requests must use `ssl._create_unverified_context()`.

## Endpoints

### Node Status
```
GET /api2/json/nodes/pve1/status
```
Returns: CPU model, cores, memory (total/used/free), uptime, PVE version.

### Cluster Resources (VMs + CTs)
```
GET /api2/json/cluster/resources?type=vm
```
Returns: All VMs and containers across the cluster with VMID, name, status, type (qemu/lxc), memory (MB), disk (bytes), vCPUs.

### VM/CT Actions
```
POST /nodes/pve1/{type}/{vmid}/status/{action}
```
Where `type` is `qemu` or `lxc`, and `action` is one of: `start`, `stop`, `shutdown`, `reboot`.

Example:
```python
import urllib.request, ssl
ctx = ssl._create_unverified_context()
req = urllib.request.Request(
    f"{url}/api2/json/nodes/pve1/{vm_type}/{vmid}/status/{action}",
    data=b"",
    headers={"Authorization": token},
    method="POST",
)
with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
    body = json.loads(resp.read())
    task_id = body.get("data")
```

The response contains a task UPID string. Tasks run asynchronously — the VM may take a few seconds to change state.

### Container Config (Read)
```
GET /api2/json/nodes/pve1/lxc/{vmid}/config
```
Returns: hostname, ostype, cores, memory, swap, net0 (network config), rootfs, unprivileged flag.

### Container Config (Update — Static IP)
```
PUT /api2/json/nodes/pve1/lxc/{vmid}/config
```
Must use `--data-urlencode` for `net0` to avoid comma parsing errors:
```bash
curl -sk -X PUT '.../nodes/pve1/lxc/200/config' \
  -H 'Authorization: PVEAPIToken=...' \
  --data-urlencode 'net0=name=eth0,bridge=vmbr0,hwaddr=BC:24:11:F1:41:68,ip=192.168.1.200/24,gw=192.168.1.1,type=veth'
```

The container must be **stopped** before updating the config, then restarted.

## Collector Pattern (Python)

```python
import ssl, json, urllib.request

ctx = ssl._create_unverified_context()
headers = {
    "Authorization": token,  # "PVEAPIToken=hermes2@pve!api=..."
    "Accept": "application/json",
}

def pve_fetch(endpoint):
    req = urllib.request.Request(f"{url}{endpoint}", headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        return json.loads(resp.read())

# Node status
node = pve_fetch("/api2/json/nodes/pve1/status")
data = node.get("data", {})

# VMs
resources = pve_fetch("/api2/json/cluster/resources?type=vm")
vms_data = resources.get("data", [])
```

## Data Mapping (Snapshot)

| Field | Source path | Notes |
|-------|-----------|-------|
| `cpuPct` | node `cpu` × 100 | Already a ratio (0.012 = 1.2%) |
| `cpuModel` | node `cpuinfo.model` | e.g. "AMD Ryzen 7 5825U" |
| `cores` | node `cpuinfo.cpus` | CPU count |
| `memTotalGB` | node `memory.total` ÷ 1e9 | Bytes to GB |
| `memUsedGB` | node `memory.used` ÷ 1e9 | Bytes to GB |
| `memPct` | `memUsedGB / memTotalGB × 100` | Percentage |
| `version` | pveversion | e.g. "pve-manager/9.2.2" |
| `uptime` | `uptime` | Seconds, formatted as `0d Xh Ym` |
| `reachable` | (boolean) | Whether the API responded |
| `nodeName` | `pve1` | Static |
| `vmTotal` | vms_data `length` | All VMs/CTs |
| `vmRunning` | vms_data `filter(status === 'running')` | Running count |
| `vmStopped` | vms_data `filter(status === 'stopped')` | Stopped count |
| `vms[]` | vms_data | Array of VM objects |

### VM Object Mapping

| Field | Source |
|-------|--------|
| `vmid` | `vmid` (int) |
| `name` | `name` |
| `status` | `status` |
| `type` | `type` (string: "qemu" or "lxc") |
| `memGB` | `mem` (bytes) ÷ 1e9, rounded |
| `diskGB` | `disk` (bytes) ÷ 1e9, rounded |
| `cpus` | `cpus` (int) |

**The `type` field** distinguishes QEMU VMs from LXC containers. Required for VM actions (start/stop/shutdown) since qemu and lxc use different API paths.

## Known Labels (for VM detail modal)

```javascript
const vmLabels = {
  105: '🧠 This is the Hermes agent VM',
  104: '📡 This is the OpenCrawl worker VM',
  102: '🏠 This is the Home Assistant VM',
};
```

## Pitfalls

- The `cpu` field from the API is a ratio (0.0–1.0), not a percentage. Multiply by 100.
- Memory is in **bytes**, not MB or GB. Divide by 1e9 for GB.
- `uptime` is in **seconds**. Format with `days = s // 86400; hours = (s % 86400) // 3600; mins = (s % 3600) // 60`.
- The API can be slow (3–5s on first request after inactivity). Set timeout=10.
- Self-signed cert means you MUST use `ssl._create_unverified_context()` — skipping it causes `CERTIFICATE_VERIFY_FAILED`.
- VM `type` (qemu vs lxc) must be known for action commands — POST to `/nodes/pve1/qemu/{vmid}/status/start` vs `/nodes/pve1/lxc/{vmid}/status/start`.
- All actions use POST with an empty body (`data=b""`). A GET will fail with 405 Method Not Allowed.
- **`!` in token value is safe in Python** but will cause bash history expansion issues if used in shell scripts. Use single quotes or `set +H`.
