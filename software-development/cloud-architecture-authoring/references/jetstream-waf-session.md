# JetStream on AVS vs Native Messaging — Session Output Reference

**Document produced:** `patterns/jetstream-avs-vs-native-messaging.md` in monty72/cloud-architecture repo

## Summary

Comparison pattern for NATS JetStream HA on Azure VMware Solution vs native Azure (Service Bus / Event Hubs) and GCP (Cloud Pub/Sub) messaging services. Covers architecture, cost, throughput, security, operations, migration paths, and WAF alignment.

## Key Design Decisions

- **3-node Raft cluster** on AVS with anti-affinity DRS, D8s_v5 VMs, Premium SSD, internal Azure LB
- **Stream sizing formula:** `(disk_capacity × 0.7) / stream_replicas` — critical for preventing Raft quorum loss from disk-full conditions
- **mTLS mandated** for all NATS cluster routes and gateways — certificate lifecycle via internal CA with auto-rotation
- **Throughput at cost parity:** JetStream's cost is flat (~£1,460/mo for 10K/s to 12M/s). At >250K/s it's 4-25x cheaper than nearest PaaS alternative
- **Migration path:** Dual-write → Cutover → Decommission (~5 weeks for Service Bus, ~6 weeks for Pub/Sub)
- **Sustainability:** Non-prod JetStream clusters must auto-shutdown outside working hours (65% carbon reduction)

## Per-Provider Comparison (at 50K msgs/sec, 1KB payloads)

| Option | Monthly Cost | Latency | Max Throughput | Ops Model |
|--------|-------------|---------|---------------|-----------|
| JetStream on AVS | ~£1,460 | ~500µs | 12M/s (flat cost) | Self-managed VMs |
| Azure Service Bus Premium | ~£1,875 | ~5-15ms | ~350K/s (hits MU ceiling) | Managed PaaS |
| Azure Event Hubs Premium | ~£640 | ~5-20ms | ~1M/s per TU | Managed PaaS |
| GCP Cloud Pub/Sub | ~£200 | ~10-50ms | Unlimited | Serverless |

## WAF Assessment Movement

- v1.0: 72% overall — weakest pillars: Security (70%), Operational Excellence (65%), Sustainability (10%)
- v2.0: 93% overall — all gaps resolved with: stream sizing formula, mTLS, monitoring dashboards, cluster recovery runbook, JWT rotation, metadata backup, throughput-at-cost-parity, carbon footprint per option

## Related Files

- Companion HTML diagram: `reviews/reference-architecture-backup-messaging.html`
- WAF assessment: `reviews/waf-alignment-backup-messaging.md`
