# Operational Standard Template

> Use this template when writing **any** cloud operational standard (backup, networking, security, observability, tagging, etc.). Every section is optional — pick the ones that fit the domain. The goal is consistency: every standard reads like it came from the same team.

---

## Frontmatter

```markdown
# {Domain} Standard

> **Document ID:** CLOUD-{DOMAIN}-{NNN}
> **Owner:** Head of Cloud Architecture
> **Classification:** Confidential — Internal Use
> **Review Cycle:** Quarterly
```

**ID scheme:** `CLOUD-{DOMAIN}-{NNN}` where DOMAIN is a 2-4 letter code (BCDR, NET, SEC, OBS, TAG, FIN) and NNN is sequential.

---

## 1. Scope

One paragraph defining:
- What this standard covers
- What it explicitly does NOT cover
- Environment applicability (all production/pre-prod always, dev/test partial)

---

## 2. Provider Tables (Multi-Cloud Pattern)

**Pattern:** One combined table per section with a provider column, NOT three separate documents.

```markdown
| Feature | AWS | Azure | GCP |
|---------|-----|-------|-----|
| {native service} | {name} | {name} | {name} |
| {capability} | {limitation} | {limitation} | {limitation} |
```

When a provider **does not** have a native equivalent, say so explicitly — don't hide it. "No native equivalent — use third-party tool" is a decision signal.

---

## 3. Tier / Classification Matrix

Define the tiers before any provider-specific content. This is the **organisation's taxonomy**, not cloud-specific.

```markdown
| Tier / Class | {Metric A} | {Metric B} | Example Workloads |
|--------------|-----------|-----------|-------------------|
| Platinum | < X | < Y | {business-critical} |
| Gold | < X | < Y | {core services} |
| Silver | < X | < Y | {operational} |
| Bronze | < X | < Y | {non-critical} |
```

Then map tiers to provider-specific configurations:

```markdown
**Platinum on AWS:** {policy name, frequency, retention}
**Platinum on Azure:** {policy name, frequency, retention}
**Platinum on GCP:** {policy name, frequency, retention}
```

---

## 4. Provider-Specific Configuration

One subsection per provider. Each subsection covers:

- **Central engine** (the single tool that governs this domain)
- **Service coverage table** (service → method → native tool → cross-region replication)
- **Policy templates** (per tier, per service)
- **Vault / resource structure** (how to name and organise the primitive)
- **Enforcement mechanisms** (Org Policy, Azure Policy, IAM policies)
- **Pricing model** (what's included, what costs extra)

**Key pattern:** The policy templates should be concrete enough to copy-paste into the cloud console or Terraform. "Daily snapshot with 30-day retention" is the minimum — include the frequency, time window, and retention chain.

---

## 5. Cross-Provider Matrix

For domains where the providers interact (e.g. cross-cloud backup, multi-cloud networking):

```markdown
| Scenario | Approach | Tooling | Frequency |
|----------|---------|---------|-----------|
| {scenario A} | {method} | {tools} | {RPO} |
| {scenario B} | {method} | {tools} | {RPO} |
```

**Opinionated stance:** Include a clear "when NOT to do this" section. For backup: "Do NOT use cross-cloud backup as primary DR — RTO is hours to days." For networking: "Do NOT use VPN for steady-state cross-cloud traffic — Cloud Interconnect or Direct Connect."

---

## 6. Testing & Validation

```markdown
| Tier / Frequency | Validation Criteria |
|-----------------|-------------------|
| Monthly | Full restore + app smoke test |
| Quarterly | Restore + data integrity + health check |
| Bi-annual | Verify backup exists + is restorable |
```

Include a checklist template that can be executed by a runbook automation or a junior engineer:

```markdown
- [ ] Service boots successfully
- [ ] Connectivity established
- [ ] Data integrity checksum passes
- [ ] Health endpoint returns 200
- [ ] SSL/TLS valid
- [ ] Monitoring active
- [ ] Cleanup within 48h
```

---

## 7. Monitoring & Alerting

```markdown
| Metric | Source | P1 Threshold | P3 Threshold |
|--------|--------|-------------|--------------|
| {metric name} | {provider tool} | {critical value} | {warning value} |
```

Include per-provider alert config snippets where applicable (CloudWatch, Monitor Alert, Cloud Monitoring).

---

## 8. Cost Benchmark

One comparative table showing cost at a standardised unit:

```markdown
| Scenario | AWS | Azure | GCP |
|----------|-----|-------|-----|
| {baseline config} | ~$X/mo | ~$Y/mo | ~$Z/mo |
```

Note: prices date-stamped. "Prices as of {Month Year} — verify in pricing calculator before procurement."

---

## 9. Compliance Mapping

| Regulation | Requirement | AWS | Azure | GCP |
|-----------|-------------|-----|-------|-----|
| {regulation} | {control requirement} | {evidence source} | {evidence source} | {evidence source} |

Cover the regulations that actually apply to the organisation (GDPR, PCI DSS, ISO 27001, SOC 2, DPA 2018).

---

## 10. Exemption Process

| Step | Detail |
|------|--------|
| 1. File | ServiceNow template `{template-name}` |
| 2. Justify | Document the deviation and why |
| 3. Compensate | What replaces the standard behaviour |
| 4. Timeline | Max 90 days, renewable once with ARB |
| 5. ADR | Attach architecture decision record |
| 6. Owner | Named individual |

**Approval chain by impact:** Lower tiers → Cloud Architect. Middle → HoCA. Higher → ARB + CISO.

---

## 11. Related Documents

| Document | Path | Content |
|----------|------|---------|
| {document name} | {path in repo} | {what it covers} |

---

## Section Decision Notes

| Section | Include When... | Skip When... |
|---------|----------------|--------------|
| Provider-Specific Config | The domain has materially different implementations per cloud | The domain is cloud-agnostic (e.g. naming, tagging format) |
| Cross-Provider Matrix | Workloads span clouds or need data portability | Single-cloud shop |
| Cost Benchmark | Costs vary significantly by provider or config choice | Domain has negligible cost (e.g. naming conventions) |
| Compliance Mapping | Domain touches regulated data (== most domains for enterprise) | Internal-only tooling standard |
| Exemption Process | Always include | Never skip — every standard needs an escape hatch |

---

## Authoring Conventions

1. **British English** — organisation, colour, analyse, centre, licence, practice
2. **Opinionated** — "Do NOT use X" is more useful than "Consider X in some situations"
3. **Decision tables over prose** — compare 3 options in a table, not 3 paragraphs
4. **Costs are date-stamped** — "Prices as of June 2026 — verify before procurement"
5. **Provider columns, not provider documents** — one standard with `AWS | Azure | GCP` columns, not 3 separate docs
6. **Policy templates are copy-pasteable** — include the exact frequency, time, retention chain
7. **Every standard has an exemption process** — no escape hatch means architects will ignore it
8. **Cross-reference to sibling standards** — backup standard links to PLATFORM-DR, which links back
