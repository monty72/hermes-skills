# Golden Highway Session — Concrete Output Reference

> Produced: May 2026
> Context: Head of Cloud Architecture (horizontal platform team) at a UK regulated enterprise
> Cloud provider: Azure (primary) + GCP (secondary)
> Tools: Roadie (managed Backstage), GitHub + Actions, Entra ID SSO, ServiceNow ITSM, Terraform, Datadog, PagerDuty

## Files Produced

### Session 1 (Original Golden Highway)
| File | Words | Purpose |
|------|-------|---------|
| `patterns/golden-highway.md` | ~19,500 | Main developer experience pattern |
| `patterns/golden-highway-actions.md` | ~12,400 | 7 Roadie scaffolder custom actions |
| `patterns/golden-highway-oidc.md` | ~6,700 | OIDC auth setup for Azure + GCP |
| `patterns/golden-highway-servicenow.md` | ~9,800 | ServiceNow ITSM integration |

### Session 2 (Tooling Expansion)
| File | Words | Purpose |
|------|-------|---------|
| `patterns/api-portal.md` | ~10,800 | API discovery, developer portal, contract-first development |
| `patterns/feature-flags.md` | ~8,800 | LaunchDarkly/Flagsmith, release toggles, canary rollouts |
| `patterns/schema-registry.md` | ~11,400 | Avro/Protobuf/AsyncAPI event catalog |
| `patterns/idp-architecture.md` | ~15,000 | IDP layer cake, platform team structure, maturity model |
| `patterns/preview-environments.md` | ~9,000 | Ephemeral per-PR deployments |
| `patterns/golden-highway-architecture.html` | SVG | Visual 4-layer IDP reference architecture diagram |

### Principles Update
| File | Change |
|------|--------|
| `principles/PRINCIPLES.md` | Added Principle 11: "Developer Experience is a Platform Concern" |

### Total Across Both Sessions
- **56 files across 26 directories**
- **~56,000 words of pattern content** across 10 pattern files + visual diagram

## Repository State After Session 2

- **56 files across 26 directories**
- **Full platform operating model** — not just blueprints and principles
- Every section of the `cloud-architecture/` repo populated with actionable artefacts
- Visual architecture diagram at `patterns/golden-highway-architecture.html` (open in browser, no dependencies)

## What Session 2 Added That Session 1 Didn't Cover

| Gap | What Was Built | Why It Matters |
|-----|---------------|----------------|
| **Principle 11** | DevEx as formal architecture principle | Without it, DevEx initiatives get deprioritised against Resilience/Security/Cost |
| **API lifecycle** | `api-portal.md` — API gateway, developer portal, contract-first dev, rate limiting, versioning, gRPC, deprecation | Tooling choice matters (Kong vs APIM vs Apigee) and changes based on multi-cloud vs Azure-only |
| **Feature flags** | `feature-flags.md` — LaunchDarkly, flag lifecycle, automated rollback, A/B testing | Needed when user mentions canary releases, gradual rollouts, or kill switches |
| **Event schema management** | `schema-registry.md` — Confluent/Azure/Buf, event catalog in Roadie, compatibility rules, AsyncAPI | Needed when architecture involves Kafka, Event Hubs, or Pub/Sub |
| **Unifying reference** | `idp-architecture.md` — full layer cake, team structure, maturity model, cost model | Needed when user has seen 4+ pattern files and asks "how does this all fit together" |
| **Visual diagram** | `golden-highway-architecture.html` — SVG with 4 layers, data flow arrows | More impactful than markdown for exec presentations, architecture reviews, team onboarding |
| **Ephemeral environments** | `preview-environments.md` — per-PR deployments, 100s lifecycle, cost containment | Needed when user complains about shared dev environments or broken staging |

## Key Design Decisions Captured

### OIDC over Secrets
- GitHub Actions authenticates to Azure + GCP via OIDC workload identity federation
- No secrets stored. No rotation. 5-minute token expiry.
- `main` branch = deploy, `feature/*` branches = read-only

### ServiceNow as Record-Keeper, Not Gate
- CMDB CI record auto-created on service scaffold
- Standard changes (code deploy, non-destructive infra) auto-approved
- High-risk changes (database migration, IAM, security groups) flagged for human approval
- Risk determined by scanning Terraform plan output in CI

### SSO + SCIM Throughout
- Entra ID is source of truth → SCIM provisions GitHub, Roadie, ServiceNow, PagerDuty
- Onboard once in HR system → auto-provisioned in all tools
- Offboard once → access removed from everything

### Developer Output After Scaffold
After clicking "Create" in Roadie, the developer sees:
- GitHub repo URL (branch protection configured)
- Roadie catalog entity
- Datadog dashboard
- PagerDuty service
- Slack channel (#svc-{name})
- ServiceNow CI record (auto-created)
- Azure/GCP dev environment (deployed)
- Estimated monthly cost (£85-120)
- `git clone` instructions

## Golden Highway Variant Templates

All share the same skeleton structure — key difference is the Terraform modules and Docker/Helm config:

| Variant | Primary Compute | Suggested DB | Use Case |
|---------|----------------|--------------|----------|
| web-api | App Service / Cloud Run | Azure SQL / Cloud SQL | REST API, CRUD |
| event-processor | Functions / Cloud Functions | Cosmos DB / Firestore | Async event handling |
| container-service | AKS / GKE | Any | Multi-service, custom infra |
| static-frontend | Static Web Apps / Cloud Storage | None | Frontend, docs, marketing |
| batch-job | Container Instances / Cloud Run Jobs | Azure SQL / BigQuery | Scheduled processing |

## Scaffolded Skeleton Structure

```
skeletons/golden-highway/web-api/
├── .github/workflows/ci.yml, deploy-dev.yml, deploy-prod.yml
├── .github/dependabot.yml
├── src/ (language-specific)
├── infrastructure/azure/main.tf, resources.tf
├── infrastructure/gcp/
├── infrastructure/shared/monitoring.tf (Datadog)
├── kubernetes/base/ + overlays/dev/ + overlays/prod/
├── .datadog/monitors.tf
├── catalog-info.yaml
├── docs/index.md, architecture.md, operations.md
├── Dockerfile, README.md, .gitignore, renovate.json
```

## Cost Model

| Component | Per Developer/Month | Notes |
|-----------|-------------------|-------|
| Roadie | ~$10-15 | Managed Backstage, no infra to run |
| GitHub | ~$4 | Team plan for private repos |
| ServiceNow | Already owned | Enterprise license, this pattern uses existing investment |
| Datadog | ~$15/host | Pro plan, 300+ integrations |
| PagerDuty | ~$21/user | Business plan, service-oriented alerting |
| Terraform Cloud | ~$20/user | Remote state, runs, policy enforcement |
| **Total** | **~$70-80/dev/mo** | vs 10x that in lost productivity without this |

## Performance Claims (from the pattern)

| Activity | Time |
|----------|------|
| Onboarding (new developer) | < 2 hours, zero tickets |
| Service creation (scaffold to deployed) | ~2 minutes |
| Developer's time outside VS Code | ~5% |
| Risk detection from Terraform plan | < 30 seconds |
