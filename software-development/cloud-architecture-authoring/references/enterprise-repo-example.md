# Enterprise Cloud Architecture Repository — Example from Sessions

> Produced: May 2026
> Context: Head of Cloud Architecture (horizontal platform team) at Royal Mail (UK regulated logistics enterprise)
> Provider: Azure (primary) + GCP (secondary)
> Repo: github.com/monty72/cloud-architecture
> Sessions: 3 cumulative rounds

## Session 1 — Foundations + Golden Highway
- 51 files, 26 directories
- 10 architecture principles (+ Principle 11: DevEx)
- Full platform lifecycle: landing zone, workload placement, self-service (Backstage/Roadie), golden paths, FinOps, SRE, incident response, security incident, DR/BC, vendor assessment, decommissioning, onboarding, training, communications, ARB charter, audit evidence pack, platform SLA catalogue, cost anomaly script, Azure region matrix
- Golden Highway pattern suite (4 files + 2 ADR examples + 3 reference blueprints)
- 5 tooling patterns: API portal, feature flags, schema registry, IDP architecture, preview environments
- One visual HTML diagram (golden-highway-architecture.html)

## Session 2 — Azure AI Foundry Document Suite
- 12 new documents under patterns/ + 1 new principle
- Principle 12: AI Workloads Use Azure AI Foundry (PRN-012)
| Document | Lines | Key Content |
|----------|-------|-------------|
| ai-foundry-hub-project.md | 502 | Hub-Project resource model, networking, RBAC, Terraform template, pitfalls |
| ai-foundry-landing-zone.md | ~400 | Full Terraform module, private endpoints, Backstage scaffolder, CI/CD |
| ai-foundry-models.md | 604 | 13 model tables, decision flow, prompt caching, quotas, versioning |
| ai-foundry-golden-path.md | ~500 | 5-phase workflow, az CLI commands, prompt patterns, cost model |
| ai-foundry-prompt-flow.md | 983 | GPT-as-judge evaluators, variants, CI/CD integration, tracing |
| ai-foundry-rag.md | 845 | Chunking strategies, hybrid search, embedding dimensions, guardrails |
| ai-foundry-content-safety.md | 940 | Categories/severity, blocklists, red teaming with PyRIT |
| ai-foundry-cost-management.md | ~450 | Pricing tables, PTU sizing, 7 optimisation strategies, MACC |
| ai-foundry-runbook.md | 632 | 8 incident templates with diagnosis CLI commands |
| ai-foundry-compliance.md | ~310 | UK GDPR, data-zone endpoints, audit pack, approved models |
| ai-foundry-gateway.md | ~350 | Multi-provider fallback (Azure→AWS→GCP), LiteLLM config |

## Session 3 — IBM Apptio FinOps + Strategy
- 6 new documents
| Document | Content |
|----------|---------|
| patterns/apptio-finops.md | Full FinOps operating model — 11 integrations, auto-response flows, unit economics, budget management, reservation tracking, anomaly detection, implementation roadmap |
| standards/TAGGING.md | Exhaustive enterprise tagging standard — 9 mandatory tags, 30+ optional, Azure Policy + GCP Org Policy, Apptio-specific tags, tag lifecycle management |
| standards/FINOPS-RACI.md | RACI matrix — 8 roles × 50+ activities across budget, reservations, anomalies, tags, integrations, reporting, strategic |
| diagrams/apptio-finops-architecture.html | Dark-themed 5-layer SVG diagram (Cloud → Apptio → Integration → Consumption → Governance) |
| enterprise/MONETISATION-STRATEGY.md | 5 monetisation angles + revenue projections |
| enterprise/SUBAGENT-ASSESSMENT.md | Sub-agent vs cron job evaluation |

## Combined Metrics (All 3 Sessions)

| Metric | Value |
|--------|-------|
| Total files | ~70+ across 30+ directories |
| Architecture principles | 12 (PRN-001 to PRN-012) |
| Patterns | ~25 (Golden Highway 10 + AI Foundry 12 + Apptio 1 + other 2) |
| Standards | 5 (naming, networking, security, observability + TAGGING.md) |
| RACI matrices | 1 (FINOPS-RACI.md) |
| Architecture diagrams | 2 (golden-highway-architecture.html, apptio-finops-architecture.html) |
| Strategy documents | 2 (MONETISATION-STRATEGY.md, SUBAGENT-ASSESSMENT.md) |
| Cron jobs | 1 (Weekly Cloud Architecture Pattern — every Monday 9am) |
| Estimated total word count | ~80,000+ |
| Visual diagrams | 2 HTML SVG |

## What the User Said

- "Legend" — after the first 12 artefact burst
- "Hero" — after the complete repository was presented
- "My work typically is around the landing zone, workload placement and escalations from other architects" — key signal for horizontal platform
- "I need artefacts before I realise they are needed" — directive for anticipatory writing
- "Do me all the docs for azure ai foundry" — full AI Foundry suite request
- "Could we monetise the skills you are learning" — triggered advisory document
- "Would it be beneficial to set you up another sub agent" — triggered sub-agent assessment

## Key Learnings

1. **Always establish: platform team vs solution architect.** First session mistakenly built workload blueprints. Corrected to: landing zone, workload placement, escalations first.
2. **British English matters.** UK organisations trust correctly-spelled documents (organisation vs organization).
3. **Over-explaining wastes time.** Write opinionated, referenced, move on. The user doesn't need rationale for every decision.
4. **Visual diagrams are high-value.** Both sessions that added an HTML diagram received no complaints. Diagrams were the first thing the user shared with stakeholders.
5. **Subagents hit output limits on large docs.** Documents over ~25KB (enterprise patterns) fail via delegate_task. Write directly with write_file.
6. **Diagram verification matters.** browser_navigate + accessibility tree snapshot is the fastest way to verify SVG diagrams render correctly — faster than debugging SVG coordinates in the writing phase.
7. **Scheduled content needs topic rotation.** Cron jobs for weekly patterns need a pick script + state file, not hardcoded topics.
8. **Advisory documents are valued.** Strategy docs (monetisation, sub-agent assessment) were written at user's request and received no corrections. Users at this level appreciate one-off advisory alongside architecture documentation.
