# Next.js Tasks Page — API-Backed Expandable Tasks + Notes

## Context

The MC V4 Tasks page at `src/app/tasks/page.tsx` was rewritten from a **hardcoded ALL_TASKS array** to a **live API-backed** implementation that fetches from `/api/tasks` (proxied to the Python backend at port 8081).

**User complaint:** "Under tasks I cannot drill and add notes to tasks waiting for me."

## Architecture

```
TasksPage (use client)
├── State: tasks[], loading, statusFilter, projectFilter
├── expandedTask: string | null   // which task is currently expanded
├── noteInputs: Record<string, string>  // per-task note text
├── newTaskOpen: boolean + newTask form state
│
├── useEffect → fetchTasks() from /api/tasks
├── Filters: status (all/todo/in_progress/done/blocked) + project
├── Task card → onClick toggleExpand(id)
│   └── Expanded panel:
│       ├── Description (pre-wrap)
│       ├── Status buttons (pending/in_progress/done/blocked)
│       │   └── onClick → updateTaskStatus(id, status)
│       └── Notes section
│           ├── Existing notes (from task.notes[])
│           ├── Text input + Add button
│           └── onKeyDown Enter → addTaskNote(id, text)
└── + New button → inline form (title, description, priority, category)
    └── createTask(data)
```

## API Functions (from `src/lib/api.ts`)

```typescript
export async function fetchTasks(): Promise<TaskListData>
export async function addTaskNote(taskId: string, note: string): Promise<any>
export async function updateTaskStatus(taskId: string, status: string): Promise<any>
export async function createTask(data: { title, description?, priority?, category? }): Promise<TaskItem>
```

All POST calls send `method: "POST"`, `Content-Type: application/json`, and proxy through the Next.js `/api/[[...slug]]` catch-all to the Python backend.

## Task Data Model (from Python backend)

```json
{
  "id": "task_api_errors",
  "title": "🔴 24 API errors in the last 24h",
  "description": "Full error traceback...",
  "status": "pending",
  "priority": "high",
  "category": "system",
  "source": "auto",
  "created_at": "2026-05-27T00:00:00Z",
  "notes": [
    {
      "id": "note_abc123",
      "text": "Checking logs now",
      "created_at": "2026-05-27T00:01:00Z"
    }
  ]
}
```

Note: The Python backend maps `status` as "pending" | "in_progress" | "done" | "cancelled". The Tasks page frontend remaps "pending" → "todo" for filter purposes.

## Per-Task Note Input Pattern

Each task has its own note input managed by `noteInputs: Record<string, string>` state. When the Add button is clicked:

```typescript
const handleAddNote = async (taskId: string) => {
  const text = noteInputs[taskId]?.trim();
  if (!text) return;
  await addTaskNote(taskId, text);
  setNoteInputs((prev) => ({ ...prev, [taskId]: "" }));
  await loadTasks();        // Re-fetch to get updated state
  setExpandedTask(taskId);  // Keep it expanded after reload
};
```

The `setExpandedTask(taskId)` after `loadTasks()` is critical — otherwise the re-render collapses the task panel, leaving the user confused.

## Task Filter Mapping

The frontend shows 5 filter statuses, mapped from the backend's 4 statuses:

| Frontend Filter | Backend Status | Notes |
|----------------|----------------|-------|
| All | any | No filter |
| ⏳ Pending | `pending` | Mapped to "todo" for display |
| 🔄 In Progress | `in_progress` | Direct |
| ✅ Done | `done` | Direct |
| 🚫 Blocked | `cancelled` | Mapped for UX clarity |

The project filter is derived from the `category` field:
- "infra" → "Infra"
- "system" → "Observability"
- "business" → "Managed SaaS"
- "feature" | "maintenance" → "MC V4"
- "energy" → "Energy"
- default → "General"

## Key State Management Details

- **`loadTasks` is wrapped in `useCallback`** with empty deps to prevent infinite re-renders. The function is defined once and passed as the initial `useEffect` dep.
- **Status update buttons** show the active one with a filled style, others with subtle border:
  ```typescript
  const isActive = task.status === s;
  `${isActive ? activeStyles : "border-lo-border text-lo-text-muted hover:border-lo-primary/30"}`
  ```
- **Notes count badge** shown on collapsed task header when notes exist: `task.notes.length note(s)`
- **Source badge** shows "🤖 auto" for auto-generated tasks, "👤 manual" for user-created

## Pitfalls

1. **TypeScript type error with object literal index access.** The priority sort map `{ high: 0, medium: 1, low: 2 }` fails at build time unless typed as `Record<string, number>`. Without this, Next.js build exits with code 1.

2. **Task panel collapse after note add.** After `addTaskNote` completes, `loadTasks()` re-fetches all tasks and React re-renders the list. The expanded task ID must be re-set: `setExpandedTask(taskId)` after `await loadTasks()`.

3. **`getProject` function must handle all categories gracefully.** The backend auto-generates tasks with categories like "infra", "system", "business" — each must map to a project label. Unmapped categories fall through to "General". No categories should produce `undefined`.

4. **Filter matching must account for backend status names.** The backend uses "pending" not "todo". The filter must remap: `const mapped = t.status === "pending" ? "todo" : t.status`.
