# Manage Tabs Architecture (MC V4.1)

The 8 Manage tabs are UI shells with sample data — they're designed to be wired to real backends. This document describes each tab's data shape, state management pattern, and integration points.

## Common Pattern

All Manage tabs follow the same architecture:

```typescript
"use client";

import { useState } from "react";

// 1. Data defined as typed constants or fetched via API
const DATA = [...];  // or fetched via useEffect + fetch()

// 2. UI state (filters, modals, selections)
const [filter, setFilter] = useState("all");

// 3. Render: <div> → header → content grid/list → optional modals
```

## Tab Details

### Tasks (`/tasks`)

**Data shape:**
```typescript
interface Task {
  id: number;
  title: string;
  status: "todo" | "in_progress" | "done" | "blocked";
  priority: "high" | "medium" | "low";
  assignee: string;
  due: string;
}
```

**UI:** Filter bar (all/todo/in_progress/done/blocked) + flat list with status dot + priority color + assignee + due date. Done tasks get `line-through`.

**Integration:** Replace `SAMPLE_TASKS` with a `/api/tasks` endpoint, or connect to Linear/Notion/Trello.

### Content (`/content`)

**Data shape:**
```typescript
interface ContentItem {
  id: number;
  title: string;
  type: "deck" | "doc" | "guide" | "report" | "design" | "research";
  status: "published" | "draft" | "review";
  updated: string;   // relative time
  size: string;      // human-readable
}
```

**UI:** Tab filter (all/published/draft/review) + responsive card grid with type icon + status badge + metadata row.

**Integration:** Connect to filesystem (`~/content/`), Notion DB, or markdown directory.

### Calendar (`/calendar`) — **Cron Schedule**

**Data source:** `/api/cron` (reads `~/.hermes/cron/jobs.json`)

**Data shape:**
```typescript
interface CronJob {
  id: string;
  name: string;
  prompt: string;
  schedule: string;
  enabled: boolean;
  last_run_at?: string;
  last_status?: string;
}
```

**UI:** Flat list with enable/disable dot, schedule badge, prompt preview, last run time, last status. No mock data — this page fetches live from the API.

**User direction:** Calendar was originally a generic event view. The user explicitly redirected it to show **cron jobs** — "calendar = cron". THIS IS INTENTIONAL, not a placeholder. Do NOT replace the cron data with calendar events.

### Projects (`/projects`)

**Data shape:**
```typescript
interface Project {
  id: number;
  name: string;
  status: "active" | "done" | "paused";
  progress: number;   // 0-100
  lead: string;
  tasks: { done: number; total: number };
  icon: string;       // pixel emoji
}
```

**UI:** 2-column card grid with progress bar, status badge, task count.

**Integration:** Connect to Linear projects, GitHub milestones, or a projects API.

### Memory (`/memory`) — **Live MEMORY.md + USER.md**

**Data source:** `/api/memory-file` + `/api/user-file` (reads `~/.hermes/memories/`)

These are Next.js API route handlers (`src/app/api/memory-file/route.ts` and `src/app/api/user-file/route.ts`) that bypass the catch-all proxy and read files from disk directly:

```typescript
import { NextResponse } from "next/server";
import { readFileSync } from "fs";
import { homedir } from "os";

export async function GET() {
  try {
    const path = `${homedir()}/.hermes/memories/MEMORY.md`;
    const content = readFileSync(path, "utf-8");
    return NextResponse.json({ content, path, size: content.length });
  } catch (e) {
    return NextResponse.json({ content: "File not found.", size: 0 });
  }
}
```

**UI:** Tab switcher (MEMORY.md / USER.md) with monospace content viewer, file path header, byte count. No mock data — fetches live from disk.

**User direction:** Memory was originally hardcoded entries. The user explicitly redirected to show actual files — "memory = memory.md". These API routes take precedence over the catch-all `/api/[[...slug]]` route because Next.js matches more specific routes first.

### Docs (`/docs`)

**Data shape:**
```typescript
interface DocEntry {
  id: number;
  title: string;       // filename
  cat: string;         // category
  pages: number;
  updated: string;     // relative time
  icon: string;        // pixel emoji
}
```

**UI:** Category filter bar + table view with columns (name, category, pages, updated).

**Integration:** Scan `~/mission-control/` and `~/.hermes/` for `.md` files, or connect to a docs API.

### Team (`/team`) — **Agents Roster**

**Data source:** `/api` dashboard API

Derives agent status from live fields:
- Worker agents: `data.openCrawl?.reachable`
- OpenClaw: `data.openClaw?.ready`
- Proxmox: `data.proxmox?.reachable`
- Gateway: `data.gateway?.active`

**Data shape:** Hardcoded array of 11 known agents/systems with live status derivation. The status dot updates on each 30-second poll.

**UI:** 3-column card grid with pixel avatar block + type badge (agent/system/infra) + status dot + role description.

**User direction:** Team was originally sample people profiles. The user explicitly redirected to show agents — "team = team of agents". The 11 agents are defined as a typed constant with live status mapping. Do NOT replace with person profiles.

### Visual (`/visual`) — **Agent Office**

**Data source:** `/api` dashboard API (fetched via `fetchDashboard()` with 15-second polling)

**UI:** An "Agent Office" view — not a KPI grid:
- **Top row:** 4 station cards (Hermes Core, OpenClaw, Proxmox Host, Worker Node) with:
  - Pixel icon + live status dot (green/red with shadow)
  - Station label + live subtext (gateway status, customer count, VM count, services)
  - Scanline overlay effect
  - SVG connection lines between stations
- **Bottom row:** 2 smaller utility cards (Cron Scheduler, Skills Library)
- **Runtime summary panel:** Model, provider, tokens, cost

**User direction:** Visual was originally a KPI grid with bar charts. The user explicitly redirected to an **"Agent Office"** — "visual = agent office". This is a visual map of the agent ecosystem, not a chart dashboard.

## Adding Real Data

For each tab, the pattern is:

1. Add an API endpoint in `server.py` (or a new Next.js API route)
2. Update the page's `useEffect` to fetch from the new endpoint
3. Remove sample data constants
4. Add loading/error states

If the data source is the Hermes filesystem (e.g., memory files, doc files), the simplest approach is a new endpoint in `server.py` that reads the relevant path and returns JSON.
