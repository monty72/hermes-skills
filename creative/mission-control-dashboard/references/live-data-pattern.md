# Live Data Dashboard Pattern

## Architecture

A static HTML dashboard that shows real-time system data without requiring a server-side template engine.

```
                  ┌─────────────────────────────┐
                  │   Browser loads index.html   │
                  └──────────┬──────────────────┘
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
            ┌──────────────┐  ┌──────────────┐
            │ fetch(API)   │  │ fallback to  │
            │ succeeds?    │  │ __SNAPSHOT__ │
            └──────┬───────┘  └──────┬───────┘
                   │                 │
                   ▼                 ▼
            ┌──────────────┐  ┌──────────────┐
            │ render(d)    │  │ render(d)    │
            └──────────────┘  └──────────────┘
```

## Key Components

### 1. Static Snapshot (always embedded in HTML)

```javascript
window.__SNAPSHOT_DATA = {
  totalTokens: 7390658,
  estimatedCost: 2.03,
  // ... all fields that render() needs
};
```

This is built at deploy time and ensures the dashboard renders immediately with useful data, even as a static file on Surge.sh or GitHub Pages.

### 2. Live API fetch (optional, backend)

```javascript
async function fetchStatus() {
  try {
    const resp = await fetch(API_URL); // e.g. http://localhost:8081/
    const data = await resp.json();
    render(data);
  } catch {
    render(window.__SNAPSHOT_DATA);
  }
}
```

The API endpoint:
- Must set `Access-Control-Allow-Origin: *` (CORS for cross-origin requests)
- Should set `Cache-Control: no-cache` (real-time data)
- Returns JSON with the same shape as `__SNAPSHOT_DATA`

### 3. render() function (shared)

A single `render(data)` function works for both live and snapshot data. It only consumes the data shape — it doesn't care where the data came from.

## When to Use This Pattern

- **Dashboards** that display system metrics (token usage, uptime, agent status)
- **Status pages** that should work both live and static
- **Any HTML page** that would be nicer with live data but must also work as a static site

## When NOT to Use This Pattern

- When the data is truly static (documentation, blogs)
- When you need real-time server-push (WebSockets would be better)
- When the API requires authentication the browser can't provide

## Implementation Tips

1. **Keep `__SNAPSHOT_DATA` updated** — regenerate it on each deploy so it reflects the latest state
2. **API and HTML on the same origin** — avoids CORS entirely if you serve the HTML from the API server
3. **Granular fallback** — you can fall back per-field rather than wholesale: `data.memPct ?? snapshot.memPct`
4. **Refresh button** — always include `location.reload()` so users can retry the fetch
5. **Show staleness** — display "Updated 2m ago" or "Static snapshot" so users know data freshness
