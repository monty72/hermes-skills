# Multi-Cloud MCP Architecture (Azure + GCP)

## The Problem

AI agents live in both clouds — Azure AI Foundry / Copilot Studio AND GCP Vertex AI. Both need access to data and services across both clouds. Where does the MCP server run?

## 5 Patterns

### 1. Single MCP in Azure (Recommended default)
MCP runs in Azure Container Apps (internal). Exposes tools for both Azure (via Managed Identity) and GCP (via Workload Identity Federation). Best when Azure is the primary AI platform.

### 2. Single MCP in GCP
Mirror of Pattern 1. MCP runs in Cloud Run (internal). Use when Vertex AI is primary.

### 3. Dual MCP (one per cloud)
Each cloud runs its own MCP server. Azure agents → Azure MCP, GCP agents → GCP MCP. Cross-cloud calls go through a proxy with workload identity. Best when both clouds are equally primary.

### 4. Foundry Toolbox federation
Azure-native. Toolbox bundles multiple MCP endpoints into one agent-facing interface. Single governance plane across both clouds. Works only for Azure agents.

### 5. Sidecar mesh
Per-agent MCP sidecar with tightest auth scoping. Most complex to operate.

## Auth Comparison

| Pattern | Azure auth | GCP auth | Key management |
|---------|-----------|----------|----------------|
| Single in Azure | Managed Identity | Workload Identity Federation | No keys |
| Single in GCP | App Registration + secret | ADC | Client secret needed |
| Dual per cloud | Managed Identity | ADC | No cross-cloud keys |
| Toolbox | Project Connections | API Key | Managed in Foundry |

## Recommendation

Deploy closest to your primary AI runtime. If that's Azure, Pattern 1. If both clouds are equally primary, Pattern 3. Start with 1, split to 3 when isolation demands it.

## Key insight — latency trade-off

Pattern 1: Azure tools = ~2ms, GCP tools = ~200ms (one extra hop)
Pattern 3: Local tools = ~2ms each cloud, cross-cloud = ~102ms

Cross-cloud calls are always slower. Minimise them by keeping most tool calls local.

Full guidance: `docs/multi-cloud-ai-mcp-architecture.md` in the `gcp-mcp-server` repo.
