# Tasks Tab: Drill-Down & Notes Pattern (MC v4 — Python Server)

## Problem (User-Reported, 2026-05-26)

1. **"Under tasks I cannot drill and add notes to tasks waiting for me."** — No Tasks tab existed. Tasks were a missing feature.
2. **"I cannot drill down on the overview tab."** — Overview metric cards used individual `showXDetail()` functions that fetched from the main API endpoint and showed limited data. No unified deep drill-down system.

## Solution: MC v4 Tasks Tab + `/api/drill/` System

### Architecture

The solution uses two complementary systems:

1. **Tasks tab** — A standalone vanilla JS tab with inline expand/collapse, notes input, status buttons, and a new-task form
2. **Deep drill-down** (`/api/drill/:key`) — A unified endpoint that returns structured table data for all drill-down views

---

## System 1: Tasks Tab

### Task Data Model (`~/.hermes/data/mc-tasks.json`)

```json
{
  "id": "task_api_errors",
  "type": "issue",
  "title": "🔴 24 API errors in the last 24h",
  "description": "DeepSeek API returned 24 errors. Check logs...",
  "status": "pending",        // pending | in_progress | done | cancelled
  "priority": "high",         // high | medium | low
  "category": "system",       // system | infra | business | general | feature | maintenance
  "source": "auto",           // "auto" (from observability) | "user" (manually created)
  "created_at": "2026-05-26T15:30:00Z",
  "updated_at": "2026-05-27T00:24:00Z",
  "notes": [
    {"id": "note_abc123", "text": "Spoke to supplier", "created_at": "2026-05-26T16:00:00Z"}
  ]
}
```

### Auto-Generated Tasks

Tasks are automatically generated from the observability snapshot every time the API is called. The `_gen_tasks_from_observability()` function checks:

| Signal | Condition | Priority | Task |
|--------|-----------|----------|-------|
| `errors.apiErrors24h > 0` | API errors exist | high | "🔴 N API errors in the last 24h" |
| `cronTotal > 0` | Cron jobs configured | medium | "📋 Review N active cron jobs" |
| `vmStopped > 0` | Proxmox VMs stopped | medium | "⏹️ N Proxmox VM(s) are stopped" |
| `customerCount == 0` | No OpenClaw customers | medium | "🔄 Onboard first OpenClaw customer" |
| `balance < 2.0` | Balance low | high | "💰 DeepSeek balance low ($X.XX)" |
| Worker `status == 'down'` | Hermes worker idle | low | "🛑 Hermes Worker on OpenCrawl is down" |
| Ollama `models` empty | No models loaded | low | "🦙 Load Ollama models on worker node" |

### Merge Strategy

Auto-generated tasks are re-created on every API call. User-created tasks are stored separately. The merge preserves user notes and status changes on auto-generated tasks:

```python
def _merge_tasks(auto_tasks, stored_tasks):
    # User-created tasks are kept as-is
    user_tasks = [t for t in stored_tasks if t.get("source") != "auto"]
    
    # Auto tasks: preserve notes and status from stored versions
    stored_auto = {t["id"]: t for t in stored_tasks if t.get("source") == "auto"}
    for t in auto_tasks:
        existing = stored_auto.get(t["id"])
        if existing:
            t["notes"] = existing.get("notes", [])
            t["status"] = existing.get("status", "pending")
    
    return merged_auto + user_tasks
```

### API Endpoints

| Endpoint | Method | Purpose | Returns |
|----------|--------|---------|---------|
| `/api/tasks` | GET | List all tasks (auto + user merged) | `{tasks: [...], total: N}` |
| `/api/tasks` | POST | Create a new user task | Created task object |
| `/api/tasks/:id` | GET | Get single task | Full task object |
| `/api/tasks/:id/notes` | GET | Get notes for a task | `{notes: [...]}` |
| `/api/tasks/:id/notes` | POST | Add a note to a task | `{id, text, created_at}` |
| `/api/tasks/:id/status` | POST | Update task status | `{ok, status}` |

### POST Payloads

**Create task:**
```json
{"title": "Task name", "description": "...", "priority": "high", "category": "system", "type": "user-task"}
```

**Add note:**
```json
{"note": "Note text here"}
```

**Update status:**
```json
{"status": "in_progress"}  // pending | in_progress | done | cancelled
```

### UI Structure (Vanilla HTML/JS — No Framework)

The Tasks tab uses inline expand/collapse (not modals):

- **Header row** (always visible): status icon + title + notes count badge + date + source tag
- **Detail panel** (expandable, hidden by default): status buttons, full description, priority/category tags, notes section with inline input

```html
<div class="agent-card task-card" id="task-{id}">
  <div class="agent-card-header" onclick="toggleTaskExpand('{id}')">
    <span>{statusIcon}</span>
    <span>{title}</span>
    <span>{notesCount} notes</span>
    <span>{created}</span>
    <span>{source}</span>
  </div>
  <div class="task-detail" id="detail-{id}" style="display:none">
    <!-- Status buttons -->
    <!-- Description -->
    <!-- Priority / Category tags -->
    <!-- Notes list + Note input -->
  </div>
</div>
```

### Task Filtering (Client-Side)

```javascript
let currentTaskFilter = 'all';
let allTasks = [];

function setTaskFilter(filter) { ... }

function renderTasks() {
  let filtered = [...allTasks];
  if (filter === 'high') filtered = filtered.filter(t => t.priority === 'high' && t.status !== 'done');
  else if (filter !== 'all') filtered = filtered.filter(t => t.status === filter);
  
  // Sort by priority (high first), then by creation date (newest first)
  const sorted = filtered.sort((a, b) => {
    const prio = {high: 0, medium: 1, low: 2};
    return (prio[a.priority] || 1) - (prio[b.priority] || 1) || ...;
  });
  
  count.textContent = `${sorted.length} of ${allTasks.length}`;
  // Render sorted list
}
```

### "New Task" Form

A simple inline form inserted before the task list:

- Title input (required)
- Description textarea
- Priority dropdown (medium/high/low)
- Category dropdown (general/system/infra/business/feature/maintenance)
- Create + Cancel buttons

Submitted via `POST /api/tasks`. On success, form is removed and tasks reloaded.

---

## System 2: Deep Drill-Down (`/api/drill/:key`)

### Problem with the old approach

Before MC v4, every drill-down had its own JS function (`showTokenDetail()`, `showCostDetail()`, `showSystemDetail()`, etc.) that re-fetched `/api` and rendered hardcoded HTML. This was:
- Duplicative (each function had the same fetch-error-render pattern)
- Hard to extend (adding a new drill-down meant a new function)
- Inconsistently detailed (some had 5 rows, some had 3)

### New approach

A single `showDeepDrill(key)` JS function calls `GET /api/drill/:key` which returns structured data:

```python
def get_overview_drill(key):
    return {
        "title": "🔵 Token Usage Breakdown",
        "headers": ["Metric", "Value"],
        "rows": [
            ["Input Tokens", "149.1M"],
            ["Output Tokens", "554.7K"],
            ...
        ]
    }
```

The JS renders it as a clean info-table:

```javascript
async function showDeepDrill(key) {
  openModal('📊 Loading...', '<div>Loading...</div>');
  try {
    const r = await fetch(`/api/drill/${key}`);
    const d = await r.json();
    let h = `<div>${d.title}</div><table>`;
    d.rows.forEach(r => {
      h += `<tr><td>${r[0]}</td><td>${r[1]}</td></tr>`;
    });
    h += `</table>`;
    document.getElementById('modalBody').innerHTML = h;
  } catch(e) { ... }
}
```

### Available drill-down keys

| Key | Data Source | Example Rows |
|-----|-------------|-------------|
| `tokens` | mainAgent.tokens | Input, Output, Total, Cache Hit Rate, Cache Saved, API Calls, Est. Cost, Pricing |
| `cost` | tokens + balance | Est. Cost, Balance, Last Topup, Input Cost, Output Cost |
| `api` | apiMetrics | Total API Calls, Avg Latency, Error Rate, 24h API Errors, Provider |
| `system` | mainAgent | Hostname, IP, Uptime, Memory, Disk, Skills, Cron, Gateway, CPU, OS |
| `worker` | openCrawl | Hostname, IP, Reachable, Uptime, Memory, Disk, Load Avg, Services, Docker, Ollama, Hermes Worker |
| `cron` | (from main API) | Job list with names and statuses |
| `skills` | (from main API) | Categories with counts |
| `errors` | errors.recentErrors | Error list with details |
| `sessions` | sessions | Today, Total, Cron, Skills |
| `pve` | proxmox | Host, Version, Node, CPU, Memory, VMs |
| `ocla_customers` | openClaw | Customers, Online, Health, Key Pool, Configs |

---

## Server-Side Code Patterns

### Task persistence

```python
TASKS_PATH = Path.home() / ".hermes" / "data" / "mc-tasks.json"

def _load_tasks():
    if TASKS_PATH.exists():
        return json.loads(TASKS_PATH.read_text())
    return []

def _save_tasks(tasks):
    TASKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    TASKS_PATH.write_text(json.dumps(tasks, indent=2))
```

### Registering POST routes in `do_POST`

```python
def do_POST(self):
    path = urllib.parse.urlparse(self.path).path
    
    # Auth check
    if not _check_auth(self.headers):
        _require_auth(self)
        return
    
    content_len = int(self.headers.get("Content-Length", 0))
    body = self.rfile.read(content_len) if content_len > 0 else b"{}"
    data = json.loads(body) if body else {}
    
    if path == "/api/tasks" or path == "/api/tasks/":
        # Create task...
        
    if path.startswith("/api/tasks/") and path.endswith("/notes"):
        # Add note...
    
    if path.startswith("/api/tasks/") and path.endswith("/status"):
        # Update status...
```

### UUID generation for task IDs

```python
import uuid
task_id = f"task_{uuid.uuid4().hex[:8]}"
note_id = f"note_{uuid.uuid4().hex[:8]}"
```

---

## Pitfalls

1. **Auto tasks are re-created every call.** If you don't merge with stored versions, user notes and status changes on auto-generated tasks are lost on every refresh. Always use the merge strategy.
2. **Task ID collisions.** Auto-generated tasks use fixed IDs (`task_api_errors`, `task_cron_review`, etc.). User-created tasks use random UUIDs. Never change the auto task IDs without merging old notes.
3. **No DELETE endpoint.** Tasks can only be cancelled, not deleted. If deletion is needed, add `POST /api/tasks/:id/delete`.
4. **Notes are text-only.** No formatting, no attachments, no @mentions. The text is escaped via `escHtml()` before rendering.
5. **Priority sorting is client-side only.** The server returns tasks in no guaranteed order. The JS `renderTasks()` function sorts by priority then date.
6. **Basic Auth applies to task endpoints too.** The API returns 401 if auth is missing, same as the main API. The browser's native auth dialog handles this.

---

## Verification Checklist

- [ ] `GET /api/tasks` returns 200 with merged auto + user tasks
- [ ] `POST /api/tasks` creates a task with `source: "user"` and random UUID id
- [ ] `POST /api/tasks/:id/notes` appends a note to the task's notes array
- [ ] `POST /api/tasks/:id/status` updates task status, returns `{ok, status}`
- [ ] Auto-generated tasks persist user notes across refreshes
- [ ] Tasks tab filter buttons show correct counts
- [ ] Clicking a task header expands/collapses the detail panel
- [ ] `/api/drill/tokens` returns 10 data rows including pricing info
- [ ] `/api/drill/system` returns hostname, IP, uptime, memory, disk, gateway status
- [ ] All 6 Overview metric cards use `showDeepDrill()` not individual functions
