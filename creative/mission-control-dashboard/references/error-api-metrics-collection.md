# Error & API Metrics Collection Pattern

## Error Detail Collection

The observability collector collects the **last 10 error lines** from `~/.hermes/logs/agent.log` for drill-down display. This gives users context about what actually went wrong, not just counts.

### Collector Pattern (Python)

```python
def get_agent_errors():
    errors = 0
    api_errors = 0
    error_details = []

    for line in reversed(AGENT_LOG.read_text().splitlines()):
        is_error = "ERROR" in line or "Traceback" in line
        if is_error:
            errors += 1
        # Collect last 10 unique error descriptions
        if len(error_details) < 10:
            clean = line.strip()
            if len(clean) > 200:
                clean = clean[:200] + "..."
            error_details.append(clean)

    return {
        "totalErrors24h": errors,
        "apiErrors24h": api_errors,
        "recentErrors": error_details,  # Last 10 lines, truncated to 200 chars
    }
```

### What Gets Collected

| Error type | Example | Classification |
|---|---|---|
| `ERROR` in log line | `[Telegram] Failed to send: Timed out` | ERROR (red) |
| `Traceback` | `Traceback (most recent call last):...` | ERROR (red) |
| `WARNING` with tool error | `Tool terminal returned error` | WARNING (amber) |
| API call with error status | `status=4xx` or `status=5xx` | API ERROR (amber) |

### Dashboard Display

The error log drill-down modal shows:
- Total error count (24h) — green if 0, red if > 0
- API error count (24h) — amber if > 0
- Each error displayed in a colored card: red for ERROR/Traceback, amber for WARNING

Key: `escHtml()` must be used to safely render log lines that may contain HTML special characters.

## API Provider Breakdown

The collector parses `provider=` from agent.log API call lines to build a provider usage breakdown:

```python
providers = {}
for line in AGENT_LOG.read_text().splitlines():
    if "API call" in line:
        pm = re.search(r'provider=(\S+)', line)
        if pm:
            prov = pm.group(1).rstrip(',').rstrip("'")
            providers[prov] = providers.get(prov, 0) + 1
```

Returns a dict like: `{"deepseek": 169}`

### Dashboard Display

The API breakdown drill-down shows:
- Provider bar chart with percentage bars
- Color coding: deepseek=blue, openai=green, anthropic=purple, groq=amber
- Total calls, avg latency, error rate, input/output tokens, cache rate, cost

## API Endpoint Pattern for Error Data

The `/api/errors` endpoint reads from the observability snapshot (not the raw log — the collector already parsed it):

```python
if path == "/api/errors":
    snap = json.loads(SNAPSHOT_PATH.read_text())
    ma = snap.get("mainAgent", {})
    errs = ma.get("errors", {})
    self.wfile.write(json.dumps({
        "totalErrors24h": errs.get("totalErrors24h", 0),
        "apiErrors24h": errs.get("apiErrors24h", 0),
        "recentErrors": errs.get("recentErrors", []),
    }).encode())
```

This avoids parsing agent.log on every API request — the 5-minute cron collector does the heavy lifting.
