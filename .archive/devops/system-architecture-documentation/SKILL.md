---
name: system-architecture-documentation
description: "Maintain and update architecture documentation (ARCHITECTURE.md, LLD.md, diagrams) when the system changes. Covers the full pattern: assess what changed, update all three doc layers, and commit."
version: 1.0.0
author: Hermes Agent
license: MIT
dependencies: []
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [architecture, documentation, diagrams, lld, infrastructure]
    related_skills: [architecture-diagram, modern-astro-ci-cd-setup, managed-agent-service, tesla-energy-dashboard, cloud-architecture-authoring]
---

# System Architecture Documentation

## Overview

When the system grows — new services, config changes, tunnels, API endpoints, credentials, provisioning pipelines — the architecture documentation needs to stay in sync. This skill covers the full workflow:

1. **ARCHITECTURE.md** — Concise one-page system overview (purpose: quick reference)
2. **LLD.md** — Full low-level design (purpose: implementer's guide, 300+ lines)
3. **Architecture Diagram** — Dark-themed SVG HTML (purpose: visual map for onboarding/presenting)

## When to Use

Any of these trigger conditions:
- A new service or daemon was installed (API server, tunnel, database, message bus)
- A new repo or project was created (Astro site, Flask app, provisioning system)
- A new subdomain or Cloudflare tunnel was added
- A port changed or a new port was opened
- A credential system changed (vault, new tokens, new git auth)
- A provisioning/managed-agent flow was built
- A cron job or background service was added
- The user says "diagram the whole system" or "update the architecture docs"
- A new physical device joined the network (Powerwall, router, HA instance)
- A new tier/customer type was added to a managed service

## Workflow

### 1. Gather Current State

Before writing anything, inventory ALL systems. Use `delegate_task` with parallel tasks for speed:

**Task A — Managed-Agent / Provisioning System:**
```
Goal: Gather managed-agent provisioning system state
Toolsets: terminal, file
Context: ~/managed-agent/ directory, scripts/, configs/, skills/
```
Check: scripts, config templates, customer directories, LLM key pools, bot pools, platform configs.

**Task B — Hermes Agent Configuration:**
```
Goal: Gather Hermes Agent config, skills, cron, state
Toolsets: terminal, file
Context: ~/.hermes/ directory — config.yaml, cron, skills, scripts, auth
```
Check: config version, model provider, connected platforms, gateway state, cron jobs, script files, memory files.

**Task C — Public Website / Dev Site:**
```
Goal: Gather dev-site / public website state
Toolsets: terminal, file
Context: ~/dev-site/ — Astro pages, GitHub Actions, Vercel, package.json
```
Check: all page routes, React islands, API integrations, CI/CD workflows, DNS records.

**Task D — Energy / Hardware / Network:**
```
Goal: Gather energy stack, network topology, hardware
Toolsets: terminal, file
Context: ~/energy-dashboard/, ~/skill-marketplace/, listening ports, HA config
```
Check: Flask ports, Tesla token status, Powerwall IP, Home Assistant URL + entity count, cloudflared tunnel config.

### 2. Generate All Three Docs

After gathering, write three files into `~/dev-site/` (or the repo root):

**ARCHITECTURE.md** — Keep it concise (50-80 lines):
```
# Project Name — Architecture

[ASCII art overview showing all services and connections]
[List of pages/routes with tech]
[Short stack section]
[Short APIs section]
[Short host/network section]
```

**LLD.md** — Full low-level design (300-500 lines):
```
# Project Name — Low-Level Design

> Author, date, domain, stack

## Table of Contents

## 1. Architecture Overview
  - ASCII art flow diagram (user → CDN → server + tunnel path)
  - Data flow section
  - Network topology table

## 2. Repository Structure
  - Folder tree (src/, scripts/, configs/, etc.)
  - Authored files outside repo (cloudflared, scripts, etc.)

## 3. Frontend
  - Why Astro (or chosen framework)
  - Page architecture pattern
  - Route table (path → file → type → interactivity)
  - Design system

## 4. CI/CD Pipeline
  - GitHub Actions workflows
  - Pipeline timings
  - Secrets table

## 5. Hosting & DNS
  - DNS records table
  - Vercel config
  - Cloudflare tunnel details

## 6. API Backend(s)
  - Endpoint table (method, path, description, data source)
  - Auth mechanism
  - Caching strategy

## 7. Hermes Agent Ecosystem
  - Hermes Agent
  - Managed-Agent provisioning
  - Subagent/delegation architecture
  - Skills library
  - Cron jobs
  - Credential vault
  - Secret management

## 8. Energy Monitoring Stack
  - Powerwall → Tesla API → Flask → Tunnel flow
  - EV charging
  - Home Assistant

## 9. Development Workflow
  - Adding a page
  - Adding a React island
  - Adding an API endpoint
  - Provisioning a new customer

## 10. Security Considerations
  - Table: concern → mitigation

## 11. Cost Breakdown
  - Table: service → tier → cost

## 12. Roadmap & Future Work
  - Near/medium/long-term goals
```

**montygroup-architecture.html** — Dark-themed SVG diagram using the `architecture-diagram` skill. Load `skill_view(name="architecture-diagram", file_path="templates/template.html")` first for the exact HTML/CSS/SVG structure, then produce the full file with:
- Every component type (frontend, backend, database, cloud, security, external)
- All connections with labeled arrows
- Legend with all component types
- Three info cards below the diagram
- Self-contained, no JS, inline CSS

### 3. Verify

- [ ] `ARCHITECTURE.md` renders cleanly in any markdown viewer
- [ ] `LLD.md` has complete table of contents
- [ ] Architecture HTML file opens in browser with all components
- [ ] All three files committed and pushed to git

### 4. Commit

```bash
cd ~/dev-site
git add ARCHITECTURE.md LLD.md montygroup-architecture.html
git commit -m "docs: update system architecture — [brief summary of changes]"
git push
```

## Pitfalls

1. **Subagent summaries are self-reports** — subagents claim things without verifying. For operations with external side-effects (HTTP requests, file creation at shared paths), require the subagent to return verifiable handles (absolute paths, HTTP 200s) and verify them yourself.

2. **Don't duplicate information** — ARCHITECTURE.md is the overview. LLD.md is the deep reference. The diagram is the visual layer. Each should contain a unique subset of info. Cross-reference across them rather than repeating.

3. **Outdated LLD sections** — When you edit only the diagram, the LLD.md stays stale. Always update all three together.

4. **Hidden processes** — `ss -tlnp` shows listening ports but not background services that don't bind ports (cron jobs, tunnel watchdogs, HA integrations). Check `cronjob action='list'` and `process(action='list')` too.

5. **Overly-large SVG** — The diagram viewBox must accommodate all components. If adding many new services, increase the SVG `viewBox` dimensions and check the legend placement stays below the lowest boundary box.

6. **Git credential helper** — The git credential helper reads `GITHUB_TOKEN` from the encrypted vault. Pushing should work without embedding the token in the remote URL. If git asks for auth, run `hermes-vault get GITHUB_TOKEN` and check the token is still valid.

## Reference Files

- `references/montygroup-full-architecture-2026-05.md` — The architecture diagram HTML, ARCHITECTURE.md, and LLD.md from the May 2026 full-system audit. Use as a concrete example of the output shape.
