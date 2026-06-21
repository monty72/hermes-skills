---
name: software-quality
description: "Software quality methodologies and workflows — test-driven development, systematic debugging, parallel code simplification, pre-commit verification, codebase inspection, and spiking/feasibility experiments."
tags: [quality, tdd, debugging, code-review, testing, methodology, spike, refactoring]
related_skills: [github, plan, writing-plans, autonomous-coding-agents]
---

# Software Quality — Methodologies & Workflows

Test-driven development, systematic debugging, code review, simplification, spike experiments, and codebase analysis.

## When to Use

- User wants TDD discipline enforced
- Debugging a complex issue
- User says "simplify" or "clean up my changes"
- Pre-commit verification needed
- Codebase size/language analysis
- Validating an idea before building

## 1. Test-Driven Development (TDD)

See `references/test-driven-development.md` for full guide. Core cycle:

```
RED → Write failing test → Watch it fail → GREEN → Write minimal code → Watch it pass → REFACTOR → Clean up
```

**Iron law:** No production code without a failing test first. If you didn't watch the test fail, you don't know if it tests the right thing.

## 2. Systematic Debugging

See `references/systematic-debugging.md` for full 4-phase process:

1. **Phase 1: Root Cause** — Read errors, reproduce, check changes, trace data flow
2. **Phase 2: Pattern Analysis** — Find working examples, compare references
3. **Phase 3: Hypothesis & Testing** — One variable at a time, scientific method
4. **Phase 4: Implementation** — Create regression test, fix root cause, verify

**Iron law:** No fixes without root cause investigation first. After 3 failed fixes, question the architecture.

## 3. Simplify Code — Parallel Review

See `references/simplify-code.md` for full workflow. Launch 3 focused reviewers in parallel via `delegate_task`:

- **Reviewer 1 (Code Reuse)** — Finds duplicated functionality
- **Reviewer 2 (Code Quality)** — Finds redundancy, parameter sprawl, leaky abstractions
- **Reviewer 3 (Efficiency)** — Finds unnecessary work, missed concurrency, N+1 patterns

Trigger when user says "simplify", "review my changes", or "clean up".

## 4. Pre-Commit Verification

See `references/requesting-code-review.md` for the full verification pipeline:

1. Get the diff
2. Static security scan (secrets, injection, eval)
3. Baseline tests and linting (stash, run, compare)
4. Independent reviewer subagent via `delegate_task`
5. Auto-fix loop (up to 2 cycles)

Run before any `git commit` or `git push`.

## 5. Codebase Inspection

```bash
pip install pygount
cd /path/to/repo
pygount --format=summary --folders-to-skip=".git,node_modules,venv,__pycache__,.cache,dist,build" .
```

See `references/codebase-inspection.md` for full detail: language breakdown, file counts, code vs comment ratios.

## 6. Spike — Throwaway Experiments

See `references/spike.md` for full workflow. Use when validating an idea before committing to a real build.

1. Decompose into 2-5 feasibility questions (Given/When/Then)
2. Research competing approaches
3. Build minimal prototypes (standalone dirs in `spikes/`)
4. Verdict: VALIDATED | PARTIAL | INVALIDATED

## References

- `references/test-driven-development.md` — Full TDD guide: cycles, rationale, red flags, common rationalizations
- `references/systematic-debugging.md` — Full debugging process: 4 phases, troubleshooting tables
- `references/simplify-code.md` — Parallel 3-agent cleanup workflow
- `references/requesting-code-review.md` — Pre-commit verification pipeline with static scan + reviewer subagent
- `references/codebase-inspection.md` — pygount LOC analysis
- `references/spike.md` — Spike experiment methodology with Given/When/Then verdicts
