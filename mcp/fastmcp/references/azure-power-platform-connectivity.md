# Azure → Power Platform Connectivity Patterns

Five canonical patterns for connecting Azure-hosted services to Power Apps, Power Automate, Copilot Studio, and AI Foundry.

## Decision Matrix

| Scenario | Pattern | Auth | Complexity |
|----------|---------|------|------------|
| Public API consumed by Power Platform | **APIM → Custom Connector** | Entra ID / API Key | Low |
| Private Azure PaaS (SQL, KV, Storage) | **VNet Direct** | Entra ID | Medium |
| Private legacy / on-prem system | **On-Prem Gateway** | Windows Auth | High |
| Real-time event reaction | **Event Grid → Flow** | Webhook + Entra | Low |
| Multi-step cross-cloud orchestration | **Logic Apps Hub** | Managed Identity | Medium |

---

## Pattern 1: APIM → Custom Connector (Recommended)

Export any Azure-hosted API through APIM, then export to Power Platform as a custom connector.

```
Power App / Flow → Custom Connector → APIM (auth, rate limit, CORS) → Backend
```

**APIM JWT validation policy:**
```xml
<inbound>
  <validate-azure-ad-token tenant-id="...">
    <client-application-ids>
      <application-id>...</application-id>
    </client-application-ids>
  </validate-azure-ad-token>
  <rate-limit calls="100" renewal-period="60" />
</inbound>
```

**Export:** Azure Portal → APIM → API → Export to Power Platform → select environment.

## Pattern 2: VNet Direct (No Gateway)

Power Platform native VNet support (GA) — delegate a subnet, create private endpoints, connect directly.

```
Power Platform Env → Delegated Subnet → Private Endpoint → Azure SQL / KV / Storage
```

**Setup:**
```bash
az network vnet subnet create \
  --name PowerPlatformDelegatedSubnet \
  --delegations Microsoft.PowerPlatform/enterprisePolicies
```
Then add VNet in Power Platform Admin Center: Environment → Settings → VNet.

## Pattern 3: On-Prem Data Gateway

Legacy/hybrid. Gateway VM bridges Power Platform to private networks.

## Pattern 4: Event Grid → Power Automate

Push-based: Azure events trigger Power Automate flows via webhook.

```bicep
resource sub 'Microsoft.EventGrid/eventSubscriptions@2023-06-01-preview' = {
  scope: storageAccount.id
  properties: {
    destination: { endpointType: 'WebHook', properties: { endpointUrl: flowUrl } }
    filter: { includedEventTypes: ['Microsoft.Storage.BlobCreated'] }
  }
}
```

## Pattern 5: Logic Apps Hub

For multi-step cross-cloud workflows. Logic App orchestrates Azure + GCP + any HTTP endpoint, abstracted behind a single custom connector.

## MCP Server Placement

When your MCP server (FastMCP-based, talking to GCP) needs to be consumed by Power Platform:

```
Copilot Studio / AI Foundry
        │
    ┌───┴───┐
    │ APIM  │ ← Auth, rate limit, IP whitelist
    └───┬───┘
        │
    ┌───┴──────────────┐
    │ Azure Container   │ ← Hosts the MCP server (FastMCP + uvicorn SSE)
    │ Apps (Internal)   │    Workload Identity Federation → GCP
    └───┬──────────────┘
        │
    ┌───┴────┐
    │ GCP     │ Vertex AI, BigQuery, Cloud Storage, etc.
    └────────┘
```

See `~/projects/gcp-mcp-server/docs/azure-power-platform-connectivity.md` for full implementation details including Bicep snippets, APIM policies, and production readiness checklist.
