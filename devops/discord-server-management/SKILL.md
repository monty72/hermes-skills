---
name: discord-server-management
description: Manage Discord servers, channels, messages, and pinned content via REST API — create/rename/reorder channels, manage pins, maintain self-updating link indexes, and handle bot permissions.
tags: [discord, channels, pins, bot, api, server-management, messaging]
---

# Discord Server Management

Manage a Discord server programmatically via the REST API. Covers channel CRUD, message/pin management, and automated content maintenance patterns.

## Prerequisites

- Bot token stored in `~/.hermes/.env` as `DISCORD_BOT_TOKEN` (also in vault)
- Bot added to the server with **Administrator** permission (permissions=8 in OAuth2 invite)
- Gateway intents enabled: Server Members Intent, Message Content Intent

## API Setup

Use a persistent opener with proper User-Agent and Authorization headers:

```python
opener = urllib.request.build_opener()
opener.addheaders = [
    ('User-Agent', 'DiscordBot (YourBot, 1.0)'),
    ('Authorization', f'Bot {TOKEN}')
]
urllib.request.install_opener(opener)
```

## Common Operations

### List Channels
`GET /guilds/{guild_id}/channels` — returns all channels with id, name, type, position.

### Create a Text Channel
`POST /guilds/{guild_id}/channels` with body `{"name": "channel-name", "type": 0, "topic": "...", "position": N}`.
- Type 0 = GUILD_TEXT, Type 2 = GUILD_VOICE, Type 4 = GUILD_CATEGORY
- Position is 0-indexed within the channel list

### Pin a Message
`PUT /channels/{channel_id}/pins/{message_id}` — returns 204 No Content on success.
Bot needs **Manage Messages** permission (included in Administrator).

### Update a Pinned Message (Edit Content)
`PATCH /channels/{channel_id}/messages/{message_id}` with body `{"content": "new text"}`.
Preserves the pin status — no need to re-pin after editing.

### Delete a Message
`DELETE /channels/{channel_id}/messages/{message_id}` — returns 204 on success.

### Send a Message
`POST /channels/{channel_id}/messages` with body `{"content": "message text"}`.

## Self-Updating Pinned Index Pattern

For channels that maintain a curated link directory or resource index (like `#notes`):

### Architecture
- **Pinned message** contains the canonical index
- **No-agent cron job** (`no_agent=True`) runs a script on schedule (e.g. every 3h)
- **Script** collects all user messages, extracts URLs, merges new ones into the pinned index
- **Silent on no-change** — script exits with sys.exit(0) when nothing new, so cron sends nothing

### Key Design Choices
- Always preserve the existing pinned content as base; only APPEND new links found in user messages
- Skip the bot's own pinned message when scanning for links (already indexed)
- Add a safety check: if pinned base is <300 chars (blanked/reset), rebuild from ALL messages in channel

### Pitfalls
- **First-run** on a fresh script can blank the pinned message if the script ignores bot messages. Always read the current pinned content before modifying.
- **Discord 403 errors** on channel listing are often a User-Agent issue — set it properly. The `/guilds/{id}/channels` endpoint is especially sensitive.
- **Pinned endpoint** returns 204 with no body — handle this gracefully (don't try to JSON-decode it).
- **Message content limit** is 2000 characters. Keep indexes concise. For longer content, split into multiple messages.
- **Bot messages** are filtered when scanning for new links — users drop links, not the bot

### Script Skeleton

```python
from dotenv import load_dotenv; import os, json, re, urllib.request
load_dotenv(os.path.expanduser('~/.hermes/.env'))
TOKEN = os.environ.get('DISCORD_BOT_TOKEN', '')
NOTES = 'channel_id'
PINNED = 'message_id'

opener = urllib.request.build_opener()
opener.addheaders = [('User-Agent', 'DiscordBot (...), 1.0)'), ('Authorization', f'Bot {TOKEN}')]
urllib.request.install_opener(opener)

def api(m, p, d=None):
    req = urllib.request.Request(f'https://discord.com/api/v10{p}', ...
    with urllib.request.urlopen(req) as r: ...

current = api('GET', f'/channels/{NOTES}/messages/{PINNED}')
base_content = current['content']

# Safety: rebuild from all messages if base is blanked
if len(base_content) < 300: ... # rebuild

# Scan user messages for new links
msgs = api('GET', ...)
for msg in msgs:
    if msg.get('id') == PINNED or msg.get('author', {}).get('bot'): continue
    # extract URLs, categorize, merge into base

# PATCH the pinned message
api('PATCH', f'/channels/{NOTES}/messages/{PINNED}', {'content': new_content})
```

## References

For the full self-updating index implementation, see the `notes-index-updater.py` script in `~/.hermes/scripts/`.

## Related

- `managed-agent-service` skill — for Hermes/OpenClaw customer provisioning (different domain but same infrastructure)
