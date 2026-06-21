# Session Reference: Azure Front Door Pattern + CAF/WAF Policy Artefact (2026-06-17)

## Trigger

User asked for "az front door pattern and separate caf/Waf aligned azure policy/blueprint artefact". Pushed to `monty72/cloud-architecture`.

## Deliverables

| File | Repo Path | Type |
|------|-----------|------|
| `AFD-001-azure-front-door.md` | `patterns/` | Build pattern — routing, WAF, caching, Private Link, multi-region failover, cost estimate, runbook |
| `CAF-POL-001-waf-policy-blueprint.md` | `policy-cicd/` | Governance artefact — 6 WAF-aligned initiatives, CAF MG hierarchy, CI/CD pipeline, exemption lifecycle |
| `afd-reference-architecture.png` | `diagrams/` | Architecture diagram — official Azure icons via `diagrams` Python library |

## Key Technique: Paired Artefacts

This session validated the **paired artefact pattern** — producing a build pattern and a governance artefact for the same technology. Both carried their own WAF self-assessment (embedded, not sibling file). The separation by audience (solution architect vs platform engineer) was explicitly documented in both documents' frontmatter.

## Diagram Approach

Used `diagrams` Python library (official Azure icons) rather than HTML/SVG. Multi-region layout (TB direction) with 4 clusters: AFD layer, UK South, UK West, Hub VNet, Management, Identity. ~150 lines of Python. Output: PNG at 200dpi.

## WAF Score Consistency

Both artefacts scored ~89% overall. Sustainability was the weakest pillar in both (~74-78%). This confirms the pattern noted in `references/jetstream-waf-session.md` that sustainability is consistently the hardest pillar to address via documentation alone.

## Repo Push

Commit `b6e6d60` to `git@github.com:monty72/cloud-architecture.git` — SSH auth, no GitHub token. 4 files, 1105 insertions.

## Follow-up Context

After this work, user pivoted to ask about building a "copilot based agent" for use as a cloud architect. Response covered 3 approaches: Hermes + Copilot ACP (recommended), Custom Copilot Extension, Dedicated Hermes Agent. No action taken yet.
