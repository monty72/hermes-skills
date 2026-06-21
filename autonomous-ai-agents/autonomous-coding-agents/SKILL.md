---
name: autonomous-coding-agents
description: "Orchestrate external AI coding agent CLIs — Claude Code, Codex, OpenCode. Covers installation, auth, print mode, interactive TUI, PR review, parallel tasking, and common pitfalls."
tags: [coding-agents, claude-code, codex, opencode, delegation, automation, orchestration]
related_skills: [github, test-driven-development]
---

# Autonomous Coding Agents — Delegation Guide

Orchestrate external AI coding agent CLIs for feature implementation, refactoring, PR review, and batch issue fixing. This umbrella covers all three major open coding agents; each has detailed reference content in `references/`.

## Choosing an Agent

| Agent | Strengths | Preferred When |
|-------|-----------|---------------|
| **Claude Code** | Anthropic Sonnet/Opus, deep reasoning, richest CLI flags, plugins/hooks/MCP | Complex multi-step tasks, code review, CI/scripting |
| **Codex** | OpenAI, `--yolo` mode for speed, worktree for parallel | Fast one-shots, parallel issue fixing |
| **OpenCode** | Provider-agnostic, open-source, no API key monopoly | User prefers open-source, wants to BYO model |

## Common Pattern: Print Mode (Preferred)

All three support bounded one-shot execution. This is the cleanest integration path.

```bash
# Claude Code
claude -p 'Add error handling to API calls' --allowedTools 'Read,Edit' --max-turns 10

# Codex
codex exec 'Add dark mode toggle'

# OpenCode
opencode run 'Add retry logic to API calls'
```

## Common Pattern: Interactive Session (Multi-turn)

For iterative work, start the CLI's TUI in background with `pty=true`:

```bash
# Start in background
terminal(command="claude -p 'Refactor auth module' --allowedTools 'Read,Edit,Bash' --max-turns 20", workdir="~/project", background=true, pty=true)

# Monitor progress
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# Send input if agent asks a question
process(action="submit", session_id="<id>", data="yes")

# Kill if needed
process(action="kill", session_id="<id>")
```

## Common Pattern: PR Review

```bash
# Quick review (print mode, no pty needed)
git diff main...feature-branch | claude -p 'Review this diff' --max-turns 1

# Deep review (interactive)
gh pr checkout 42
opencode run 'Review this PR vs main' --thinking

# Isolated review in temp clone
REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW
codex exec "gh pr checkout 42 && codex review --base origin/main"
```

## Common Pattern: Parallel Tasking

Use worktrees or separate workdirs for parallel execution:

```bash
git worktree add -b fix/issue-78 /tmp/issue-78 main
git worktree add -b fix/issue-99 /tmp/issue-99 main

terminal(command="claude -p 'Fix issue #78' --max-turns 15", workdir="/tmp/issue-78", background=true, pty=true)
terminal(command="codex exec --yolo 'Fix issue #99'", workdir="/tmp/issue-99", background=true, pty=true)
```

## Prerequisites (All Agents)

| Agent | Install | Auth |
|-------|---------|------|
| Claude Code | `npm i -g @anthropic-ai/claude-code` | `claude auth login` or `ANTHROPIC_API_KEY` |
| Codex | `npm i -g @openai/codex` | `OPENAI_API_KEY` or Codex OAuth |
| OpenCode | `npm i -g opencode-ai@latest` | `opencode auth login` or provider env vars |

## Key Pitfalls

1. **All agents need `pty=true` for interactive/TUI sessions.** Print mode (`-p` for Claude, `exec` for Codex, `run` for OpenCode) works without pty.
2. **Git repo is required** by all three — Codex refuses to run outside one. Use `mktemp -d && git init` for scratch work.
3. **Claude Code's `--dangerously-skip-permissions` dialog defaults to "No, exit"** — use print mode to skip dialogs entirely.
4. **Codex sandboxing** may fail in Hermes gateway contexts. Use `--sandbox danger-full-access`.
5. **OpenCode's `/exit` is NOT valid** — use Ctrl+C to exit. OpenCode run doesn't need pty.
6. **Set `--max-turns`** (Claude) or `--full-auto` (Codex) or `run` (OpenCode) — prevents runaway loops.
7. **Clean up tmux sessions** when done with Claude interactive mode.

## References

- `references/claude-code.md` — Full Claude Code reference: all CLI flags, session management, hooks, MCP, subagents, settings
- `references/codex.md` — Full Codex reference: flags, parallel worktrees, batch PR reviews
- `references/opencode.md` — Full OpenCode reference: TUI keybindings, session management, cost tracking
