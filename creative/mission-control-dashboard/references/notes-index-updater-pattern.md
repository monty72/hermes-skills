# Notes Index Updater — No-Agent Discord Cron Pattern

## Purpose

Maintain a pinned "master link directory" in a Discord channel, auto-updating
when users drop new URLs. Runs as a no-agent cron watchdog — no LLM tokens consumed.

## Architecture

```
User drops link in #notes
        ↓
Cron tick (every 3h) → ~/.hermes/scripts/notes-index-updater.py
        ↓
Reads pinned message content as base
        ↓
Fetches all messages, extracts URLs from non-bot non-pinned messages
        ↓
Merges new URLs into appropriate section (GitHub, Websites, Services, Energy, Other)
        ↓
PATCHes the pinned message with updated content
        ↓
Silent if no new links found (sys.exit(0))
```

## The Script

Location: `~/.hermes/scripts/notes-index-updater.py`
Cron: no-agent watchdog, every 3h, deliver: local

Key implementation details:
- Reads `DISCORD_BOT_TOKEN` from `~/.hermes/.env` via `load_dotenv`
- Discord REST API via `urllib.request` (no library needed)
- Pinned message ID and channel ID are hardcoded constants
- Script checks pinned message length < 300 chars → rebuilds from ALL channel messages (safety net)
- Only posts if new links are found (no-op otherwise)
- Categories URLs by domain pattern matching (github.com, montygroup, 192.168, netzero/octopus/energy/powerwall)

## Discord REST API Patterns Used

### Create channel
`POST /guilds/{guild_id}/channels` — `{name, topic, type: 0, position}`

### Get messages
`GET /channels/{channel_id}/messages?limit=100`

### PATCH message (update pinned content)
`PATCH /channels/{channel_id}/messages/{message_id}` — `{content: "..."}`

### Pin message
`PUT /channels/{channel_id}/pins/{message_id}` — empty body, returns 204

### Delete message
`DELETE /channels/{channel_id}/messages/{message_id}` — returns 204

### Auth header
`Authorization: Bot <token>` — bot tokens use `Bot` prefix, not `Bearer`

## Cron Job

```bash
hermes cron create \
  --name "notes-index-updater" \
  --schedule "every 3h" \
  --script notes-index-updater.py \
  --no-agent \
  --deliver local
```

## Pitfalls

- **First version must preserve existing content.** If the script rebuilds from scratch
  filtering out bot messages, it will blank the pin (no non-bot links exist yet).
  Always use a "base content + merge new" pattern.
- **Pinned message update replaces content.** You cannot append — you must PATCH the
  entire message body with the merged result.
- **Discord 2000-char message limit.** Keep the pinned index concise.
- **Bot messages filtered out from "new" links.** Only user-dropped links count as new.
  The initial index content is written by the bot as the pinned message.
- **URL regex must handle Discord markdown.** Users may paste bare URLs, embedded links
  with `<>`, or wrapped in markdown. `r'https?://\S+'` catches most cases.
