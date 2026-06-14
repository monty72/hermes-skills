---
mapped_from: session_id=20260524_124448_f6f00a38, captured_at=2026-05-24T12:45
application: Checking DeepSeek token usage from logs during live Telegram session
---

# DeepSeek Session Trace — Worked Example

## Context

During a Telegram conversation, the user asked "How many DeepSeek tokens have you used". The live session (`20260524_124448_f6f00a38`) was running on `deepseek-chat` via `provider=deepseek`.

## Steps Taken

### 1. Check sessions.json first (quick but inaccurate)

```
~/.hermes/sessions/sessions.json
```

Showed `total_tokens: 0`, `last_prompt_tokens: 16512`, `estimated_cost_usd: 0.0`, `cost_status: "unknown"`.

**Lesson:** During an active session, the aggregator may not persist updated totals. Cross-reference with logs.

### 2. Check agent.log for API call lines

```
~/.hermes/logs/agent.log
```

Each turn generates one or more lines like:

```
API call #1: model=deepseek-chat provider=deepseek in=15905 out=9 total=15914 latency=1.8s
API call #2: model=deepseek-chat provider=deepseek in=15920 out=63 total=15983 latency=1.4s cache=15872/15920 (100%)
```

### 3. Parse and sum

Two sessions were active:
- `20260524_124209_78171e` — CLI setup session (23 API calls)
- `20260524_124448_f6f00a38` — Current Telegram session (10 API calls)

Results:

| Session | Calls | Input | Output | Total |
|---------|-------|-------|--------|-------|
| CLI setup | 23 | 573,100 | 3,444 | 576,544 |
| Telegram | 10 | 234,040 | 1,032 | 235,072 |
| **Total** | **33** | **807,140** | **4,476** | **811,616** |

Cache hit rate (from available lines): ~95% on prompt tokens.

### 4. Cost calculation

At DeepSeek pricing ($0.27/1M input, $1.10/1M output):

```
Input:  807,140 / 1,000,000 * $0.27 = $0.218
Output:   4,476 / 1,000,000 * $1.10 = $0.005
Total:                               $0.223
```

Cache reading is billed at $0.07/1M instead of $0.27/1M, but the log line's `in=` already reflects the *actual* billed prompt tokens (after cache deduction), so the cache savings are *already baked in* to the $0.27/M input rate.

### 5. Provider portal URL

https://platform.deepseek.com/usage

## Parsing Script Used

```python
# Extracted from the session — works for any provider
import re

with open('/home/matth/.hermes/logs/agent.log') as f:
    lines = f.readlines()

input_total = output_total = count = 0
for line in lines:
    # With cache info
    m = re.search(r'in=(\d+) out=(\d+) total=(\d+).*cache=(\d+)/(\d+)', line)
    if m:
        input_total += int(m.group(1))
        output_total += int(m.group(2))
        count += 1
        continue
    # Without cache info (cold start first call)
    m = re.search(r'in=(\d+) out=(\d+) total=(\d+) latency', line)
    if m:
        input_total += int(m.group(1))
        output_total += int(m.group(2))
        count += 1

print(f'API calls: {count}')
print(f'Input: {input_total:,}')
print(f'Output: {output_total:,}')
print(f'Total: {input_total + output_total:,}')
```
