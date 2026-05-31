# OpenClaw Prompt Architecture

Source: `OPENCLAW_SYSTEM_PROMPT_STUDY.md` from the [seedprod/openclaw-prompts-and-skills](https://github.com/seedprod/openclaw-prompts-and-skills) repo (released by Lonely Octopus).

## Core Insight

OpenClaw's personality is **entirely markdown files** injected into the system prompt. No fine-tuning, no special models. The agent's behaviour, memory, tools, and identity all come from `.md` files that get assembled before every message.

## The 7 Prompt Files

| File | Purpose | Injected? |
|------|---------|-----------|
| `SOUL.md` | Core personality — opinions, boundaries, vibe, tone. "Be genuinely helpful, not performatively helpful." "Have opinions." | Always |
| `IDENTITY.md` | Agent fills in its name, creature type, vibe, emoji during first conversation | Always (after bootstrap) |
| `USER.md` | User profile — name, timezone, preferences, context. Built over time by the agent | Always |
| `CLAUDE.md` (→ `AGENTS.md` in OpenClaw) | Workspace rules: memory system, safety rules, heartbeat protocol, group chat etiquette, tool-specific notes | Always |
| `TOOLS.md` | Environment-specific notes (camera names, SSH hosts, device nicknames, speaker names). Separated from skills so skills are sharable without leaking infra | Always |
| `BOOTSTRAP.md` | First-run ritual: "Hey, I just came online. Who am I? Who are you?" Guides the agent through populating IDENTITY.md + USER.md, then deletes itself | First run only |
| `MEMORY.md` | Long-term memory maintained by the agent. Curated distillations from daily `memory/YYYY-MM-DD.md` files | Main session only |

## System Prompt Assembly Order

```
Base identity → Tool definitions → Skills list (from .claude/skills/)
→ Workspace info → Runtime info (model, channel, capabilities)
→ Project context files:
    SOUL.md
    IDENTITY.md
    USER.md
    AGENTS.md (as CLAUDE.md)
    TOOLS.md
    BOOTSTRAP.md (first run only, deleted after onboarding)
→ Session history
→ Current message
```

### Full System Prompt Structure (from the study)

```text
## Base Identity
"You are a personal assistant running inside OpenClaw."

## Tooling
Tool availability filtered by policy. ~20 tools (read, write, edit, exec, web_search, browser, cron, message, sessions_spawn, sessions_send, etc.)

## Tool Call Style
Default: do not narrate routine tool calls. Narrate only for multi-step, complex, or sensitive operations.

## Skills (mandatory)
<available_skills>
  <skill><name>weather</name><description>...</description><location>/path/to/skill/SKILL.md</location></skill>
</available_skills>
Constraint: read exactly one skill per message.

## Memory Recall
Before answering about prior work: memory_search on MEMORY.md + memory/*.md, then memory_get for specific lines.

## Heartbeats
HEARTBEAT_OK = silent suppression. Agent checks HEARTBEAT.md for proactive work.

## Reply Tags
[[reply_to_current]] / [[reply_to:<id>]] for native reply/quote on supported surfaces.

## Silent Replies
HEARTBEAT_OK must be the ENTIRE message. Never append it to a real reply.

## Runtime
agent=main | host=macbook | os=darwin | channel=telegram | capabilities=inlineButtons | thinking=off
```

## Message Flow

```
User sends message → Gateway receives → Build system prompt →
Build messages array (system + history + new message) → Call LLM API →
Process response (tool call → execute → loop, or HEARTBEAT_OK → suppress,
or SILENT_REPLY → suppress, or text → send back to user)
```

## Heartbeat Flow

```
Cron/scheduler (every 30min) → Inject heartbeat message →
Agent reads HEARTBEAT.md → Checks email/calendar/weather/mentions →
Nothing: reply HEARTBEAT_OK (suppressed) | Something: send alert to user
```

## Memory Flow

```
Session start: read SOUL.md → IDENTITY.md → USER.md → memory/YYYY-MM-DD.md (today + yesterday) → MEMORY.md
During session: writes decisions/context to memory/YYYY-MM-DD.md
Maintenance (heartbeat): reads recent memory/*.md, extracts important info, updates MEMORY.md, cleans outdated info
```

## Key Design Principles

1. **Memory is files.** No vector DB, no embeddings. Daily notes + curated long-term = continuity.
2. **Personality is explicit.** "Have opinions. You're allowed to disagree." "Be the assistant you'd actually want to talk to." The model follows these because they're in the prompt.
3. **First impressions matter.** BOOTSTRAP.md creates the "coming alive" moment. It's theatrical but effective.
4. **Group chat behavior is prompted.** Rules about when to speak vs HEARTBEAT_OK, when to react vs reply, how to avoid dominating.
5. **Skills are self-describing.** Each skill is a SKILL.md with name, description, trigger conditions, and linked scripts/templates.

## Differences from Hermes Agent

| Aspect | OpenClaw | Hermes |
|--------|----------|--------|
| Identity files | SOUL.md + IDENTITY.md + USER.md + CLAUDE.md + TOOLS.md + BOOTSTRAP.md | SOUL.md + USER.md + MEMORY.md (in-memory memory tool) |
| Memory | File-based (memory/YYYY-MM-DD.md + MEMORY.md) | Tool-based (memory tool with SQLite backend) |
| Skills | `.claude/skills/<name>/SKILL.md` read by agent at runtime | `~/.hermes/skills/<category>/<name>/SKILL.md` read on demand |
| Heartbeats | Cron injects heartbeat message; agent replies HEARTBEAT_OK for silence | Cron jobs in agent loop |
| Session persistence | `.jsonl` files per channel | SQLite session DB |
| Platform | Node.js CLI (openclaw) | Python CLI (hermes) |

## Reference

- Repo: https://github.com/seedprod/openclaw-prompts-and-skills
- Full study: `OPENCLAW_SYSTEM_PROMPT_STUDY.md` (24KB, 425 lines, includes ASCII flow diagrams)
- Telegram POC bot: `telegram-claude-poc.py` (~130 lines, pipes Telegram to Claude Code headless via `claude -p`)
- Skills included: weather, wacli, voice-call, video-frames, Trello, tmux, Things, summarize, Spotify, Sonos, songsee, Slack, skill-creator, motion, macOS-cmds, music, local-web, invite, get-screenshots, github, email, docker, dispatch, custom-instruction, calendar, brew, apple-notes, 1password
