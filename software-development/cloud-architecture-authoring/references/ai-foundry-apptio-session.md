# AI Foundry + Apptio FinOps — Concrete Session Output Reference

> Produced: May 2026
> Context: Head of Cloud Architecture (horizontal platform team) at Royal Mail (UK regulated logistics enterprise)
> Cloud: Azure (primary) + GCP (secondary)
> Tools: Apptio Cloudability, ServiceNow, LeanIX, Grafana, PagerDuty, Backstage, SAP, Entra ID, Datadog
> Repo: cloud-architecture (local, ~/code/cloud-architecture/)

## Session Overview

This session spanned two major document suites plus strategy advice:

1. **Azure AI Foundry** — Complete document suite (13 files) covering the full AI platform lifecycle
2. **Apptio FinOps** — Enterprise FinOps operating model with 11 integrations, auto-response, RACI, tagging standard, and architecture diagram
3. **Strategy advice** — Monetisation assessment and sub-agent evaluation

## Files Produced

### Azure AI Foundry Suite

| File | Words | Content |
|------|-------|---------|
| `principles/AI-FOUNDRY.md` | ~4,100 | PRN-012 — AI workloads must use Azure AI Foundry. Exceptions require ARB. Rationale, scope, compliance. |
| `patterns/ai-foundry-hub-project.md` | ~20,000 | Hub & Project resource model. Hub ownership (VNet, PE, MI, connection secrets, model catalog, compute quotas) vs Project ownership (prompt flows, evals, deployments, AI Search indexes). Naming convention `rm-{env}-{region}-aif-hub-{team}`. 5 max hubs/sub, 100 max projects/hub. 7 private endpoint types. RBAC roles. Terraform variables.tf. 5 pitfalls documented. |
| `patterns/ai-foundry-landing-zone.md` | ~18,600 | Full Terraform module (main.tf, networking.tf, identity.tf, diagnostics.tf, content-safety.tf, quota.tf). Hub provisioning `azurerm_machine_learning_workspace`. Project provisioning with sizing matrix (5 tiers from £200 to £15,000/mo). Private endpoint config for 8 services. Egress firewall allow-list. Backstage scaffolder action YAML. GitHub Actions CI/CD YAML. Mermaid reference architecture. |
| `patterns/ai-foundry-models.md` | ~27,000 | 13 model tables with endpoint type, versions, context length, pricing (GBP), UK region availability, throughput limits, quota. Decision flow diagram (Mermaid). Prompt caching (GPT-4o: 1,024 token prefix, 50% saving). Model versioning policy — one-quarter grace period. Quota defaults (UK South: GPT-4o 450K TPM, GPT-4o-mini 10M TPM, embeddings 1M TPM). Quota increase process. |
| `patterns/ai-foundry-golden-path.md` | ~23,000 | 5-phase workflow. Phase 1 (Day 1-2): Discovery — model catalog, playground, baseline prompts. Phase 2 (Day 2-5): Experiment — Backstage scaffolder, Prompt Flow build, iteration. Phase 3 (Day 5-7): Evaluate — GPT-as-judge evaluators, pass/fail gates (4.0/5.0 minimum on all metrics), content safety scan. Phase 4 (Day 7-9): Deploy — managed endpoint, A/B traffic split, auto-scaling. Phase 5 (Day 9-10): Monitor — Datadog integration, cost tags, ServiceNow registration. Prompt engineering patterns (system prompt template, few-shot placement, temperature vs top-p). Rollback procedure. Full CLI command reference. |
| `patterns/ai-foundry-prompt-flow.md` | ~29,000 | Flow types (Standard, Chat, Evaluation). Node types (LLM, Python, Prompt). $ variable reference syntax. Custom GPT-as-judge evaluators with full judge prompt templates. Code-based evaluators (BLEU, ROUGE-L, F1, Exact Match) with complete Python. Variants for A/B testing. Bulk runs. Deployment (Docker export, online endpoint). CI/CD (full GitHub Actions workflow YAML with threshold gating). Tracing. 5 pitfalls documented. |
| `patterns/ai-foundry-rag.md` | ~31,000 | User → Prompt Flow → AI Search (hybrid) → GPT-4o-mini → Response. Data ingestion pipeline with Document Intelligence skill set JSON. Chunking strategies (fixed 512/64, semantic, hierarchical). Embedding dimension selection table (256/512/1024/3072). AI Search index schema with HNSW config, scoring profile (keyword 0.3/vector 0.5/freshness 0.2). Guardrails (query rewriting, 0.7 relevance threshold, citation extraction, no-context fallback). Evaluation (hit rate, MRR, NDCG for retrieval; groundedness, faithfulness for generation). Cost model per 100K queries ($100.80). 5 pitfalls. |
| `patterns/ai-foundry-content-safety.md` | ~35,000 | Hub-level service. Categories (Hate/Sexual/Violence/SelfHarm, 0-6 scale). Thresholds by workload type (customer-facing vs internal). Custom blocklists (platform-wide + project-specific). Jailbreak risk detection. Protected material detection (code + text). Azure CLI configuration commands. Python SDK examples. Prompt Flow integration YAML. Monitoring dashboard metrics. Red teaming playbook — monthly schedule, 50+ attack patterns across 9 families using PyRIT. False positive management through ServiceNow (48h adjudication SLA). Mandatory requirements table. Exemption process (90-day, ARB-approved). Royal Mail-specific PII patterns (tracking numbers RMXXXXXXXXXGB, employee IDs). |
| `patterns/ai-foundry-cost-management.md` | ~18,300 | Pricing models (PAYG, PTU, Batch 50% discount, Serverless). Model pricing tables in GBP. PTU sizing formula with Python code example. Quota defaults table. Quota increase process (standard/significant/emergency). Budget config (80/90/100/120% thresholds with Slack, PagerDuty, and CTO escalation). 7 optimisation strategies (right-model 94% saving, prompt caching 50% saving, batch mode 50% discount, embedding dimension reduction 80% saving, compute right-sizing £6,300/mo, idle shutdown 60% saving, reserved instances 30-50% saving). MACC commitment tiers. Monthly review checklist. Cost anomaly detection bash script. |
| `patterns/ai-foundry-runbook.md` | ~22,800 | Core services map (Hub, Azure OpenAI, AI Search, Content Safety). Health check script. SLA targets (99.9%, P95 < 5s, P1 < 30min). 8 incident templates: INC-01 429 quota, INC-02 high latency, INC-03 false positives, INC-04 eval drift, INC-05 cost anomaly, INC-06 private endpoint, INC-07 hub unavailable, INC-08 model deprecation. Each with: symptoms, diagnosis CLI, resolution steps, escalation path (Tier 1 → 2 → Microsoft), verification. |
| `patterns/ai-foundry-compliance.md` | ~16,000 | UK GDPR, DPA 2018, Ofcom. Data-zone vs global-standard endpoints. Data classification tiers (Public/Internal/Confidential/Restricted) with model restrictions. Audit requirements (5 mandatory records with retention). PII handling rules (data-zone endpoints, content safety blocklist JSON, no fine-tuning on PII). Model transparency pack (evaluation report + RA impact assessment + data sheet). Monthly evidence collection bash script. Approved models list with ARB intake process. Exemption process (ARB charter exception, 12-month max). |
| `patterns/ai-foundry-gateway.md` | ~15,000 | Multi-provider inference fallback (Azure → AWS Bedrock → GCP Vertex). LiteLLM config (full YAML with model list, router settings, fallbacks). Provider endpoints table. Authentication (gateway API keys scoped by team, provider creds in Key Vault). Cost routing table. Datadog OpenTelemetry integration. Deployment options (LiteLLM on ACA £200/mo, Portkey SaaS £500-5K/mo, Kong AI Gateway). Operational runbook (health check, failed provider recovery, test failover). |

### Apptio FinOps

| File | Words | Content |
|------|-------|---------|
| `patterns/apptio-finops.md` | ~28,400 | Executive summary with 10-15% Year 1 savings target. 11-system integration architecture table with protocols and frequency. End-to-end data flow (4-stage pipeline). Showback → chargeback strategy with cost centre hierarchy. Auto-response workflow (anomaly → Slack + ServiceNow INC + Backstage ticket + PagerDuty escalation). 10-event catalogue with triggers, severity, auto-actions, and SLA. Budget management (annual SAP import, monthly phasing, ServiceNow approval workflow). Reservation tracking (Azure RI, Savings Plan, GCP CUD, capacity reservations) with dashboard metrics. Unit economics (6 metrics with unit cost targets, efficiency ratio). Anomaly detection algorithm with investigation template. Governance cadence (weekly/monthly/quarterly/annual). Target audience dashboards (CFO, CTO, Dev). 4-phase implementation roadmap (8 months). Cost & resourcing (licensing £15-30K/yr per £1M spend + £50-100K implementation + 0.5 FTE). 9 pitfalls with risk ratings and mitigations. |
| `standards/TAGGING.md` | ~18,800 | Exhaustive enterprise tagging standard. 9 mandatory tags with regex validation. 30+ optional tags across 8 categories. Tag format rules (PascalCase names, lowercase hyphen values, max 50 chars). Azure Policy JSON definitions (deny, modify, append). GCP Org Policy CEL constraints. Cost allocation hierarchy (primary: CostCentre → Workload → Environment; secondary: BusinessUnit → ServiceTier → CostType). Apptio-specific tags (5 tags with purpose and values). Tag lifecycle management (new/deprecation/audit). Exemption process (ARB-only, 90-day, auto-P3). Compliance reporting (4 reports with cadence, tag health score formula). Azure + GCP tag validation bash scripts. Tag matrix by resource type (18 resource types). |
| `standards/FINOPS-RACI.md` | ~10,700 | 8 roles × 50+ activities. Role definitions table (11 roles). 8 RACI domains: Core FinOps process (8 rows), Budget management (10 rows), Reservation management (9 rows), Anomaly & incident (10 rows), Tag governance (10 rows), Integration & data pipeline (11 rows), Reporting & dashboards (9 rows), Strategic (10 rows). Each row maps R/A/C/I per role. |
| `diagrams/apptio-finops-architecture.html` | SVG | 5-layer dark-themed SVG: Layer 1 (Cloud: Azure, GCP, Entra ID, SAP), Layer 2 (Apptio Core: ingestion, allocation, anomaly detection), Layer 3 (Integration: ServiceNow, LeanIX, Backstage, PagerDuty, Slack/Teams, Datadog), Layer 4 (Consumption: Grafana, ServiceNow, LeanIX, SAP), Layer 5 (Governance: FinOps cadence, RACI, tag standard, ARB, enterprise standards). Legend. 3 info cards (11 integrations, auto-response workflows, governance metrics). |

### Strategy Documents

| File | Content |
|------|---------|
| `enterprise/MONETISATION-STRATEGY.md` | 5 monetisation angles. Operating model as product (Gumroad/Substack). Consulting-as-code (£15K/engagement). Content business (newsletter, KDP, templates). Skill pack subscriptions (£49-99/yr). White label to consultancies (£5-50K). Feasibility matrix. Recommended next step. |
| `enterprise/SUBAGENT-ASSESSMENT.md` | When a sub-agent is useful vs when cron jobs are better. Recommendation: skip sub-agent, set up cron-based content generation instead. Concrete cron config examples. |

## Key Patterns and Techniques Discovered

### AI Foundry Document Authoring
- **Document count:** 12 core documents + 1 architecture diagram for a complete AI platform document suite
- **Each document must stand alone** — cross-reference don't cross-depend. A FinOps reader shouldn't need to read the golden path.
- **Pricing in GBP, not USD** — UK enterprises won't convert. Include the pricing date.
- **Model catalog must be self-service** — "When to use X vs Y" decision tree is the most consulted section
- **Content safety triggers are the second most consulted** — teams need to know what gets blocked and how to handle false positives

### Apptio FinOps Document Authoring
- **Integration table with protocols and frequency** is the most referenced section — teams need to know how data flows, not just that it connects
- **Auto-response workflow** is the differentiator — "when X happens, Y auto-creates" sells the value proposition
- **RACI is a negotiation tool** — teams use it to resolve who pays for what. Get the roles right.
- **Tagging standard is the foundation** — without it, Apptio cannot allocate costs. The TAGGING.md is a prerequisite for apptio-finops.md.

## Repository State After This Session

```
cloud-architecture/
├── principles/
│   └── AI-FOUNDRY.md              ← NEW (PRN-012)
├── patterns/
│   ├── ai-foundry-hub-project.md           ← NEW
│   ├── ai-foundry-landing-zone.md          ← NEW
│   ├── ai-foundry-models.md                ← NEW
│   ├── ai-foundry-golden-path.md           ← NEW
│   ├── ai-foundry-prompt-flow.md           ← NEW
│   ├── ai-foundry-rag.md                   ← NEW
│   ├── ai-foundry-content-safety.md        ← NEW
│   ├── ai-foundry-cost-management.md       ← NEW
│   ├── ai-foundry-runbook.md               ← NEW
│   ├── ai-foundry-compliance.md            ← NEW
│   ├── ai-foundry-gateway.md               ← NEW
│   ├── apptio-finops.md                    ← NEW
├── standards/
│   └── TAGGING.md                          ← NEW
│   └── FINOPS-RACI.md                      ← NEW
├── diagrams/
│   └── apptio-finops-architecture.html     ← NEW
└── enterprise/
    ├── MONETISATION-STRATEGY.md            ← NEW
    └── SUBAGENT-ASSESSMENT.md              ← NEW
```

**Total new files this session:** 19
**Total repo files across all sessions:** ~75
