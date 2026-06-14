# Backup & DR Standard — Session Output Reference

**Document produced:** `standards/backup-dr-standard.md` in monty72/cloud-architecture repo

## Summary

Multi-cloud backup & DR standard (CLOUD-BCDR-001) covering Azure, AWS, and GCP using native tooling only. v2 was iterated after a WAF self-assessment identified 6 gaps.

## Key Design Decisions

- **Backup vs DR split:** Backup (point-in-time data recovery from corruption/deletion) and DR (workload failover for availability) are separate sections with separate mechanisms. They share the same RTO/RPO tiers but use different tooling.
- **Data classification → policy mapping:** Every workload's backup tier is determined by its `data-classification` tag (Public/Internal/Confidential/Restricted). Enforcement via Azure Policy / AWS SCP / GCP Org Policy.
- **Policy-as-code mandate:** All backup plans, vaults, and ASR replication policies must be defined as code and deployed via CI/CD. No manual portal creation permitted.
- **Chargeback model:** Three models documented — direct tag-based, proportional by usage, flat per-tier. Monthly backup cost reports sent to each budget owner.
- **Restore SLA defined:** Platinum < 15min, Gold < 4h, Silver < 24h, Bronze < 72h, measured from incident declaration to health endpoint 200.

## Key Numbers

- RTO/RPO tiers: Platinum <5min/<15min through Bronze <7d/<72h
- Testing cadence: Platinum monthly restore + quarterly DR drill, Bronze annual
- Retention: 35d PITR (Confidential), 30d (Internal), cold at 7d (Silver+), archive at 180-365d
- Cost: ~$10-12.50/mo per 100GB for full stack (hot + cold + DR)
- WAF score: 71% → 91% after v2 gap resolution

## Per-Provider Highlights

| Provider | Key Distinction |
|----------|----------------|
| **Azure** | GRS vault = zero-egress replication to paired region. Cheapest cross-region option. |
| **AWS** | Backup Vault Lock in Compliance mode (irreversible, 1yr lock). Glacier/Deep Archive lifecycle. |
| **GCP** | Backup DR Service with Governance mode. CMEK required for Confidential+. |

## Related Files

- Companion HTML diagram: `reviews/reference-architecture-backup-messaging.html`
- Cross-reference: `business-continuity/PLATFORM-DR.md`
- WAF assessment: `reviews/waf-alignment-backup-messaging.md`
