# DeepSeek V4 Model Family

## Models

| Model ID | Description | Context | Concurrency |
|----------|-------------|---------|-------------|
| `deepseek-v4-flash` | Fast/cheap daily driver, thinking optional | 1M tokens | 2,500 req |
| `deepseek-v4-pro` | Deep reasoning, chain-of-thought | 1M tokens | 500 req |

`deepseek-chat` and `deepseek-reasoner` are marked **deprecated** in DeepSeek's API docs (may be removed in a future API version). However, **Hermes Agent can still safely use them today** — `deepseek-chat` maps to v4-flash in **non-thinking mode**, which is the preferred daily-driver config because it avoids the thinking-mode token trap described below.

When Hermes sends `model: deepseek-chat`, the DeepSeek API returns direct responses with no hidden reasoning token waste. If the raw name `deepseek-v4-flash` is used, Hermes must explicitly handle the `thinking: {"type": "disabled"}` parameter — not every code path does this correctly.

**Recommendation:** Use `deepseek-chat` in Hermes config.yaml for now (it maps to v4-flash non-thinking). Only migrate to the raw alias when Hermes can configure thinking mode per-model or the deprecated alias is actually removed. Avoid `deepseek-reasoner` — it maps to v4-flash thinking and burns tokens on invisible reasoning.

## Thinking Mode — The Token Trap

Both v4-flash and v4-pro default to **thinking mode**. In this mode:

- The model produces `reasoning_content` (chain-of-thought)
- `content` may be empty while reasoning is in progress
- `reasoning_tokens` count against `max_tokens` budget
- With small `max_tokens`, reasoning can consume the entire budget, leaving no room for the actual response

### Empirical Evidence

**v4-flash with thinking enabled (default), max_tokens=100, prompt="Hi":**
- `completion_tokens`: 100 (all `reasoning_tokens`)
- `content`: empty
- `finish_reason`: `"length"`  (ran out of budget before producing output)
- Reasoning shown: Chinese chain-of-thought about greeting etiquette

This is wasteful — the user never sees the reasoning, and tokens are burned invisibly.

### How to Disable Thinking

**In config.yaml** (recommended for daily use):
```yaml
agent:
  reasoning_effort: ""   # empty string disables thinking
```

**In API calls directly:**
```json
{
  "thinking": {"type": "disabled"}
}
```

**When to enable:** Development tasks requiring complex decomposition, multi-step planning, or debugging.

### Cost Impact

With thinking enabled, a simple "Hello" response burns ~15 reasoning tokens before emitting any content. Over a long session, this adds up to significant wasted spend. With thinking disabled, responses are direct and token-efficient.

## Context Caching

DeepSeek v4 supports **automatic prompt caching** with dramatically lower cache-hit pricing:

| Model | Cache Hit (per 1M) | Cache Miss (per 1M) | Savings vs Miss |
|-------|--------------------|--------------------|---------------- --|
| v4-flash | $0.0028 | $0.14 | **98%** |
| v4-pro | $0.003625 | $0.435 | **99%** |

The Hermes system prompt, memory, and repeated prefix content are cached automatically. This means **most of the input cost is eliminated** in long conversations — the cache-hit rate is the relevant price for practical usage.

## v4-pro Discount Cliff

DeepSeek v4-pro launched with a **75% discount** from the target price:

| | Discount (until 31 May 2026) | Full price (after) |
|---|---|---|
| Input | $0.435/M | $1.74/M |
| Output | $0.87/M | $3.48/M |

After May 31, v4-pro becomes 4× more expensive. v4-flash pricing is permanent.

## Recommended Config

For Hermes Agent (cost-effective setup):

```yaml
model:
  default: deepseek-v4-flash      # daily driver
  provider: deepseek
  base_url: https://api.deepseek.com/v1

fallback_providers:
  - provider: deepseek
    model: deepseek-v4-pro         # auto-escalates when rate-limited

agent:
  reasoning_effort: ""             # disable thinking for flash
  max_turns: 90                    # 1M context can handle deep sessions
```

## Budget Estimates

At v4-flash pricing with context caching:

- 20-turn session (100K input + 20K output): **~$0.02**
- 50-turn deep session (500K input + 100K output): **~$0.05**
- $2.87 balance → **~140 sessions**

At v4-pro discounted pricing:
- 20-turn session: **~$0.06**
- After May 31: **~$0.24**
