---
name: provider-usage-tracking
description: "Check token usage, API costs, and provider billing info from Hermes Agent logs, session records, and slash commands."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [tokens, usage, billing, costs, monitoring, observability]
    related_skills: [hermes-agent, systematic-debugging]
---

# Provider Usage & Token Tracking

## Overview

Hermes Agent tracks API token consumption per session in the `sessions.json` file and per-API-call in `agent.log`. Most providers also expose billing dashboards. This skill covers all methods for finding out how many tokens you've used and what they cost.

### Method 0: Just Ask

The agent in the current session can usually tell you. When the user asks "how many tokens have you used" or "how many DeepSeek tokens", check the logs and session records proactively — use the log-based method below to answer without asking the user to run commands themselves.

```
User: "How many DeepSeek tokens have you used?"
Agent: *checks agent.log and sessions.json automatically, reports back*
```

This is the fastest path for the user. Only fall back to Methods 1–4 if the agent needs to explain HOW to verify independently.

### Full Methods (from quickest to most thorough)

1. **`/usage` slash command** — in-session overview (any provider)
2. **`sessions.json`** — session-level totals (aggregated per conversation)
3. **`agent.log`** — per-API-call breakdown with cache statistics
4. **Provider billing portal** — authoritative source for all-time usage

---

## Method 1: `/usage` Slash Command

In any running session (CLI or gateway):

```
/usage
```

Shows:
- Input (prompt) tokens
- Output (completion) tokens  
- Cache-read tokens (if applicable)
- Total tokens
- Estimated cost (where provider pricing is known)

**Limitations:**
- Only covers the **current session**
- Cost estimate may show `"unknown"` if the provider isn't in the cost catalog
- Token counts reset between sessions

---

## Method 2: Session Records (sessions.json)

Session-level totals are stored in:

```
~/.hermes/sessions/sessions.json
```

Each session entry has these fields:

| Field | Description |
|-------|-------------|
| `input_tokens` | Total prompt tokens across all turns |
| `output_tokens` | Total completion tokens |
| `cache_read_tokens` | Tokens served from cache |
| `cache_write_tokens` | Tokens written to cache |
| `total_tokens` | input + output (excludes cache) |
| `last_prompt_tokens` | Most recent turn's prompt size |
| `estimated_cost_usd` | Cost estimate |
| `cost_status` | `"known"`, `"unknown"`, or `"partial"` |

**Note:** As of the current config, `total_tokens` may show `0` even when tokens have been used — the counts are updated per API call response, and the aggregator may not persist all updates to JSON. Cross-reference with `agent.log` for accurate totals.

## Proactive Cost Monitoring (Cron-Based)

For ongoing cost vigilance, set up a cron job that checks the provider balance daily and alerts when thresholds are crossed. A no-agent watchdog script is preferred — it runs on schedule, queries the API, and delivers its output verbatim with zero LLM token cost per tick.

### Watchdog Script Pattern

Store at `~/.hermes/scripts/<provider>-monitor.sh`:

```bash
#!/bin/bash
set -e
source ~/.hermes/.env.local 2>/dev/null
export PATH="$HOME/.local/bin:$PATH"
KEY=$(hermes-vault get DEEPSEEK_API_KEY)

BALANCE=$(curl -s --max-time 10 "https://api.deepseek.com/user/balance" \
  -H "Authorization: Bearer $KEY" | python3 -c "
import sys, json
d = json.load(sys.stdin)
bi = d.get('balance_infos', [{}])[0]
print(bi.get('total_balance','error'))
")

BAL_NUM=$(echo "$BALANCE" | awk '{print $1+0}')

echo \"🤖 DeepSeek Monitor\"
echo \"Balance: \$$BALANCE USD\"
echo \"Model: $(grep 'default:' ~/.hermes/config.yaml | head -1 | awk '{print $2}')\"

if (( $(echo \"$BAL_NUM < 0.50\" | bc -l) )); then
    echo \"🚨 CRITICAL — Switching to flash-only (removing Pro fallback)\"
    hermes config set fallback_providers '[]' 2>/dev/null
    echo \"→ Top up at https://platform.deepseek.com/topup\"
elif (( $(echo \"$BAL_NUM < 1.00\" | bc -l) )); then
    echo \"⚠️  WARNING — below \$1.00. ~\$(echo \"$BAL_NUM / 0.02\" | bc) sessions left.\"
elif (( $(echo \"$BAL_NUM < 2.00\" | bc -l) )); then
    echo \"🟡 LOW — below \$2.00\"
else
    echo \"🟢 Healthy — ~\$(echo \"$BAL_NUM / 0.02\" | bc) sessions remaining\"
fi
```

Note: The script uses `hermes-vault get DEEPSEEK_API_KEY` to retrieve the API key at runtime. This only works if the vault passphrase is in `~/.hermes/.env.local` (auto-unlock). Without that, the script will prompt for a passphrase and hang.

### Cron Job Registration

The reference script `scripts/deepseek-cost-monitor.py` provides a full implementation with:
- Daily balance tracking with persistant history (`~/.hermes/data/deepseek-history.json`)
- 7-day average spend calculation
- Spend spike detection (alerts when today's spend > 2× the 7-day avg)
- 30-day spend total
- Auto-escalation: removes Pro fallback when balance < $0.50
- Weekly time-remaining estimate

Register it as a no-agent cron job:

```json
{
  "action": "create",
  "name": "DeepSeek cost monitor",
  "script": "deepseek-monitor.sh",
  "no_agent": true,
  "schedule": "0 9 * * *",
  "prompt": "Daily DeepSeek API balance check."
}
```

Set `no_agent: true` so the script output is delivered verbatim — zero token cost per run. The script runs, checks balance, produces a formatted message, and the cron system delivers it to the home channel.

### Threshold Tiers

Design thresholds as a four-tier escalator. Each tier takes progressively drastic action so the user is never suddenly locked out:

| Balance | Severity | Action |
|---------|----------|--------|
| > $2.00 | 🟢 Healthy | Report with session estimate |
| $1.00–$2.00 | 🟡 Low | Warn, show sessions remaining |
| $0.50–$1.00 | ⚠️ Warning | Urge top-up |
| < $0.50 | 🚨 Critical | Auto-remove expensive fallback models, demand action |

### Quick View

```bash
# Show all session totals
python3 -c "
import json
d = json.load(open('$HOME/.hermes/sessions/sessions.json'))
for k, v in d.items():
    print(f'{v[\"display_name\"]}: in={v[\"input_tokens\"]} out={v[\"output_tokens\"]} total={v[\"total_tokens\"]} cost=\${v[\"estimated_cost_usd\"]:.4f} ({v[\"cost_status\"]})')
"
```

---

## Method 3: Agent Logs (per-API-call detail)

The most granular source. Every API call is logged with exact token counts in:

```
~/.hermes/logs/agent.log
```

### Log Line Format

```
API call #N: model=<model> provider=<provider> in=<prompt_tokens> out=<completion_tokens> total=<sum> latency=<seconds>s cache=<cache_hit>/<total> (<percentage>%)
```

### Summing Token Usage Across a Session

```bash
# Sum all DeepSeek API calls in agent.log
grep "API call.*provider=deepseek" ~/.hermes/logs/agent.log | \
  python3 -c "
import sys, re
input_total = output_total = count = 0
for line in sys.stdin:
    m = re.search(r'in=(\d+) out=(\d+) total=(\d+).*cache=(\d+)/(\d+)', line)
    if m:
        input_total += int(m.group(1))
        output_total += int(m.group(2))
        count += 1
    else:
        # No cache info (first call, cold start)
        m = re.search(r'in=(\d+) out=(\d+) total=(\d+) latency', line)
        if m:
            input_total += int(m.group(1))
            output_total += int(m.group(2))
            count += 1
print(f'API calls: {count}')
print(f'Input: {input_total:,} tokens')
print(f'Output: {output_total:,} tokens')
print(f'Total: {input_total + output_total:,} tokens')
"
```

### By-Provider Breakdown

```bash
# Which providers have been used?
grep "API call #" ~/.hermes/logs/agent.log | grep -oP 'provider=\S+' | sort | uniq -c | sort -rn
```

### Cache Hit Rates

DeepSeek (and Anthropic) report cache hit ratios per call. To get aggregate:

```bash
grep "API call.*cache=" ~/.hermes/logs/agent.log | \
  python3 -c "
import sys, re
total_cache = total_prompt = 0
for line in sys.stdin:
    m = re.search(r'cache=(\d+)/(\d+)', line)
    if m:
        total_cache += int(m.group(1))
        total_prompt += int(m.group(2))
if total_prompt:
    print(f'Cache hit rate: {total_cache/total_prompt*100:.1f}% ({total_cache:,}/{total_prompt:,} prompt tokens cached)')
"
```

---

## Method 4: Provider Billing Dashboards

| Provider | Portal |
|----------|--------|
| DeepSeek | https://platform.deepseek.com/usage |
| OpenRouter | https://openrouter.ai/activity |
| Anthropic | https://console.anthropic.com/usage |
| OpenAI | https://platform.openai.com/usage |
| Google Gemini | https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/usage |
| xAI/Grok | https://console.x.ai/ |

For direct API queries (if you have an API key with billing scope):

```bash
# DeepSeek balance check
curl -s https://api.deepseek.com/user/balance \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY" | python3 -m json.tool
```

---

## Pricing Reference (per million tokens)

| Provider | Model | Input (per 1M) | Output (per 1M) | Cache Hit | Notes |
|----------|-------|----------------|-----------------|-----------|-------|
| DeepSeek | v4-flash | $0.14 | $0.28 | $0.0028 | 1M context, thinking optional |
| DeepSeek | v4-pro | $0.435 | $0.87 | $0.003625 | **75% discount until 31 May 2026**; full price: $1.74/$3.48 |
| Anthropic | claude-sonnet-4 | $3.00 | $15.00 | $0.30 | |
| Anthropic | claude-haiku-3.5 | $0.80 | $4.00 | $0.08 | |
| OpenAI | gpt-4o | $2.50 | $10.00 | $1.25 | |
| OpenAI | gpt-4o-mini | $0.15 | $0.60 | — | |
| Google | gemini-2.5-flash | $0.15 | $0.60 | — | |

Pricing changes frequently. Verify at each provider's pricing page.

> **DeepSeek V4 caveats:** See `references/deepseek-v4-models.md` for thinking-mode gotchas, context caching behavior, and the May 31 discount cliff. **Use `deepseek-chat` in Hermes config** (maps to v4-flash non-thinking mode, avoiding the thinking token trap) or `deepseek-v4-flash` with `reasoning_effort: \"\"`. Avoid `deepseek-reasoner` which forces thinking mode on every call.

### Cost Calculation

```bash
# Calculate cost from a known token count
# DeepSeek v4-flash example: 800K input + 4.5K output
python3 -c "
input_tok = 800000
output_tok = 4500
input_cost = input_tok / 1_000_000 * 0.14
output_cost = output_tok / 1_000_000 * 0.28
cache_savings = input_tok / 1_000_000 * 0.137  # cache hit saves ~$0.14 → $0.0028
print(f'Input:  \${input_cost:.4f}')
print(f'Output: \${output_cost:.4f}')
print(f'Cache hit savings: ~\${cache_savings:.4f}')
print(f'Total:  \${input_cost + output_cost:.4f}')
"
```

---

## Common Pitfalls

5. **`sessions.json` shows 0 tokens.** The aggregator may not persist updated totals to JSON during active sessions. Always cross-reference with `agent.log` for real-time data. After a session ends, the final totals should be accurate. Note: the `total_tokens` field may show `0` even when tokens have been used — this is a known aggregator limitation, not an actual zero-usage situation.

6. **The first API call per session lacks cache info** in its log line. The grep scripts handle this with an alternation regex. If you see a `grep` missing a call, widen the match pattern for lines that contain `in=` and `out=` without requiring `cache=`.

2. **`estimated_cost_usd` shows `0.0` with `cost_status: "unknown"`.** The provider isn't in Hermes's cost catalog. Calculate manually using the pricing table above.

3. **Counting tokens from logs misses the first call.** The first API call in a session doesn't have cache info in its log line. The grep scripts above handle this with an alternation pattern — if you see a missing count, check the regex.

4. **`/usage` only shows the current session.** It does not aggregate across sessions. For cross-session totals, use the log-based method.

5. **Token counts in agent.log are prompt_tokens, not characters.** DeepSeek counts tokens using a proprietary tokenizer — multiplying characters by 0.3-0.4 gives an approximation but exact counts come from the API response.

---

## Verification Checklist

- [ ] `/usage` slash command works in the current session
- [ ] `sessions.json` shows session-level totals (cross-check with log method if showing 0)
- [ ] `agent.log` has `API call #N:` lines with `in=` and `out=` for every turn
- [ ] Cache hit rate is calculable for cache-supported providers (DeepSeek, Anthropic)
- [ ] Provider billing portal confirms the numbers

---

## Quick One-Liners

```bash
# Quick total from logs for the current provider
grep "API call.*provider=deepseek" ~/.hermes/logs/agent.log | grep -oP 'total=\K\d+' | paste -sd+ | bc

# Per-call breakdown (latest first)
grep "API call.*provider=deepseek" ~/.hermes/logs/agent.log | tail -20

# Cost estimate for v4-flash (paste total in+out)
python3 -c "i=807000;o=4500;print(f'\${i/1e6*0.14+o/1e6*0.28:.4f}')"
```

## Reference Files

- `references/deepseek-v4-models.md` — DeepSeek V4 specifics: thinking mode gotcha, context caching, pricing with discount cliff, model aliases, and recommended Hermes config.
