---
name: discord-bot-management
description: Create, configure, and manage Discord bots — application setup, OAuth2 invite flow, channel management, message operations, pinned indexes, and auto-updating link directories via Discord REST API.
tags: [discord, bot, gateway, oauth, channels, messages, pinned-messages, cron, server-setup]
related_skills: [hermes-agent, managed-agent-service]
---

# Discord Bot Management

## Overview

End-to-end Discord bot operations: creating an application in the Developer Portal, obtaining and storing bot tokens, inviting the bot to a server with proper permissions, managing channels and messages via the REST API, and setting up automated index maintenance.

---

## 1. Creating a Discord Application & Bot

### Via Browser (Discord Developer Portal)

1. Navigate to https://discord.com/developers/applications
2. Click **New Application** → name it
3. Go to **Bot** section → **Add Bot**
4. **Reset Token** — copy the token immediately (cannot see it again)
5. **Enable Gateway Intents**:
   - ✅ Server Members Intent
   - ✅ Message Content Intent (required for reading messages / Discord bridge)

### Token Storage

Save the bot token securely — do not leave in plaintext during setup:

```bash
# Preferred: Hermes vault
hermes-vault set DISCORD_BOT_TOKEN "<token>"

# Alternative: Hermes .env (gateway reads from here)
# Add to ~/.hermes/.env:
# DISCORD_BOT_TOKEN=<token>
```

**Important:** The Hermes gateway reads `DISCORD_BOT_TOKEN` from `~/.hermes/.env` at startup. If using the vault, inject via a cron script or `eval $(hermes-vault env)`. Restart the gateway after changes: `hermes gateway restart`.

### Token Verification

```python
from dotenv import load_dotenv
import os, json, urllib.request

load_dotenv(os.path.expanduser('~/.hermes/.env'))
token = os.environ.get('DISCORD_BOT_TOKEN', '')

opener = urllib.request.build_opener()
opener.addheaders = [('User-Agent', 'DiscordBot (BotName, 1.0)'), ('Authorization', f'Bot {token}')]
urllib.request.install_opener(opener)

# Test: gateway info
req = urllib.request.Request('https://discord.com/api/v10/gateway/bot')
with urllib.request.urlopen(req) as resp:
    print(json.loads(resp.read()))
```

**Pitfall:** Always set a `User-Agent` header of the form `DiscordBot (..., 1.0)`. Without it, Discord may return 403s for some endpoints that work fine in other contexts.

---

## 2. OAuth2 Invite — Adding Bot to Server

### Generate Invite URL

In Discord Developer Portal → **OAuth2** → **URL Generator**:

| Scope | Value |
|-------|-------|
| Scope | `bot` |
| Bot Permissions | `Administrator` (value: `8`) or specific |

The URL format:
```
https://discord.com/api/oauth2/authorize?client_id=<CLIENT_ID>&permissions=8&scope=bot
```

### Authorization Flow

1. Open the URL in a browser
2. **hCaptcha challenge appears** — the agent CANNOT solve this. User must click the "I'm not a robot" checkbox on the live browser tab.
3. After the user completes hCaptcha, click **Authorise** (if the page redirects or logs out, the browser session expired — user needs to log in again)
4. **After authorizing:** The bot joins the server. Verify via the API:

```python
req = urllib.request.Request(
    f'https://discord.com/api/v10/guilds/<GUILD_ID>',
    headers={'Authorization': f'Bot {token}', 'User-Agent': 'DiscordBot (HermesAgent, 1.0)'}
)
with urllib.request.urlopen(req) as resp:
    guild = json.loads(resp.read())
    print(f"Bot in guild: {guild['name']}")
```

**Pitfalls:**
- Browser sessions expire. If Discord shows a login page, the user must log in again before the OAuth flow completes.
- If using the browser tool, set `stealth_residential_proxies=true` in config or hCaptcha will flag the request.
- If the bot token returns 403 on `/users/@me` — that's normal. Bot tokens use `/gateway/bot` for basic verification.

---

## 3. Channel Management via REST API

### List All Channels

```python
req = urllib.request.Request(
    f'https://discord.com/api/v10/guilds/{guild_id}/channels',
    headers={'Authorization': f'Bot {token}', 'User-Agent': 'DiscordBot (HermesAgent, 1.0)'}
)
with urllib.request.urlopen(req) as resp:
    channels = json.loads(resp.read())
    for ch in channels:
        print(f'{ch["name"]:20s} {ch["id"]:20s} type={ch["type"]} pos={ch["position"]}')
```

### Create a Text Channel

```python
import json
req = urllib.request.Request(
    f'https://discord.com/api/v10/guilds/{guild_id}/channels',
    data=json.dumps({
        'name': 'channel-name',    # lowercase, no spaces
        'type': 0,                 # 0 = GUILD_TEXT
        'topic': 'Channel description',
        'position': 3
    }).encode(),
    headers={
        'Authorization': f'Bot {token}',
        'Content-Type': 'application/json',
        'User-Agent': 'DiscordBot (HermesAgent, 1.0)'
    },
    method='POST'
)
with urllib.request.urlopen(req) as resp:
    channel = json.loads(resp.read())
    print(f"Created: #{channel['name']} (id: {channel['id']})")
```

### Channel Types
| Value | Type | Description |
|-------|------|-------------|
| 0 | GUILD_TEXT | Standard text channel |
| 2 | GUILD_VOICE | Voice channel |
| 4 | GUILD_CATEGORY | Category for grouping channels |
| 5 | GUILD_ANNOUNCEMENT | Announcement channel |
| 15 | GUILD_FORUM | Forum channel |

---

## 4. Messages — Send, Read, Pin

### Send a Message

```python
req = urllib.request.Request(
    f'https://discord.com/api/v10/channels/{channel_id}/messages',
    data=json.dumps({'content': 'Message text here'}).encode(),
    headers={
        'Authorization': f'Bot {token}',
        'Content-Type': 'application/json',
        'User-Agent': 'DiscordBot (HermesAgent, 1.0)'
    },
    method='POST'
)
with urllib.request.urlopen(req) as resp:
    msg = json.loads(resp.read())
    print(f"Sent: {msg['id']}")
```

### Read Messages (recent 100)

```python
req = urllib.request.Request(
    f'https://discord.com/api/v10/channels/{channel_id}/messages?limit=100',
    headers={'Authorization': f'Bot {token}', 'User-Agent': 'DiscordBot (HermesAgent, 1.0)'}
)
with urllib.request.urlopen(req) as resp:
    messages = json.loads(resp.read())
```

### Pin a Message

```python
# PUT with empty body — returns 204 No Content on success
# Error 403 with code 10103 = "Missing Permissions" (need Manage Messages or Administrator)
req = urllib.request.Request(
    f'https://discord.com/api/v10/channels/{channel_id}/pins/{message_id}',
    data=b'',
    headers={'Authorization': f'Bot {token}', 'User-Agent': 'DiscordBot (HermesAgent, 1.0)'},
    method='PUT'
)
try:
    with urllib.request.urlopen(req) as resp:
        print(f"Pinned! Status: {resp.status}")
except urllib.error.HTTPError as e:
    if e.code == 204:
        print("Pinned!")  # Discord returns 204 with empty body
    else:
        body = e.read().decode()
        print(f"Error {e.code}: {body}")
```

**Pitfall:** Pinning returns `204 No Content` with an empty body. Don't try to parse JSON from it — check status code instead.

### Update (Edit) a Message

```python
req = urllib.request.Request(
    f'https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}',
    data=json.dumps({'content': 'Updated content'}).encode(),
    headers={
        'Authorization': f'Bot {token}',
        'Content-Type': 'application/json',
        'User-Agent': 'DiscordBot (HermesAgent, 1.0)'
    },
    method='PATCH'
)
with urllib.request.urlopen(req) as resp:
    updated = resp.read()
```

---

## 5. Notes Channel — Auto-Updating Link Directory

This pattern creates a pinned message that acts as a canonical link directory, with a no-agent watchdog cron that merges user-dropped URLs into the pinned message.

### Setup

1. Create `#notes` channel (see §3 above)
2. Post the initial master link directory as a message
3. Pin it (see §4 above)
4. Save the pinned message ID

### Watchdog Script

Save to `~/.hermes/scripts/notes-index-updater.py`:

```python
#!/usr/bin/env python3
"""Watchdog: update pinned link directory by merging new user-link drops."""
from dotenv import load_dotenv; import os, json, re, urllib.request, sys
load_dotenv(os.path.expanduser('~/.hermes/.env'))
TOKEN = os.environ.get('DISCORD_BOT_TOKEN', '')
NOTES_CHANNEL = '<channel_id>'
PINNED_MSG_ID = '<message_id>'

opener = urllib.request.build_opener()
opener.addheaders = [('User-Agent', 'DiscordBot (HermesAgent, 1.0)'), ('Authorization', f'Bot {TOKEN}')]
urllib.request.install_opener(opener)

def api(method, path, data=None):
    req = urllib.request.Request(
        f'https://discord.com/api/v10{path}',
        data=json.dumps(data).encode() if data else None,
        headers={'Content-Type': 'application/json'} if data else {},
        method=method
    )
    with urllib.request.urlopen(req) as r:
        body = r.read()
        return json.loads(body) if body else {}

# Get pinned message content as base
current = api('GET', f'/channels/{NOTES_CHANNEL}/messages/{PINNED_MSG_ID}')
base_content = current.get('content', '')

# Get new user messages (not bot, not pinned)
msgs = api('GET', f'/channels/{NOTES_CHANNEL}/messages?limit=100')
new_links = {}
for msg in msgs:
    if msg.get('id') == PINNED_MSG_ID or msg.get('author', {}).get('bot', False):
        continue
    c = msg.get('content', '')
    for url in re.findall(r'https?://\S+', c):
        idx = c.find(url)
        label = c[max(0, idx-50):idx].strip().rstrip('•-*[]():, ')
        new_links[url] = label if label else url

# Filter to truly new links
missing = {u: l for u, l in new_links.items() if u not in base_content}
if not missing:
    sys.exit(0)

# Categorize and append
cats = {}
for url, label in missing.items():
    cat = 'Other Links'
    if 'github.com' in url: cat = 'GitHub Repositories'
    elif any(s in url for s in ['montygroup', '192.168.', 'homeassistant']): cat = 'Self-Hosted Services'
    elif any(s in url for s in ['netzero', 'octopus', 'powerwall']): cat = 'Energy Stack'
    # ... add categories as needed
    cats.setdefault(cat, []).append(f"• {label}: {url}" if label != url else f"• {url}")

# Append to base content under the right sections
# ... (section parsing logic)
result = api('PATCH', f'/channels/{NOTES_CHANNEL}/messages/{PINNED_MSG_ID}',
             {'content': updated_content})
```

### Cron Job

```bash
# Create via Hermes cron tool — runs every 3 hours, no agent overhead
cronjob action=create \
  name=notes-index-updater \
  schedule='every 3h' \
  no_agent=true \
  script=notes-index-updater.py \
  deliver=local
```

**Design choice:** `no_agent=true` is deliberate — this is a pure data-processing task. The script reads messages, patches the pinned message, and exits. No LLM reasoning needed.

---

## 6. Gateway Integration

For Hermes-to-Discord bridging:

```yaml
# In ~/.hermes/config.yaml:
gateway:
  platforms:
    discord:
      enabled: true
      token: "${DISCORD_BOT_TOKEN}"
      # Channel-specific conversation routing:
      # channels:
      #   general: "chat"
      #   scripts: "free-response"
```

After updating config, restart the gateway:
```bash
hermes gateway restart
```

**⚠️ Gateway restart kills the active agent session.** Ask the user first or wait for a natural break.

---

## Pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| `401 Unauthorized` on all endpoints | Token is invalid | Reset token in Developer Portal, update `.env`, restart gateway |
| `403` on `/users/@me` | Normal for bot tokens | Use `/gateway/bot` for verification instead |
| `403` on `/guilds/{id}/channels` | Missing User-Agent header | Add `User-Agent: DiscordBot (Name, 1.0)` |
| `403` with code `10103` on pin | Missing Manage Messages | Use Administrator permissions (8) or add explicit permission overwrite |
| `PUT /pins/{id}` returns empty 204 | Expected! | Check status code, don't parse JSON body |
| hCaptcha blocks OAuth | Browser detects automation | User must solve on the live browser tab |
| Token works in API but not in Hermes gateway | Gateway hasn't restarted | `hermes gateway restart` to reload `.env` |
| Message length > 2000 chars | Discord limit | Content must be ≤ 2000 characters. Truncate, split, or use embeds. |
