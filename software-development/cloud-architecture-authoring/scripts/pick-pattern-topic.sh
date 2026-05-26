#!/bin/bash
# pick-pattern-topic.sh — Cycles through enterprise pattern topics for weekly content generation
# State file tracks position across runs
# Output: topic string to stdout

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_FILE="$SCRIPT_DIR/.pattern-rotation-state"
TOPICS_FILE="/tmp/pattern-topics-$$.txt"

cat > "$TOPICS_FILE" << 'TOPICS'
Cloud Native Security — Zero Trust Networking Patterns on Azure
Azure Policy as Code — Enterprise Governance at Scale
GCP Landing Zone Design — Organisation Hierarchy and Folder Structure
Multi-Cloud Networking — Azure ExpressRoute + GCP Interconnect Topology
Container Strategy — AKS vs GKE vs App Service Decision Framework
Database Modernisation — SQL Managed Instance, Cosmos DB, Cloud SQL, Spanner
API Management Strategy — Azure API Management vs Apigee vs Kong
Observability Operating Model — Datadog, Grafana, OpenTelemetry
Data Platform Architecture — Azure Synapse, BigQuery, Data Lakes
CI/CD Enterprise Standards — Branch Strategy, Environments, Promotion Gates
Disaster Recovery — Azure Site Recovery, GCP DR Patterns, Cross-Region Failover
Secret Management — Key Vault, Secret Manager, Zero-Trust CI/CD
Cost Optimisation Playbook — Rightsizing, Reservations, Spot, Savings Plans
Cloud Migration Strategy — 6Rs Assessment, Wave Planning, TCO Modelling
Backstage Enterprise Adoption — Catalog, Templates, TechDocs, Plugins
Platform Engineering Maturity — Level 1-5 Assessment with Transition Plans
Entra ID Governance — RBAC, PIM, Conditional Access for Cloud
Compliance Automation — Azure Policy, GCP Org Policy, Sentinel Rules
Workload Placement Strategy — Per-Environment Decision Tree
FinOps Maturity Model — Crawl-Walk-Run for Multi-Cloud Cost Management
TOPICS

if [ -f "$STATE_FILE" ]; then
  INDEX=$(cat "$STATE_FILE" 2>/dev/null || echo 0)
else
  INDEX=0
fi

TOTAL=$(wc -l < "$TOPICS_FILE")
TOPIC=$(sed -n "$((INDEX + 1))p" "$TOPICS_FILE")
NEXT_INDEX=$(( (INDEX + 1) % TOTAL ))
echo "$NEXT_INDEX" > "$STATE_FILE"
echo "$TOPIC"
rm -f "$TOPICS_FILE"
