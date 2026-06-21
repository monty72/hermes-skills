# Simplify Code — Parallel 3-Agent Review & Cleanup

Three focused reviewers run in parallel, findings get aggregated and applied.

## When to Use

User says: "simplify", "simplify my changes", "review my code", "clean up my changes"

**Do NOT auto-run after every edit** — costs 3 subagents. Only when explicitly asked.

## Options

- **Focus**: `simplify focus on efficiency` → run only efficiency reviewer
- **Dry run**: `simplify but don't change anything` → present findings only
- **Scope**: `simplify staged | the last commit | src/foo.py` → narrow diff

## Process

### Phase 1 — Capture the diff

```bash
git diff                                     # uncommitted changes (default)
git diff HEAD                                # includes staged
git diff --staged                            # only staged
git diff HEAD~1                              # last commit
git diff main...HEAD                         # this branch
```

### Phase 2 — Launch three reviewers in parallel

Use `delegate_task` batch mode with ALL THREE goals:

**Reviewer 1 — Code Reuse:** Search codebase for existing functions/patterns the new code duplicates. Flag: re-implemented utilities, manual string/path manipulation where helpers exist.

**Reviewer 2 — Code Quality:** Redundant state, parameter sprawl, copy-paste-with-variation, leaky abstractions, stringly-typed code.

**Reviewer 3 — Efficiency:** Unnecessary work, missed concurrency, N+1 patterns, hot-path bloat, TOCTOU anti-patterns, memory issues.

### Phase 3 — Aggregate & Apply

1. Merge findings, dedupe overlaps
2. Discard false positives
3. Resolve conflicts (correctness > user's focus > readability > micro-perf)
4. Apply fixes with `patch`/`write_file`
5. Verify tests + lint pass
6. Summarize changes

## Pitfalls

- Give the WHOLE diff to each reviewer — cross-file issues hide in gaps
- Don't fan out wider than ~3
- Avoid "while I'm here" rewrites — keep edits scoped to the diff
- Large diffs (>2000 lines) → warn user, offer to scope down
