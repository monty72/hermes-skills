# Discord API Channel Setup

Quick-reference commands for creating Hermes channels via the Discord REST API.

## Prerequisites

- Bot in server with Administrator permissions
- `DISCORD_BOT_TOKEN` set in environment

## Get Server (Guild) ID

```python
from dotenv import load_dotenv
import os, json, urllib.request
load_dotenv(os.path.expanduser('~/.hermes/.env'))
token = os.environ['DISCORD_BOT_TOKEN']
opener = urllib.request.build_opener()
opener.addheaders = [('User-Agent', 'DiscordBot (HermesAgent, 1.0)'),
                     ('Authorization', f'Bot {token}')]
urllib.request.install_opener(opener)
req = urllib.request.Request('https://discord.com/api/v10/guilds/1508964446582734848')
with urllib.request.urlopen(req) as r:
    g = json.loads(r.read())
    print(f'{g["name"]}: {g["id"]}')
```

## Create Standard Hermes Channels

```python
GUILD = '0000000000000000000'  # Replace with your guild ID

def create_channel(name, topic, position=0):
    return api('POST', f'/guilds/{GUILD}/channels', {
        'name': name,
        'type': 0,  # GUILD_TEXT
        'topic': topic,
        'position': position,
    })

# Standard layout
general      = create_channel('general', 'Main communication with HermesAgent', 0)
daily_digest = create_channel('daily-digest', 'Automated daily summaries from HermesAgent', 1)
ideas        = create_channel('content-ideas', 'Brainstorm content ideas and projects', 2)
scripts      = create_channel('scripts', 'Code scripts, automation, and terminal output', 3)
notes        = create_channel('notes', 'Master index of all repos, tools, URLs, and services', 4)
```

### Channel Layout (Hermes HQ)

| Channel | Purpose | Position |
|---------|---------|----------|
| `#general` | Main chat — @HermesAgent to summon | 0 |
| `#daily-digest` | Automated daily briefing (cron) | 1 |
| `#content-ideas` | Brainstorming | 2 |
| `#scripts` | Free-response — no @ needed | 3 |
| `#notes` | Master link directory (pinned + auto-updated) | 4 |

## Channel Types

| Value | Type |
|-------|------|
| `0` | GUILD_TEXT |
| `2` | GUILD_VOICE |
| `4` | GUILD_CATEGORY |
| `5` | GUILD_ANNOUNCEMENT |
| `15` | GUILD_FORUM |

## Post and Pin a Master Message (for #notes)

```python
# Post the initial master index
msg = api('POST', f'/channels/{NOTES_ID}/messages', {'content': master_list_content})
msg_id = msg['id']

# Pin it
api('PUT', f'/channels/{NOTES_ID}/pins/{msg_id}', {})
```

## Get Channel IDs

```python
channels = api('GET', f'/guilds/{GUILD}/channels')
for ch in channels:
    print(f'#{ch["name"]:20s} {ch["id"]}  type={ch["type"]} pos={ch["position"]}')
```

## Channel ID Usage

Use channel IDs for:
- `discord.allowed_channels` in Hermes config.yaml
- `deliver: "discord:<channel_id>"` in cron jobs
- Target in `send_message`: `discord:1508966625494437928`

## Full Reference

See the main `SKILL.md` for:
- Pinned message management (pin, update, pitfalls)
- No-agent watchdog pattern for auto-maintaining pinned indexes
- Python API access pattern for cron scripts
- Script template: `scripts/notes-index-watchdog.py`
