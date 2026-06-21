# Spike — Throwaway Experiments

Validate an idea before committing to a real build.

## When NOT to Use

- Answer is knowable from docs — just research
- Work is production path — use `plan` skill instead
- Idea already validated — jump to implementation

## Core Method

```
decompose → research → build → verdict
     ↑__________________________↓
```

### 1. Decompose

Break the idea into **2-5 independent feasibility questions**:

| # | Spike | GWT | Risk |
|---|-------|-----|------|
| 001 | websocket-streaming | When LLM streams tokens → client receives <100ms | High |
| 002a | pdf-parse-pdfjs | When parsed with pdfjs → structured text | Medium |
| 002b | pdf-parse-camelot | Same question, different approach | Medium |

Order by risk — most likely to kill idea runs first.

### 2. Research (per spike)

- Surface competing approaches with pros/cons/status
- Pick one (or build quick variants for credible ties)
- Use `web_search`, `web_extract`, `terminal` for research

### 3. Build

One standalone directory per spike:
```
spikes/001-websocket-streaming/README.md + main.py
```

**Bias toward something the user can interact with.** Prefer: runnable CLI > HTML page > web server > unit test.

**Default choices:** Use `delegate_task` for parallel comparison spikes.

### 4. Verdict

Each `README.md` closes with:

```markdown
## Verdict: VALIDATED | PARTIAL | INVALIDATED

### What worked / What didn't / Surprises / Recommendation
```

For comparison: head-to-head table with dimensions.

## Frontier Mode

If spikes exist and user asks "what next?", look for:
- Integration risks (tested independently but never together)
- Data handoffs (A's output assumed compatible with B's input)
- Gaps in vision (assumed capabilities unproven)

## Pitfalls

- One successful happy-path run ≠ validated. Test edge cases.
- Avoid Docker, env files, build tools unless the spike requires it.
- Spikes that take 2 days to "clean up" were bad spikes — keep throwaway.
