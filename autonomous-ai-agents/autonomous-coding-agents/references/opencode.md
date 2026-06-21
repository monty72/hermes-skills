# OpenCode CLI — Reference

Provider-agnostic, open-source AI coding agent.

## Prerequisites

```bash
npm i -g opencode-ai@latest
opencode auth login
opencode auth list  # should show at least one provider
```

## One-Shot Tasks

```bash
opencode run 'Add retry logic to API calls'
opencode run 'Review config for security issues' -f config.yaml
opencode run 'Refactor auth module' --model openrouter/anthropic/claude-sonnet-4
opencode run 'Debug CI failures' --thinking
```

## Interactive Sessions (Background)

```bash
terminal(command="opencode", workdir="~/project", background=true, pty=true)
process(action="submit", session_id="<id>", data="Implement OAuth refresh")
process(action="poll", session_id="<id>")
process(action="write", data="\x03")  # Ctrl+C to exit
```

**Important:** Do NOT use `/exit` — it opens an agent selector. Use Ctrl+C or kill.

## TUI Keybindings

| Key | Action |
|-----|--------|
| Enter | Submit (press twice if needed) |
| Tab | Switch agents (build/plan) |
| Ctrl+X L | Switch session |
| Ctrl+X M | Switch model |
| Ctrl+C | Exit |

## Common Flags

| Flag | Use |
|------|-----|
| `run 'prompt'` | One-shot execution |
| `-c, --continue` | Continue last session |
| `-s, --session <id>` | Continue specific session |
| `--agent <name>` | Choose agent (build or plan) |
| `--model provider/model` | Force specific model |
| `--thinking` | Show model thinking blocks |
| `--variant high|max|minimal` | Reasoning effort |
| `-f, --file <path>` | Attach file(s) |
| `--title <name>` | Name the session |

## PR Review

```bash
opencode pr 42
# Or in isolated clone:
REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW
cd $REVIEW && opencode run 'Review this PR vs main'
```

## Session & Cost Management

```bash
opencode session list
opencode stats --days 7 --models anthropic/claude-sonnet-4
```
