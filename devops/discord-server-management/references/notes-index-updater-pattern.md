# Self-Updating Pinned Index — Pattern Reference

A no-agent watchdog cron maintains a pinned link directory in the `#notes` channel.
It runs every 3 hours, extracts URLs from user messages, and appends new ones to
the pinned index without touching already-indexed content.

## Key Design Decisions

### Why a no-agent script instead of an LLM-driven cron?
- Deterministic: URLs are extracted by regex, not by LLM interpretation
- Cheap: zero token cost per run
- Silent: exits with code 0 when no new links, so nothing is delivered
- Reliable: no model availability issues, no rate limits

### Why PATCH the pinned message instead of unpin/repin?
- Pinning is a write operation; editing preserves the pin
- No flash effect in the channel
- History of changes is visible in the edit log

## Script Flow

1. GET the current pinned message content as `base_content`
2. If `base_content < 300 chars`: rebuild from ALL messages (safety net)
3. GET all messages in channel (limit 100)
4. Skip pinned message and any bot-authored messages
5. Regex-extract all `https?://\S+` URLs from user messages
6. Filter to URLs NOT already in `base_content`
7. Categorize URLs (github, montygroup, 192.168, energy, other)
8. Append new entries under the correct section header
9. PATCH the pinned message with merged content

## Categorization Rules

| Contains in URL | Section |
|---|---|
| `github.com` | GitHub Repositories |
| `montygroup` | Websites and Domains |
| `192.168.` | Self-Hosted Services |
| `netzero`, `octopus`, `energy`, `powerwall`, `tesla` | Energy Stack |
| Everything else | Other Links |

## Cron Config

```yaml
action: create
name: notes-index-updater
script: notes-index-updater.py
no_agent: true
schedule: every 3h
deliver: local
```

## Error Recovery

If the pinned message gets blanked (writing a too-short version), the 300-char
safety check in the script will auto-rebuild from all messages in the channel
on the next run. No manual recovery needed.

## Environment Loading (No-Agent Cron Gotcha)

When the script runs as a `no_agent: true` cron job, it runs in a bare shell
with no Hermes environment. The `.env` file must be loaded explicitly:

```python
from dotenv import load_dotenv
load_dotenv(os.path.expanduser('~/.hermes/.env'))
# NOT: load_dotenv()  — this won't find the file from a no-agent context
```

The `NOTES` and `PINNED` channel/message IDs are hardcoded constants in the
script — they don't come from env vars because they never change for a given
channel setup.
