# Systematic Debugging — 4-Phase Root Cause Process

## Overview

Random fixes waste time. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

## The Four Phases

### Phase 1: Root Cause Investigation (NO fixes yet)

1. **Read error messages** — Don't skip. Read stack traces, note line numbers.
2. **Reproduce consistently** — Can you trigger it reliably? Exact steps?
3. **Check recent changes** — `git log --oneline -10`, `git diff`
4. **Gather evidence** — Log what enters/exits each component boundary
5. **Trace data flow** — Where does bad value originate? Trace upstream to source

**Complete when:** You understand WHAT and WHY.

### Phase 2: Pattern Analysis

1. Find working examples in the same codebase
2. Compare against references (read completely, don't skim)
3. Identify every difference between working and broken
4. Understand dependencies

### Phase 3: Hypothesis & Testing

1. State clearly: "I think X is root cause because Y"
2. Make the SMALLEST possible change to test
3. One variable at a time
4. Didn't work? Form NEW hypothesis. Don't pile on fixes.

### Phase 4: Implementation

1. Create failing test case (use TDD)
2. Implement single fix at root cause
3. Verify: run regression test + full suite
4. **Rule of Three:** After 3 failed fixes, STOP and question architecture

## Red Flags

- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "One more fix attempt" (after 2+)
- Each fix reveals a new problem in a different place → architectural issue

## Quick Reference

| Phase | Key Activities | Success |
|-------|---------------|---------|
| 1. Root Cause | Read errors, reproduce, check changes, trace data | Understand WHY |
| 2. Pattern | Find working examples, compare | Know what's different |
| 3. Hypothesis | Form theory, test minimally | Confirmed or new theory |
| 4. Implementation | Regression test, fix root cause, verify | Bug resolved, tests pass |
