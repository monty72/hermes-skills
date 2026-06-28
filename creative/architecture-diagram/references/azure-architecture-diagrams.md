---
name: azure-architecture-diagrams
description: Generate production-quality Azure (and cross-cloud) architecture diagrams using the `diagrams` Python library with official Microsoft Azure stencil icons. For Head of Cloud Architecture / platform leads who need real diagrams with the actual iconography — not custom SVG approximations. Supports Azure, GCP, AWS, Kubernetes, on-prem, and custom nodes. Use whenever the user asks for an "Azure architecture diagram", "reference architecture", "landing zone diagram", or mentions official cloud stencil kits.
---

# Azure Architecture Diagrams

Generate architecture diagrams using the `diagrams` Python library. Produces `.png` output with the actual official Microsoft Azure icon set (and GCP, AWS, K8s, on-prem, or generic icons as needed).

## Prerequisites

```bash
pip install --break-system-packages diagrams
sudo apt-get install -y graphviz
```

Verify: `python3 -c "from diagrams import Diagram; print('OK')"`

## Technique

The `diagrams` library wraps Graphviz to produce clean orthogonal-routed architecture diagrams. Each service is a node with its official SVG icon. Clusters group related services. Edges connect them with styled lines.

### Basic Structure

```python
from diagrams import Diagram, Edge, Cluster
from diagrams.azure.compute import AppServices, AKS, FunctionApps
from diagrams.azure.database import SQLDatabases, CosmosDb
from diagrams.azure.network import FrontDoors, Firewall
from diagrams.azure.security import KeyVaults
from diagrams.azure.identity import ActiveDirectory

output_path = "/home/matth/my-diagram"

with Diagram("Title", show=False, direction="LR", filename=output_path, outformat="png",
    graph_attr={"bgcolor": "#0f172a", "fontcolor": "#e2e8f0", "fontname": "JetBrains Mono", "dpi": "200", "splines": "ortho"},
    node_attr={"fontcolor": "#e2e8f0", "fontname": "JetBrains Mono", "fontsize": "9"},
    edge_attr={"fontcolor": "#94a3b8", "fontname": "JetBrains Mono", "fontsize": "7"},
):
    # ... nodes and edges
```

### Finding the Right Service Class Names

The `diagrams` library has TWO module naming conventions — check both:

```bash
python3 -c "
import diagrams.azure
import pkgutil, importlib
for importer, modname, ispkg in pkgutil.iter_modules(diagrams.azure.__path__):
    mod = importlib.import_module(f'diagrams.azure.{modname}')
    names = [x for x in dir(mod) if not x.startswith('_')]
    print(f'\n--- {modname} ---')
    print(', '.join(sorted(names)[:30]))
"
```

Some modules have both old and new names (e.g. `diagrams.azure.network` and `diagrams.azure.networking`). The old-namespace (`network`) is usually more complete for Azure. Common imports:

### 🔑 Key Pattern: All Azure Service Classes Use PLURAL Names

The `diagrams` library follows a strict naming rule for Azure icons: **every Azure service class name is plural** (unlike the Azure portal which uses singular names). This is a systematic pattern, not per-class:

| Azure portal name | `diagrams` class name | Why |
|---|---|---|
| Virtual WAN | `VirtualWans` | Plural |
| Front Door | `FrontDoors` | Plural |
| App Service | `AppServices` | Plural |
| Key Vault | `KeyVaults` | Plural |
| SQL Database | `SQLDatabases` | Plural |
| Function App | `FunctionApps` | Plural |
| Private Endpoint | `PrivateEndpoint` | No word to pluralize |

Azure services → **pluralize the last word**. "Virtual WAN" → `VirtualWans`, not `VirtualWan`. "App Service" → `AppServices`, not `AppService`. "ExpressRoute Circuit" → `ExpressrouteCircuits`.

The only exceptions are single-word names (no word to pluralize): `Firewall`, `Monitor`, `AKS`, `CosmosDb`, `Blank`, `PrivateEndpoint`. These have no trailing `s`. When you see an import error for a class name that matches the Azure portal's singular form, try the plural.

**Always verify before you write the script:**
```bash
python3 -c "
from diagrams.azure.network import *
import diagrams.azure.network as mod
names = [n for n in dir(mod) if not n.startswith('_') and n[0].isupper()]
print('\n'.join(sorted(names)))
"
```

| Azure Service | Module | Class |
|--------------|--------|-------|
| Virtual WAN | `diagrams.azure.network` | `VirtualWans` |
| Virtual Hub | `diagrams.azure.network` | ⚠️ No icon — use `Blank` from generic |
| Front Door / WAF | `diagrams.azure.network` | `FrontDoors` |
| App Gateway | `diagrams.azure.network` | `ApplicationGateway` |
| Azure Firewall | `diagrams.azure.network` | `Firewall` |
| ExpressRoute Circuit | `diagrams.azure.network` | `ExpressrouteCircuits` |
| VPN / ER Gateway | `diagrams.azure.network` | `VirtualNetworkGateways` |
| VNet | `diagrams.azure.network` | `VirtualNetworks` |
| Route Table | `diagrams.azure.network` | `RouteTables` |
| Private Endpoint | `diagrams.azure.network` | `PrivateEndpoint` |
| Private DNS Zones | `diagrams.azure.network` | `DNSPrivateZones` |
| Load Balancer | `diagrams.azure.network` | `LoadBalancers` |
| App Service | `diagrams.azure.compute` | `AppServices` |
| AKS | `diagrams.azure.compute` | `AKS` |
| Functions | `diagrams.azure.compute` | `FunctionApps` |
| Container Instances | `diagrams.azure.compute` | `ContainerInstances` |
| VM | `diagrams.azure.compute` | `VM` / `VMScaleSets` / `VMSS` |
| SQL Database | `diagrams.azure.database` | `SQLDatabases` |
| Cosmos DB | `diagrams.azure.database` | `CosmosDb` |
| Redis Cache | `diagrams.azure.database` | `CacheForRedis` |
| Service Bus | `diagrams.azure.integration` | `ServiceBus` |
| API Management | `diagrams.azure.integration` | `APIManagement` |
| Event Hubs | `diagrams.azure.analytics` | `EventHubs` |
| Event Grid | `diagrams.azure.integration` | `EventGridTopics` |
| Storage (Blob) | `diagrams.azure.storage` | `BlobStorage` |
| Key Vault | `diagrams.azure.security` | `KeyVaults` |
| Management Groups | `diagrams.azure.general` | `Managementgroups` |
| Entra ID | `diagrams.azure.identity` | `ActiveDirectory` |
| AI Foundry | `diagrams.azure.ml` | `MachineLearningServiceWorkspaces` |
| Content Safety | `diagrams.azure.ml` | `CognitiveServices` |
| Monitor | `diagrams.azure.monitor` | `Monitor` |
| App Insights | `diagrams.azure.monitor` | `ApplicationInsights` |
| Log Analytics | `diagrams.azure.monitor` | `LogAnalyticsWorkspaces` |
| Defender for Cloud | `diagrams.azure.security` | `MicrosoftDefenderForCloud` |
| GitHub Actions | `diagrams.onprem.ci` | `GithubActions` |
| Users/Clients | `diagrams.onprem.client` | `Users` |

### Non-Azure Icons

```python
from diagrams.onprem.client import Users
from diagrams.onprem.ci import GithubActions
from diagrams.onprem.monitoring import Grafana, Prometheus
from diagrams.generic.blank import Blank          # Generic placeholder
from diagrams.generic.database import SQL         # Generic DB
from diagrams.generic.network import Firewall     # Generic firewall
from diagrams.generic.storage import Storage      # Generic storage
from diagrams.programming.language import Python  # Language icons
```

## Layout & Aesthetics

### Orientation

- `direction="TB"` — top-to-bottom (best for layered/hierarchical architectures like KV reference)
- `direction="LR"` — left-to-right (best for data-flow/landing zone diagrams)
- `direction="BT"` — bottom-to-top

### Dark Theme (user-preferred)

```python
graph_attr={
    "bgcolor": "#0f172a",          # Slate-950 background
    "fontcolor": "#e2e8f0",        # Slate-200 text
    "fontname": "JetBrains Mono",
    "dpi": "200",                  # Retina quality
    "pad": "1.0",
    "ranksep": "0.9",              # Vertical gap between layers
    "nodesep": "0.5",              # Horizontal gap between peers
    "splines": "ortho",            # Right-angle routing
}
node_attr={"fontcolor": "#e2e8f0", "fontname": "JetBrains Mono", "fontsize": "9"}
edge_attr={"fontcolor": "#94a3b8", "fontname": "JetBrains Mono", "fontsize": "7"}
```

### Cluster Colors (Semantic)

```python
with Cluster("Hub Network", graph_attr={
    "bgcolor": "#1e293b",         # Slate-800
    "fontcolor": "#fbbf24",       # Amber-400
    "pencolor": "#fbbf24",        # Border
    "style": "dashed",            # Dashed border
}):
```

| Layer | Font Color | Purpose |
|-------|-----------|---------|
| Hub / Management Plane | `#fbbf24` (amber) | Network/infrastructure layer |
| Compute / Production | `#34d399` (emerald) | Workloads |
| Data | `#a78bfa` (violet) | Databases |
| Security | `#fb7185` (rose) | Security/monitoring |
| CI/CD | `#22d3ee` (cyan) | DevOps |
| Non-Prod | `#a78bfa` (violet) | Dev/test/QA |

### Using `Blank` for Text-Only Nodes in Clusters

Some Azure services have no dedicated icon in the `diagrams` library (e.g. Virtual Hub, Firewall Policy, Management Groups). Use `Blank` from `diagrams.generic.blank` as a text-only label:

```python
from diagrams.generic.blank import Blank

with Cluster("UK South — Primary Region"):
    hub = Blank("Virtual Hub\nvhub-uks-prod\n10.100.0.0/23")  # text-only placeholder
    fw = Firewall("Azure Firewall (Premium + IDPS)")
```

`Blank` renders as a small invisible node that serves as an anchor for edges and shows multi-line text. Use it whenever a component exists in the architecture but doesn't have a library icon.

### Edge Styles for Different Traffic Types

Define separate `Edge` attribute dicts for different traffic types to make the diagram semantically readable:

```python
edge_inspect  = {"color": "#E81123", "style": "bold", "fontsize": "9"}   # Firewall-inspected traffic
edge_network  = {"color": "#0078D4", "style": "bold", "fontsize": "9"}   # Direct network flow
edge_mgmt     = {"color": "#0078D4", "style": "dotted", "fontsize": "9"}  # Management/control plane
edge_dns      = {"color": "#FF8C00", "style": "dashed", "fontsize": "9"}  # DNS resolution

# Usage:
hub >> Edge(**edge_inspect, label="Routing Intent") >> fw
hub >> Edge(**edge_network) >> er
mgmt >> Edge(**edge_mgmt, label="Policy →") >> vwan
spoke >> Edge(**edge_dns, label="DNS query") >> dns
```

This pattern makes diagrams self-documenting: red = inspected, blue = direct, dotted = management, orange/dashed = DNS.

### Edge Styles

```python
users >> Edge(color="#94a3b8", style="dashed") >> front_door           # HTTPS / external
front_door >> Edge(color="#fbbf24", label="WAF") >> apim               # Security-filtered
apps >> Edge(color="#22d3ee") >> service_bus                            # Async messaging
apps >> Edge(color="#a78bfa") >> sql                                    # Data access
apps >> Edge(color="#fb7185", style="dashed") >> monitor                # Observability
aks >> Edge(color="#e2e8f0", style="dotted", label="Managed ID") >> entra  # Identity
apps >> Edge(color="#facc15", style="dotted", label="Secrets") >> kv    # Secrets
actions >> Edge(color="#22d3ee", label="OIDC") >> apps                   # CI/CD deploy
```

## Output

Script writes a `.png` file to the `output_path` location. Set `outformat="png"`. The file is typically 500KB-1.5MB at 200dpi.

To deliver to the user, send via Telegram with the MEDIA: prefix:
```python
send_message(message=f"Description: MEDIA:{output_path}.png", target="telegram")
```

## Known Issues

- **Direction `LR` with many clusters** can produce extremely tall images (e.g. 3128x10778px). For complex multi-cluster diagrams with `direction="LR"`, reduce `ranksep` to `0.6` and `nodesep` to `0.4`. Or switch to `direction="TB"` for hierarchical layers.
- **Class names differ between library versions.** Always verify with `python3 -c "from diagrams.azure.X import *; print([x for x in dir() if not x.startswith('_')])"` before writing the script.
- **Dark theme requires setting bgcolor explicitly** — the default is white.
- **execute_code() sandbox** does not have `diagrams` installed. Always run via `terminal()` in the user's environment.
- **File sizes** at 200dpi can be 1MB+. Set `dpi="100"` for quicker iterations if needed.

## Workflow

1. User describes the architecture (services, layers, connections)
2. Write the Python script using `diagrams.azure.*` imports
3. Save to `/tmp/` and run via `terminal()` 
4. Copy to `~/.hermes/media_cache/` for Telegram delivery
5. Send with `MEDIA:` prefix

## Reference

- `references/landing-zone-example.py` — Worked example: Azure Landing Zone with hub, prod, non-prod, management spokes
- `references/key-vault-architecture.py` — Worked example: Key Vault enterprise reference (management plane → KV → consuming workloads)
