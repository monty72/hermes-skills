# Pre-Commit Code Verification — Independent Reviewer Pipeline

Automated verification pipeline before code lands.

## When to Use

- After implementing a feature or bug fix, before `git commit` or `git push`
- When user says "commit", "push", "ship", "done", "verify"

**Skip:** documentation-only changes, pure config tweaks.

## Step 1 — Get the diff

```bash
git diff --cached  # staged changes
# If empty: git diff, then git diff HEAD~1 HEAD
```

## Step 2 — Static security scan

```bash
# Secrets
git diff --cached | grep "^+" | grep -iE "(api_key|secret|password|token)\s*=\s*['\"][^'\"]{6,}['\"]"
# Shell injection
git diff --cached | grep "^+" | grep -E "os\.system\(|subprocess.*shell=True"
# Dangerous eval/exec
git diff --cached | grep "^+" | grep -E "\beval\(|\bexec\("
# SQL injection
git diff --cached | grep "^+" | grep -E "execute\(f\"|\.format\(.*SELECT"
```

## Step 3 — Baseline tests & linting

Detect project, run tests. Compare against baseline (stash → run → pop). Only NEW failures matter.

## Step 4 — Self-review checklist

- [ ] No hardcoded secrets, API keys
- [ ] Input validation on user data
- [ ] Parameterized SQL queries
- [ ] Error handling on external calls
- [ ] No debug print/console.log
- [ ] Tests for new code

## Step 5 — Independent reviewer subagent

```python
delegate_task(
    goal="You are an independent code reviewer. Return ONLY valid JSON.",
    context="""<static_scan_results>[findings]</static_scan_results>
<code_changes>[diff]</code_changes>
Return: {"passed": bool, "security_concerns": [...], "logic_errors": [...], "suggestions": [...], "summary": "..."}""",
)
```

Fail-closed: non-empty security_concerns/logic_errors → passed=false.

## Step 6 — Evaluate

All passed → commit. Any failure → auto-fix loop.

## Step 7 — Auto-fix (max 2 cycles)

Spawn fix subagent to fix ONLY reported issues. Re-verify. If still failed after 2 cycles, escalate to user.

## Step 8 — Commit

```bash
git add -A && git commit -m "[verified] <description>"
```
