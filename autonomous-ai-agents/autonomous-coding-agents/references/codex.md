# Codex CLI — Reference

Delegate coding to OpenAI Codex CLI.

## Prerequisites

```bash
npm install -g @openai/codex
# Auth: OPENAI_API_KEY or Codex OAuth from `hermes auth add openai-codex`
```

**Must run inside a git repository** — Codex refuses to run outside one.

## One-Shot Tasks

```bash
terminal(command="codex exec 'Add dark mode toggle'", workdir="~/project", pty=true)
```

For scratch work:
```bash
terminal(command="cd $(mktemp -d) && git init && codex exec 'Build a snake game'", pty=true)
```

## Background Mode

```bash
terminal(command="codex exec --full-auto 'Refactor auth module'", workdir="~/project", background=true, pty=true)
process(action="poll", session_id="<id>")
process(action="submit", session_id="<id>", data="yes")
```

## Key Flags

| Flag | Effect |
|------|--------|
| `exec "prompt"` | One-shot execution, exits when done |
| `--full-auto` | Sandboxed but auto-approves file changes |
| `--yolo` | No sandbox, no approvals (fastest) |
| `--sandbox danger-full-access` | Bypass sandbox (use in Hermes gateway) |

## PR Review

```bash
REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW
cd $REVIEW && gh pr checkout 42 && codex review --base origin/main
```

## Parallel Issue Fixing

```bash
git worktree add -b fix/issue-78 /tmp/issue-78 main
git worktree add -b fix/issue-99 /tmp/issue-99 main

codex --yolo exec 'Fix issue #78: <description>' workdir="/tmp/issue-78" background=true pty=true
codex --yolo exec 'Fix issue #99: <description>' workdir="/tmp/issue-99" background=true pty=true

# After completion
cd /tmp/issue-78 && git push -u origin fix/issue-78
gh pr create --repo user/repo --head fix/issue-78 --title 'fix: ...'
```

## Rules

1. Always use `pty=true` — Codex is interactive TUI
2. Git repo required — use `mktemp -d && git init` for scratch
3. Use `exec` for one-shots
4. Use background for long tasks
5. In Hermes gateway, prefer `--sandbox danger-full-access`
