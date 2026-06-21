# Test-Driven Development — Full Guide

## Overview

Write the test first. Watch it fail. Write minimal code to pass. Refactor.

**Core principle:** If you didn't watch the test fail, you don't know if it tests the right thing.

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Write code before the test? Delete it. Start over.

## Red-Green-Refactor Cycle

### RED — Write Failing Test

One minimal test. Clear name, tests real behavior, one thing:

```python
def test_retries_failed_operations_3_times():
    attempts = 0
    def operation():
        nonlocal attempts; attempts += 1
        if attempts < 3: raise Exception('fail')
        return 'success'
    result = retry_operation(operation)
    assert result == 'success'
    assert attempts == 3
```

**Bad:** Mock-heavy, vague name ("test_retry_works"), tests implementation not behavior.

### Verify RED — Watch It Fail (MANDATORY)

```bash
pytest tests/test_feature.py::test_specific_behavior -v
```

### GREEN — Minimal Code

Simplest code to pass. Cheating is OK: hardcode, copy-paste, duplicate.

### Verify GREEN — Watch It Pass (MANDATORY)

```bash
pytest tests/test_feature.py::test_specific_behavior -v
pytest tests/ -q  # full suite, check no regressions
```

### REFACTOR — Clean Up

Remove duplication, improve names, extract helpers. Keep tests green.

### Repeat

Next failing test for next behavior. One cycle at a time.

## Why Order Matters

- Tests written after code pass immediately → prove nothing
- Tests-first forces edge case discovery before implementing
- Test-after = "what does this do?" Test-first = "what should this do?"

## Red Flags — STOP

- Code before test / test after implementation / test passes first run
- "Keep as reference" / "already spent X hours" / "TDD is dogmatic"
- Any rationalization that skips the RED phase

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I'll test after" | Tests-after prove nothing — they pass immediately. |
| "Already manually tested" | Ad-hoc ≠ systematic. No record, can't re-run. |
| "TDD will slow me down" | TDD is faster than debugging. |

## Integration

When dispatching subagents, enforce TDD in the goal:

```python
delegate_task(
    goal="Implement [feature] using strict TDD",
    context="Follow software-quality TDD workflow: 1) Write failing test 2) Verify it fails 3) Write minimal code to pass 4) Verify 5) Refactor",
)
```
