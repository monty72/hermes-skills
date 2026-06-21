# `diagrams` Python Library — Import Quirks & Gotchas

> **Library version:** `diagrams` v0.25.1 (graphviz backend)
> **Last verified:** June 2026
> **Context:** Using `diagrams` from `pip install diagrams` for Azure architecture diagrams with official Microsoft stencil icons.

---

## Why This Reference Exists

The `diagrams` library (diagrams.mingrammer.com) lets you generate cloud architecture diagrams as Python code. However, its import names don't always match Azure service names you'd expect. This reference saves the 3-5 import-error cycles per diagram session.

---

## Quick-Reference: Import Names vs Expected Names

| Expected Name | Actual Import Path | Actual Name |
|---|---|---|
| `VirtualWan` | `diagrams.azure.network` | **`VirtualWans`** (plural) |
| `VirtualHub` | (does not exist) | Use `Blank` with a label |
| `Firewall` / `AzureFirewall` | `diagrams.azure.network` | **`Firewall`** |
| `ExpressRoute` | `diagrams.azure.network` | **`ExpressrouteCircuits`** |
| `VPNGateway` | `diagrams.azure.network` | **`VirtualNetworkGateways`** |
| `RouteTable` | `diagrams.azure.network` | **`RouteTables`** |
| `FrontDoor` | `diagrams.azure.network` | **`FrontDoors`** |
| `PrivateDNSZone` | `diagrams.azure.network` | **`DNSPrivateZones`** |
| `SQLDatabase` | `diagrams.azure.database` | **`SQLDatabases`** (plural) |
| `CosmosDB` / `CosmosDb` | `diagrams.azure.database` | **`CosmosDb`** ✅ (this one matches) |
| `AppService` | `diagrams.azure.web` | **`AppServices`** (plural) |
| `APIM` / `APIManagement` | `diagrams.azure.web` | **`APIManagementServices`** |
| `KeyVault` | `diagrams.azure.security` | **`KeyVaults`** (plural) |
| `LogAnalyticsWorkspace` | `diagrams.azure.analytics` | **`LogAnalyticsWorkspaces`** (plural) |
| `ApplicationInsights` | `diagrams.azure.devops` | **`ApplicationInsights`** ✅ |
| `StorageAccounts` | `diagrams.azure.storage` | **`StorageAccounts`** ✅ |
| `BlobStorage` | `diagrams.azure.storage` | **`BlobStorage`** ✅ |
| `CognitiveServices` | `diagrams.azure.ml` | **`CognitiveServices`** ✅ |
| `AzureOpenAI` | `diagrams.azure.ml` | **`AzureOpenAI`** ✅ |
| `MachineLearningServiceWorkspaces` | `diagrams.azure.ml` | **`MachineLearningServiceWorkspaces`** ✅ |
| `ActiveDirectory` | `diagrams.azure.identity` | **`ActiveDirectory`** ✅ |
| `ManagementGroups` | `diagrams.azure.general` | **`Managementgroups`** (lowercase 'g') |
| `VM` | `diagrams.azure.compute` | **`VM`** ✅ |
| `AKS` | `diagrams.azure.compute` | **`AKS`** ✅ (good stand-in for Container Apps) |
| `Internet` | `diagrams.onprem.network` | **`Internet`** ✅ |
| `User` | `diagrams.onprem.client` | **`User`** ✅ |
| `Blank` | `diagrams.generic.blank` | **`Blank`** ✅ |
| `Custom` | `diagrams.custom` | **`Custom`** ✅ |

---

## Names That DO NOT Exist

| Tried | Actual / Workaround |
|-------|-------------------|
| `diagrams.azure.network.VirtualHub` | Does not exist. Use `Blank("Virtual Hub\\n...")` |
| `diagrams.azure.network.ContainerApps` | Does not exist. Use `diagrams.azure.compute.AKS` as visual stand-in |
| `diagrams.azure.network.PrivateEndpoint` | Actually DOES exist in v0.25.1 ✅ |
| `diagrams.azure.analytics.CognitiveSearch` | Does not exist. Use `CognitiveServices` (generic AI icon) |
| `diagrams.azure.ai` | **Module does not exist** — use `diagrams.azure.ml` instead |
| `diagrams.azure.cognitiveservices` | **Module does not exist** — use `diagrams.azure.ml` instead |
| `diagrams.azure.security.ManagedIdentities` | Does not exist. Use `Blank("Managed Identity")` |
| `diagrams.azure.security.Sentinel` | Actually `AzureSentinel` in `diagrams.azure.security` |

---

## Edge Attribute Gotchas

Cannot use `**dict` unpacking AND override a key in the same `Edge()` call:

```python
# WRONG — TypeError: got multiple values for keyword argument 'style'
fw >> Edge(**edge_attr_inspect, style="dotted", label="Inspected") >> spoke

# RIGHT — create a new dict or spell it out
fw >> Edge(color="#E81123", style="dotted", label="Inspected") >> spoke
```

---

## Common Diagram Patterns

### Clustered regions with internal components

```python
from diagrams import Diagram, Edge, Cluster

with Diagram("Title", show=False, filename="path", direction="TB"):
    with Cluster("Region Name"):
        component = VirtualNetwork("vnet-name")
        workload = AppServices("App Service")
        component >> Edge(color="#0078D4") >> workload
```

### Layered architectures (TB direction)

```
Layers stack naturally with TB direction:
  Layer 1 (top) → most abstract / user-facing
  Layer N (bottom) → infrastructure
```

### Using Blank as placeholder

```python
from diagrams.generic.blank import Blank
placeholder = Blank("Label Text\n(description)")
```

---

## Verification

After generating a `.png`, verify it rendered correctly:

```bash
ls -lah diagrams/*.png
# Expected: 300KB-1.5MB for 200dpi diagrams
```

If file size is suspiciously small (<100KB), the diagram may have layout errors.
If generation succeeds but the output is blank, check that you connected nodes with `>>` operators — unconnected nodes are omitted from the output.
