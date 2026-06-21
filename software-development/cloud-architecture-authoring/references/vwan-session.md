# Session Reference: Azure Virtual WAN Hub Pattern + Policy Artefact (2026-06-18)

## Trigger

User asked for "a standard pattern for azure Vwan hub". Pushed to `monty72/cloud-architecture`.

## Deliverables

| File | Repo Path | Type |
|------|-----------|------|
| `VWAN-001-azure-virtual-wan.md` | `patterns/` | Build pattern — hub types (standard/secured), routing intent, Private Endpoints in vWAN, multi-hub mesh, migration from hub VNet, Bicep impl., cost model, operational runbook, 14 pitfalls |
| `CAF-POL-002-vwan-policy-blueprint.md` | `policy-cicd/` | Governance artefact — 8 custom policy definitions (CUSTOM-VWAN-001 through -008), CAF + WAF initiatives, CI/CD pipeline, assignment map, exemption lifecycle |
| `vwan-reference-architecture.png` | `diagrams/` | Multi-region architecture diagram — official Azure icons, 6-layer topology |

## Key Technique: Diagram Regeneration After Region Change

User asked to change DR region from UK West to Germany West Central after the diagram was already generated. The fix was straightforward — patch the Python script's variable names (`hub_ukw` → `hub_gwc`, etc.), cluster labels, and resource naming, then re-run. The `diagrams` library produces deterministic output, so regenerating is always consistent.

**Workflow for region changes:** patch script → re-run → `git add` new PNG → commit.

## Diagram Approach

Used Python `diagrams` library (official Azure icons, v0.25.1). Multi-region TB layout with Clusters for UK South (active) and Germany West Central (DR). Key import names discovered:

- `VirtualWans` (plural, not singular `VirtualWan`)
- `Firewall as AzureFirewall` (not `AzureFirewall`)
- `ExpressrouteCircuits as ExpressRoute`
- `VirtualNetworkGateways as VPNGateway`
- `SQLDatabases` (not `SQLDatabase`)
- `AppServices` (not `AppService`)
- `Managementgroups` (not `ManagementGroups`)

~190 lines of Python. Output: 739KB PNG at 200dpi.

## Private Endpoints in vWAN (Critical Gotcha)

The #1 difference from traditional hub VNet: vWAN VNet connections are NOT VNet peering — Private DNS Zones linked to a hub VNet do NOT auto-propagate to connected spokes. The pattern document covers the DNS Resolver VNet architecture as the recommended enterprise solution.

## WAF Score Consistency

Both artefacts scored ~87-88%. Sustainability was the weakest pillar (78% / 76%) — confirming the pattern from `references/jetstream-waf-session.md` and `references/afd-frontdoor-session.md` that sustainability is consistently the hardest pillar.

## Repo Push

Commit `adeae9e` (initial) + `8bb2d71` (region fix) to `git@github.com:monty72/cloud-architecture.git`. 3 files, 1,797 insertions initially.

## Follow-up Context

User praised the architecture diagrams and requested a region update. No further corrections or pivots in this session.
