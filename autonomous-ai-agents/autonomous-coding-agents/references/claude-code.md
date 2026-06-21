# Claude Code — Comprehensive Reference

Full orchestration guide for Claude Code (Anthropic's autonomous coding agent CLI v2.x).

## Prerequisites

```bash
npm install -g @anthropic-ai/claude-code
claude --version    # requires v2.x+
claude doctor        # health check
claude auth login    # browser OAuth (Pro/Max)
claude auth login --console  # API key billing
```

## Print Mode (`-p`) — Non-Interactive (PREFERRED)

One-shot task, returns result, exits. No PTY needed.

```bash
claude -p 'Add error handling' --allowedTools 'Read,Edit' --max-turns 10
cat src/auth.py | claude -p 'Review for bugs' --max-turns 1
```

Key flags: `--output-format json`, `--json-schema '{"type":"object"}'`, `--max-budget-usd`, `--fallback-model haiku`, `--bare` (fastest startup, skips OAuth).

## Interactive Mode via tmux

For multi-turn sessions, use tmux orchestration with `pty=true`:

```bash
tmux new-session -d -s claude-work -x 140 -y 40
tmux send-keys -t claude-work 'cd ~/project && claude' Enter
```

Handle dialogs: `sleep 4 && tmux send-keys Enter` (trust), then `Down && Enter` (permissions).

## CLI Flags Reference

### Session & Environment
- `-p, --print` — non-interactive mode
- `-c, --continue` — resume most recent session
- `-r, --resume <id>` — resume specific session
- `--fork-session` — create new session ID on resume
- `--worktree [name]` — isolated git worktree
- `--tmux` — create tmux session with worktree

### Model & Performance
- `--model sonnet|opus|haiku` — model selection
- `--effort low|medium|high|max` — reasoning depth
- `--max-turns <n>` — limit agentic loops (print mode only)
- `--max-budget-usd <n>` — cap spend

### Permission & Safety
- `--dangerously-skip-permissions` — auto-approve all tool use
- `--allowedTools 'Read,Edit,Bash'` — whitelist tools
- `--disallowedTools 'Bash(rm -rf)'` — blacklist tools
- `--permission-mode default|acceptEdits|auto|bypassPermissions`

### Output & Context
- `--output-format text|json|stream-json`
- `--append-system-prompt "text"` — add to system prompt
- `--mcp-config <file>` — load MCP servers
- `--agents '<json>'` — define subagents dynamically
- `--settings <file-or-json>` — extra settings

## Slash Commands (Interactive)

Session: `/compact`, `/clear`, `/context`, `/cost`, `/rewind`, `/status`, `/exit`
Review: `/review`, `/security-review`, `/plan`, `/loop`, `/batch`
Config: `/model`, `/effort`, `/init`, `/memory`, `/config`, `/permissions`, `/agents`, `/mcp`

## Hooks — Automation Events

All 8 hook types in `.claude/settings.json`: `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Notification`, `Stop`, `SubagentStop`, `PreCompact`, `SessionStart`.

## MCP Integration

```bash
claude mcp add -s user github -- npx @modelcontextprotocol/server-github
claude mcp add -s local postgres -- npx @anthropic-ai/server-postgres ...
claude mcp list
```

## Cost Tips

1. Use `--max-turns` to prevent runaway loops
2. Use `--effort low` for simple tasks
3. Use `--bare` for CI/scripting
4. Use `--model haiku` for cheap tasks, `opus` for complex
5. `/compact` proactively when context exceeds 70%
6. Start new sessions for distinct tasks

## Pitfalls

1. Interactive mode REQUIRES tmux — Claude is a full TUI app
2. `--dangerously-skip-permissions` defaults to "No, exit"
3. `--max-turns` is print-mode only
4. Context degrades above 70% — use `/compact`
5. Background tmux sessions persist — always clean up
