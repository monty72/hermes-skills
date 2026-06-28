# Private On-Prem → Copilot Studio Connectivity

## The Core Problem

Copilot Studio is multi-tenant SaaS — it can't be put on ExpressRoute. To privately reach a Copilot Studio agent's data, the MCP server must be deployed in Azure (in your VNet) and connected to Copilot Studio via Power Platform VNet Integration.

## 4 Patterns

### 1. VNet + ACA + ExpressRoute (Recommended — fully private)
Copilot Studio → Power Platform VNet Integration → Azure Container Apps (internal, MCP server) → ExpressRoute → on-prem. No public IP anywhere. The VNet integration delegates a subnet to Power Platform; ACA runs in the same VNet with `--ingress internal`.

### 2. APIM Premium (VNet-injected) + ExpressRoute
Copilot Studio hits APIM's public URL (IP-restricted to Microsoft ranges). APIM backend calls go over ExpressRoute to on-prem. Semi-private — the first hop is public HTTPS.

### 3. On-Prem Data Gateway + Custom Connector
Gateway runs on Windows VM on-prem, polls outbound. Private end-to-end but DOES NOT support MCP protocol — only REST custom connectors. You can wrap MCP as a translation layer on-prem.

### 4. Cloudflare Tunnel (dev/testing)
Tunnel from on-prem to Cloudflare edge. Copilot Studio hits the tunnel URL. Not truly private (tunnel provider sees traffic). Fastest to set up for homelabs.

## Key deployment commands

```bash
# ACA internal-only
az containerapp create --name mcp-server --ingress internal \
  --vnet my-vnet --subnet aca-subnet

# VNet subnet delegation for Power Platform
az network vnet subnet create --name pp-subnet \
  --delegations Microsoft.PowerPlatform/enterprisePolicies
```

## MCP protocol limitation

Only Pattern 1 (VNet + ACA) supports native MCP SSE protocol end-to-end. Patterns 3 (gateway) and 4 (tunnel) need a translation layer or only work with REST custom connectors.

Full guidance: `docs/on-prem-copilot-private-connectivity.md` in the `gcp-mcp-server` repo.
