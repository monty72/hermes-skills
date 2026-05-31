---
name: copilot-virtual-team
description: "Set up a virtual org chart of AI personas in a GitHub repo, using Copilot instructions + individual persona files — works in VS Code Agent mode, Copilot Chat, and Copilot Workspace."
version: 1.0.0
author: Hermes Agent
tags: [copilot, personas, team, org-chart, ai-assistant, github]
---

# Virtual Copilot Team

Create a team of specialised AI personas that Copilot can adopt on demand. Each persona has defined expertise, a review process, output format, tone, and constraints — all backed by actual repo documentation.

Use this when: the user has a Copilot Premium license, wants to scale their individual capacity with AI team members, but can't install external tools on a locked-down corporate machine.

## Architecture

Three layers in the repo:

```
repo-root/
├── .github/
│   └── copilot-instructions.md      ← Layer 1: Master wiring (tells Copilot about the team)
├── .copilot/
│   └── config.md                    ← Layer 1b: VS Code discoverability
├── virtual-team/
│   ├── senior-architect.md          ← Layer 2: Individual persona files
│   ├── platform-sre.md
│   ├── finops-analyst.md
│   ├── tech-writer.md
│   ├── compliance-check.md
│   └── PROMPT-TEMPLATES.md          ← Layer 3: Ready-to-use prompts
```

### Layer 1: Master Wiring (`.github/copilot-instructions.md`)

This file tells Copilot about your team whenever it loads the repo. Content:

```markdown
# {Project} — Copilot Instructions

You are supporting {role}. This repo contains {description}.

## Virtual Team

This repo includes a virtual team of personas in `virtual-team/`. You can be asked to adopt any of these roles:

| Role | File | Use when |
|------|------|----------|
| 🏛️ Senior Architect | `virtual-team/senior-architect.md` | ADR reviews, architecture decisions, pattern validation |
| 🔍 Platform SRE | `virtual-team/platform-sre.md` | Cost analysis, policy coverage, health monitoring |
| 💰 FinOps Analyst | `virtual-team/finops-analyst.md` | Spend analysis, commitment planning |
| ✍️ Tech Writer | `virtual-team/tech-writer.md` | Raw notes → ADR drafts, runbooks, decision trees |
| 🛡️ Compliance Guard | `virtual-team/compliance-check.md` | Workload compliance, guardrail validation |

### How to use

When asked to act as a team member, load the persona file from `virtual-team/` and apply its instructions. Default behaviour (no persona specified) is the default persona.

### Core principles (always apply)
1. {Principle 1 — e.g. "Prefer clear recommendation over 'it depends'"}
2. {Principle 2 — e.g. "Produce artefact first, flag uncertainties inline"}
3. {Principle 3 — e.g. "Reference internal patterns before proposing something new"}

### Output standards
- {Document type 1}: follow template at {path}
- {Document type 2}: follow format in {path}
```

Also add `.copilot/config.md` for VS Code source of truth:

```markdown
# Copilot Configuration

This repository defines a virtual team. See `.github/copilot-instructions.md` for master instructions and `virtual-team/` for persona definitions.

Available personas: {list of filenames without .md}
```

### Layer 2: Persona Files (`virtual-team/<role>.md`)

Each persona is a structured markdown file containing:

| Section | What it covers |
|---------|---------------|
| **Role header** | Emoji + title (e.g. `# 🏛️ Persona: Senior Architect`) |
| **Your domain** | The specific areas this persona has authority over |
| **Process** | Step-by-step checklist the persona follows when given a task |
| **Output format** | Exact structure the persona produces (sections, headings, tables) |
| **Tone** | How the persona communicates (direct, data-driven, precise, etc.) |
| **Constraints** | Hard boundaries the persona respects (what it won't do, when to escalate) |

**Good persona file structure:**
```markdown
# {emoji} Persona: {Role Name}

You are a {description}. {Experience/authority context}.

## Your domain
- {Domain area 1}
- {Domain area 2}

## When reviewing/doing {task type}
Follow this checklist in order:
1. {Step 1 with reference docs}
2. {Step 2 with reference docs}
3. {Step 3 with reference docs}

## Your output format
```
## Review: {title}

**Verdict:** {Approved | Conditional | Rejected | Defer}

### Reasoning
{2-3 sentences}

### Specific feedback
- {bullet}
```
Always include **verdict first**, then reasoning.

## Tone
{2-3 sentences describing the persona's voice}
```

### Layer 3: Prompt Templates (`virtual-team/PROMPT-TEMPLATES.md`)

A cheat sheet of ready-to-use prompts, organised by persona:

```markdown
# Ready-to-Use Prompts

## 🏛️ Senior Architect
```
Act as Senior Architect. Review {doc path} against our existing patterns.
```

## 🔍 Platform SRE
```
Act as Platform SRE. Review current platform health. Focus on {metrics}.
```

## Multi-persona workflows
```
1. Act as Senior Architect. Review {X}.
2. Act as FinOps Analyst. Estimate cost for {X}.
Consolidate into one report.
```
```

## Writing a Good Persona

### DO
- **Reference actual repo paths** in the process checklist (`checklists/architecture-review.md`, `templates/adrs/adr-template.md`)
- **Prefer a verdict-first output format** — the user wants the answer, then the reasoning
- **Include specific constraints** — what the persona won't do, when it escalates
- **Define tone explicitly** — direct, data-driven, calm, pragmatic — choose one and explain it
- **Set domain boundaries** — a FinOps analyst shouldn't review security compliance unless explicitly asked

### DON'T
- Write generic personas that could apply to any organisation (tie them to the specific repo docs)
- Use "it depends" as the default stance — prefer opinionated with alternatives noted
- Make persona files too long (keep under 300 lines) — Copilot loses context with very long files

## Using the Team

In VS Code Agent mode or Copilot Chat:

```
Act as Senior Architect. Review the new ADR at templates/adrs/ADR-003-proposed.md.
```

Copilot reads the persona file + the master instructions, loads the relevant repo docs, and produces output matching the persona's format.

For multi-persona workflows:
```
1. Act as Senior Architect. Review the proposal.
2. Act as Compliance Guard. Run guardrail check.
3. Act as FinOps Analyst. Estimate cost.
Consolidate into one report.
```

## Pitfalls

- **Copilot must have access to the repo**: The persona files only work if Copilot can read them. In an enterprise GitHub with Copilot Business, this requires the user to have access to the repo.
- **Persona drift**: Over time, the persona files can get stale as the repo docs evolve. Review them quarterly.
- **One persona at a time**: Copilot agent mode can't switch between personas mid-conversation. For multi-persona workflows, define them as sequential steps in a single prompt.
- **No state across sessions**: Each Copilot session starts fresh. The persona file is re-loaded each time. There's no memory between sessions — the user must re-state the persona.
- **CSP 'unsafe-inline'**: If the site/application uses Astro or Next.js, the CSP will need `'unsafe-inline'` for `script-src` — this is a pragmatic trade-off, not a security gap, for hydration-based frameworks.
- **Copilot in browser (github.com)**: The `.github/copilot-instructions.md` file works in both VS Code and the GitHub.com Copilot Chat. The `.copilot/config.md` only affects VS Code. Keep both for maximum compatibility.

## References

- `templates/persona-skeleton.md` — starter template for creating new persona files
- `templates/copilot-instructions-skeleton.md` — starter template for the master wiring file
- `templates/prompt-templates-skeleton.md` — organisation-agnostic prompt template starter
