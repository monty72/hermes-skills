---
name: discord-integration
description: Set up Discord as a message delivery channel for Hermes Agent — bot creation, token retrieval, server/channel setup, and Hermes config.yaml wiring.
category: social-media
version: 1.2.0
author: Agent
created_by: agent
---

# Discord Integration for Hermes Agent

Set up Discord as a messaging platform for Hermes Agent's `send_message` tool, gateway delivery, and cron job output.

## Overview

Hermes Agent can deliver messages to Discord via its gateway/bridge system. This requires:
1. A Discord bot application + bot token
2. A server for the bot to join
3. The bot invited to your server with proper permissions
4. Channels configured for delivery
5. Hermes configured with the bot token in `config.yaml`
6. A default channel configured for delivery

## Step 1: Create the Bot Application

1. Go to https://discord.com/developers/applications
2. Click **Log In** and authenticate
3. Click **New Application** → name it (e.g., "Hermes Agent")
4. Go to the **Bot** section in the left sidebar
5. Click **Add Bot** → confirm
6. Under the **TOKEN** section, click **Reset Token** → **Copy**
7. Save this token securely (it won't be shown again)

### Browser Login (React SPA Workaround)

The Discord Developer Portal is a React SPA where `browser_snapshot` often returns empty or partial accessibility trees. Use the JS console instead:

**Option A — QR code login** (simplest):
Click **Log In** and choose **Log in with QR Code**. Scan from the Discord mobile app (Settings → Scan QR Code).

**Option B — Credential login via JS console**:
1. Click **Log In** to show the form
2. Find input fields:
   ```js
   browser_console({ expression: "document.querySelectorAll('input')" })
   ```
3. Set values using React-compatible native setter — `.value =` alone does NOT trigger Discord's React onChange:
   ```js
   browser_console({
     expression: `
       const email = document.querySelector('input[name="email"]');
       const pass = document.querySelector('input[name="password"]');
       const setter = Object.getOwnPropertyDescriptor(
         Object.getPrototypeOf(email), 'value'
       ).set;
       setter.call(email, 'user@example.com');
       email.dispatchEvent(new Event('input', {bubbles: true}));
       email.dispatchEvent(new Event('change', {bubbles: true}));
       setter.call(pass, 'password123');
       pass.dispatchEvent(new Event('input', {bubbles: true}));
       pass.dispatchEvent(new Event('change', {bubbles: true}));
     `
   })
   ```
4. Click the submit button:
   ```js
   browser_console({
     expression: "document.querySelector('button[type=\"submit\"]').click()"
   })
   ```

### Resetting the Bot Token

After clicking **Reset Token**, Discord requires either:
- **Account password** — enter in the MFA dialog's password field, then click **Submit**
- **Authenticator 2FA code** — click **Verify with something else** to switch methods, enter the code

Check for the verification dialog:
```js
// Find dialog contents
browser_console({
  expression: "Array.from(document.querySelectorAll('[role=\"dialog\"]')).map(d => d.innerText.substring(0, 500))"
})
// Find input fields in the dialog
browser_console({
  expression: "Array.from(document.querySelectorAll('[role=\"dialog\"] input')).map(i => ({id: i.id, placeholder: i.placeholder}))"
})
```

Once confirmed, the token appears on screen with a **Copy** button and the message "Be sure to copy it as it will not be shown to you again." Click **Copy** immediately via JS:

```js
browser_console({
  expression: "Array.from(document.querySelectorAll('button')).filter(b => b.innerText.includes('Copy')).forEach(b => b.click())"
})
```

Store the token immediately in Hermes `.env`:
```bash
echo 'DISCORD_BOT_TOKEN=<your-token>' >> ~/.hermes/.env
```

### Enabling Gateway Intents Programmatically

In the **Bot** section, scroll to **Privileged Gateway Intents**. The intents are rendered as `<input type="checkbox" role="switch">` elements — **not** regular buttons, so finding them via `browser_console` requires `[role="switch"]`:

```js
// Find all toggle switches and identify by aria-labelledby
browser_console({
  expression: `
    Array.from(document.querySelectorAll('[role="switch"]')).map((s, i) => {
      var labelId = s.getAttribute('aria-labelledby');
      var label = labelId ? (document.getElementById(labelId)?.innerText?.substring(0, 50) || '?') : '?';
      return i + ': checked=' + s.checked + ' ' + label;
    })
  `
})
```

Typical index mapping:
- Index 0: Public Bot toggle
- Index 1: OAuth2 Code Grant
- **Index 2: Presence Intent**
- **Index 3: Server Members Intent** (recommended)
- **Index 4: Message Content Intent** (required)

Enable by clicking:

```js
// Enable required intents
browser_console({
  expression: `
    var switches = document.querySelectorAll('[role="switch"]');
    switches[3].click();  // Server Members Intent
    switches[4].click();  // Message Content Intent
  `
})
```

**Required:** Message Content Intent is mandatory for the bot to read any message content. Without it, the bot sees only message IDs and metadata.

### Navigating the Application

Once logged in, existing applications appear as links on the main page. Click them via JS:
```js
// Find and click an existing app
browser_console({
  expression: "Array.from(document.querySelectorAll('a')).filter(a => a.innerText.includes('MyAppName')).forEach(a => a.click())"
})
```

The left sidebar has navigation sections. Click them by matching text:
```js
// Navigate to Bot section
browser_console({
  expression: "Array.from(document.querySelectorAll('nav a, *')).filter(el => el.innerText?.trim() === 'Bot').forEach(el => el.click())"
})
```

## Step 2: Create a Discord Server (If You Don't Have One)

If you don't have a server to add the bot to, create one via the Discord web app at `https://discord.com/app`. Log in, then:

1. Click the **+** (Add a Server) icon at the bottom of the server list (left sidebar) — look for `aria-label="Add a Server"`
2. Choose **"Create My Own"**
3. Pick **"For me and my friends"** (or appropriate template)
4. Enter a server name (e.g. "Hermes HQ")
5. Click **Create**

The server is created with a default `#general` channel. You'll return to `discord.com/app` at `(4) Discord | #general | <ServerName>`.

### Browser Automation Notes

- The server creation flow is a multi-step dialog. Use `browser_console` with `querySelectorAll('[role="dialog"]')` to detect each step.
- Text inputs use React — `element.value = 'text'` alone won't work. Use the native setter + event dispatch pattern (see Step 1's React SPA workaround).
- The dialog has two inputs: a file input (icon) and a text input (name). Find the text input by filtering for `type="text"`.

## Step 3: Invite the Bot to Your Server

Build the invite URL:
```
https://discord.com/api/oauth2/authorize?client_id=CLIENT_ID&permissions=PERMISSIONS&scope=bot
```

- **CLIENT_ID**: Found in **OAuth2 → General** → **Client ID** (copy it)
- **PERMISSIONS**: Use the Permission Calculator or these common values:
  - `268446726` — Read Messages, Send Messages, Read Message History, Embed Links, Attach Files, Add Reactions, Use External Emoji
  - `8` — Administrator (most permissive; handles channel creation, webhooks, all permissions)
  - `274877991936` — Same as first + Manage Channels, Manage Webhooks

Open the URL in a browser. If you're already logged into Discord in that browser, it shows your avatar and a server dropdown.

### OAuth Scroll-to-Reveal Flow

The Authorize page uses a scroll-based reveal pattern. The button text transitions through:
1. **"Keep Scrolling..."** — you must scroll within the **`.body__8a031` container** (NOT `window`). Find it via:
   ```js
   document.querySelector('.body__8a031').scrollTop = document.querySelector('.body__8a031').scrollHeight;
   ```
2. **"Continue"** — appears after scrolling. Click to proceed to the permission confirmation page.
3. **"Authorise"** — appears on the permission confirmation page showing the exact permissions the bot will receive (e.g. "Administrator"). Scroll the body container again if hidden.
4. **hCaptcha** — After clicking Authorise, Discord may present an hCaptcha challenge ("Please confirm you're not a robot"). This **cannot be bypassed programmatically**. You must either:
   - Share a screenshot and ask the user to solve it
   - Use `browser_get_images` or `browser_vision` (if available) to let them see the CAPTCHA

**Automatic note:** The OAuth state persists in the browser session. If the user solves the CAPTCHA and the bot appears in the server, the setup is complete from Discord's side.

### Direct Navigation to Bot Section

Once logged into the Developer Portal, you can navigate directly to the Bot section without clicking through the sidebar:
```
https://discord.com/developers/applications/{APPLICATION_ID}/bot
```
Get the `APPLICATION_ID` from the URL when viewing any app page (e.g., `https://discord.com/developers/applications/123456789/information` → ID is `123456789`).

## Step 4: Create Server Channels (via Discord API)

Once the bot is in your server with Administrator permissions, create channels programmatically. First get the guild (server) ID:

```bash
# List guilds the bot can see
curl -s -H "Authorization: Bot $DISCORD_BOT_TOKEN" \
  https://discord.com/api/v10/users/@me/guilds | python3 -m json.tool
```

Create channels:

```bash
GUILD_ID="your_server_id_here"

# Create #general
curl -s -X POST -H "Authorization: Bot $DISCORD_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"general","type":0}' \
  https://discord.com/api/v10/guilds/$GUILD_ID/channels

# Create #daily-digest - for automated daily summaries
curl -s -X POST -H "Authorization: Bot $DISCORD_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"daily-digest","type":0,"topic":"Automated daily summaries from Hermes"}' \
  https://discord.com/api/v10/guilds/$GUILD_ID/channels

# Create #content-ideas
curl -s -X POST -H "Authorization: Bot $DISCORD_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"content-ideas","type":0,"topic":"AI-generated content suggestions and inspiration"}' \
  https://discord.com/api/v10/guilds/$GUILD_ID/channels

# Create #scripts
curl -s -X POST -H "Authorization: Bot $DISCORD_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"scripts","type":0,"topic":"Code scripts, automation output, and terminal results"}' \
  https://discord.com/api/v10/guilds/$GUILD_ID/channels
```

Channel types: `0` = text, `2` = voice, `5` = announcement, `15` = forum

> 📘 See `references/discord-api-channel-setup.md` for copy-paste-ready commands with channel ID lookup.

**Standard Hermes channel layout:**

| Channel | Purpose |
|---------|---------|
| #general | Main communication — Hermes responds here |
| #daily-digest | Automated daily summaries/reports (cron job output) |
| #content-ideas | Ideas, research, inspiration (content brainstorming) |
| #scripts | Code scripts, automation output, terminal results |

## Step 5: Configure Hermes Agent

Add the bot token to `~/.hermes/.env` (NOT `config.yaml`):

```bash
echo 'DISCORD_BOT_TOKEN=<your-token>' >> ~/.hermes/.env
```

The `discord:` section in `~/.hermes/config.yaml` is auto-generated on first run. Common adjustments:

```yaml
discord:
  require_mention: true            # Bot only responds when @mentioned
  free_response_channels: ''        # Channels where bot responds without mention (comma-separated names)
  allowed_channels: ''              # Restrict to specific channels only (comma-separated IDs)
  auto_thread: true                 # Auto-create threads for conversations
  thread_require_mention: false     # Require mention in threads too
  history_backfill: true            # Load recent message history
  history_backfill_limit: 50        # Messages to backfill
  reactions: true                   # React to messages
  channel_prompts: {}               # Per-channel prompt overrides (see below)
  dm_role_auth_guild: ''            # Guild ID for DM role-based auth
  server_actions: ''                # Guild ID for server-level actions
  allow_any_attachment: false       # Allow non-image attachments
  max_attachment_bytes: 33554432    # Max attachment size (32 MB)
```

**Free response mode** (bot responds in specific channels without @mention):

```yaml
discord:
  require_mention: false
  free_response_channels: 'general,daily-digest,content-ideas,scripts'
```

**Restrict to specific channels by ID**:

```yaml
discord:
  allowed_channels: '123456789,987654321'  # Channel IDs in server
```

**Per-channel prompt overrides** — give the bot different instructions in different channels:

```yaml
discord:
  channel_prompts:
    daily-digest: "You are a daily digest assistant. Summarize the day's events concisely."
    content-ideas: "You brainstorm content ideas and creative projects."
    scripts: "You write and explain code, scripts, and automation workflows."
```

**IMPORTANT:** Token goes in `.env`, not in `config.yaml`. The gateway reads `DISCORD_BOT_TOKEN` from the environment at startup.

Then restart the gateway:
```
hermes gateway restart
```

Verify connection:
```bash
grep -E "(discord|connected|failed)" ~/.hermes/logs/gateway.log | tail -10
```

## Step 6: Configure Delivery Channels

Once the gateway is running, list available targets:

```
hermes gateway targets
```

Or via the `send_message` tool with `action='list'`.

### Setting Up Server Channels

The user typically wants these channels for a Hermes agent:
- `#general` — Main communication channel
- `#daily-digest` — Automated daily summaries/reports
- `#content-ideas` — Ideas, research, and inspiration
- `#scripts` — Code scripts, automation output, terminal results

Channels can be created manually via Discord UI or programmatically via the Discord API.

### Delivery Targeting

When using `send_message`, format targets as:
- `discord` — Sends to the home/default channel
- `discord:guild_id` — Sends to the server's default system channel
- `discord:channel_id` — Sends to a specific channel
- `discord:channel_id:thread_id` — Sends to a specific thread

Use `send_message(action='list')` to discover available targets after the gateway is running.

## Step 7: Cron Job Delivery to Discord

When creating cron jobs for Discord delivery, set deliver to the channel target:

```yaml
deliver: "discord:123456789"  # specific channel
```

## Troubleshooting

| Problem | Likely Fix |
|---------|------------|
| Bot doesn't appear in server | Re-invite with correct permissions |
| Token not found | Go to Dev Portal → Bot → Reset Token |
| "Missing Access" errors | Bot needs Read Messages + Send Messages perms |
| Channel ID not found | Right-click channel → Copy ID (Dev Mode must be ON in Discord) |

### Discord Developer Mode

To see channel IDs:
1. Discord Settings → Advanced → **Developer Mode** ON
2. Right-click any channel → **Copy ID**

## Managing Pinned Messages via the Discord API

Pinning messages and updating pinned content is a common pattern for reference channels (#rules, #links, #notes).

### Pin a Message

```python
import urllib.request
req = urllib.request.Request(
    f'https://discord.com/api/v10/channels/{channel_id}/pins/{message_id}',
    data=b'',  # Empty body required
    method='PUT'
)
with urllib.request.urlopen(req) as resp:
    print(f'Pinned! Status: {resp.status}')  # 204 No Content on success
```

The response is HTTP 204 (no JSON body). On failure, catch `urllib.error.HTTPError`.

### Update a Pinned Message

Pinned messages can be edited just like any other message:

```python
import json, urllib.request
req = urllib.request.Request(
    f'https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}',
    data=json.dumps({'content': 'Updated content'}).encode(),
    headers={'Content-Type': 'application/json'},
    method='PATCH'
)
with urllib.request.urlopen(req) as resp:
    updated = json.loads(resp.read().decode())  # Returns full message object
```

### Python API Access Pattern (for Cron Scripts)

When writing Discord API scripts for cron jobs (no-agent watchdog mode), use this pattern for reliable authentication:

```python
from dotenv import load_dotenv
import os, json, urllib.request

load_dotenv(os.path.expanduser('~/.hermes/.env'))
TOKEN = os.environ.get('DISCORD_BOT_TOKEN', '')

# Install global opener with consistent headers
opener = urllib.request.build_opener()
opener.addheaders = [
    ('User-Agent', 'DiscordBot (HermesAgent, 1.0)'),
    ('Authorization', f'Bot {TOKEN}')
]
urllib.request.install_opener(opener)

def api(method, path, data=None):
    """Call Discord REST API. Returns parsed JSON or empty dict on 204."""
    req = urllib.request.Request(
        f'https://discord.com/api/v10{path}',
        data=json.dumps(data).encode() if data else None,
        headers={'Content-Type': 'application/json'} if data else {},
        method=method
    )
    with urllib.request.urlopen(req) as resp:
        body = resp.read()
        return json.loads(body) if body else {}
```

### Common Pitfalls

- **`PUT` vs `POST`**: Pinning uses `PUT` with an empty body (`data=b''`). Do NOT use `POST`.
- **204 responses**: Pin operations return HTTP 204 with no body. Don't try to parse JSON — check for empty body.
- **403/Missing Permissions**: The bot needs `Manage Messages` permission to pin. Administrator permission includes this, but channel-level permission overwrites can block it. If you get error `10103` ("Missing Permissions"), check the channel's permission overwrites.
- **Message ownership**: Any bot can pin any message in channels where it has Manage Messages. You don't need to own the message.

## Auto-Maintaining a Channel Index with a Cron Watchdog

For channels like `#notes` or `#links` where users drop URLs, reference material, or assets, set up a **no-agent watchdog cron** that keeps a pinned master index in sync.

### The Pattern

1. **Create the channel** with a descriptive topic
2. **Post an initial master message** compiling everything known
3. **Pin that message** so it stays at the top
4. **Deploy a no-agent cron script** that periodically:
   - Fetches all non-bot messages in the channel
   - Extracts new links/references
   - Merges them into the existing pinned message
   - Patches the pinned message with the updated content

### Script Template

A full working example is available at `scripts/notes-index-watchdog.py`. Key design decisions:

- **No-agent mode** (`no_agent: true`) — the script runs as a plain Python process with no LLM overhead. Only non-empty stdout is delivered to the user.
- **Dotenv-based auth** — reads `DISCORD_BOT_TOKEN` from `~/.hermes/.env` via `python-dotenv`.
- **Idempotent merge** — only adds entries not already present in the pinned message, so running every 3h is safe.
- **Silent when unchanged** — exits with status 0 and empty stdout when there's nothing new, so the user gets no noise.

### Cron Setup

```bash
# Register the watchdog (run inside a Hermes session)
cronjob action=create \
  name=notes-index-updater \
  schedule="every 3h" \
  no_agent=true \
  script=notes-index-watchdog.py
```

The script lives in `~/.hermes/scripts/` (the default script directory for cron jobs).

### When to Use This Pattern

- **#notes** — master link directory (as built in this session)
- **#daily-digest** — collating user-submitted updates into a daily summary
- **#links / #resources** — any channel where reference material is crowdsourced
- **#changelog** — aggregating release notes from multiple sources

## Pitfalls

- **Token security**: Never commit the bot token to git. Use Hermes vault (`hermes-vault` skill) or env vars.
- **Permission scope**: The bot must have both the right OAuth2 scopes AND server-level permissions.
- **Message intent**: For privileged intents (message content, member list), enable them in Dev Portal → Bot → Privileged Gateway Intents. Message Content Intent is required for the bot to read message content in DMs and servers with >100 users.
- **Rate limits**: Discord API rate limits apply (50 req/s per endpoint). Keep cron job frequency reasonable.
- **PrivilegedIntentsRequired crash**: If the bot hasn't enabled the intents it's requesting (Message Content, Server Members, Presence), the gateway fails with `discord.errors.PrivilegedIntentsRequired` and enters a reconnect loop with exponential backoff (30s → 120s → 240s → 300s). The error appears in journalctl as: `RuntimeError: Shard ID None is requesting privileged intents`. Fix: enable the required intents at https://discord.com/developers/applications → Bot → Privileged Gateway Intents, then restart the gateway with `systemctl --user restart hermes-gateway`. systemd may auto-restart once after the crash (producing a brief "FAILURE" + a successful restart with a new PID), but it will keep failing until the intents are actually enabled. To verify the fix worked, check `journalctl --user -u hermes-gateway --no-pager -n 10` for 0 Discord errors after restart.
- **React SPA accessibility**: `browser_snapshot` often returns empty or partial views for Discord's React-rendered pages. When you see "(empty page)" but know the page loaded (check via `browser_console` JS), use `browser_console({expression: '...'})` for all DOM interaction instead — query inputs, set values with native setters, dispatch events, and click buttons programmatically. Never rely on ref IDs from snapshots for Discord.
- **React form value binding**: Setting `element.value = 'text'` programmatically does NOT trigger Discord's React onChange handler. Always use the native setter pattern: `Object.getOwnPropertyDescriptor(Object.getPrototypeOf(element), 'value').set.call(element, 'text')` then dispatch `new Event('input', {bubbles: true})` and `new Event('change', {bubbles: true})`.
- **Token reset requires verification**: Clicking "Reset Token" opens a confirmation dialog ("Reset Bot's Token?") with "Yes, do it!". After confirming, Discord prompts for account password or 2FA code as a security check. Do not report the token as ready until you handle this step — the token value is only shown after successful verification.
- **Copy button after reset**: After successful password/2FA verification, Discord shows the token with a prominent **Copy** button and the text "Be sure to copy it as it will not be shown to you again." Click it immediately. If no visible text button appears, check for a small copy-icon button next to the token display field.
- **OAuth scroll-reveal**: The Authorize page hides the "Continue"/"Authorise" buttons behind a scrollable `.body__8a031` container. `window.scrollTo()` will NOT work — you must scroll the body container programmatically: `document.querySelector('.body__8a031').scrollTop = el.scrollHeight`.
- **hCaptcha at authorization**: Discord's OAuth flow may present an hCaptcha challenge after clicking "Authorise". The bot only appears in the server after the CAPTCHA is solved. This is a human-in-the-loop step — do not report the bot as authorized until you verify it actually joined the server. Share a screenshot to let the user solve it.
- **Server creation via web app**: If the user has no server, create one at `discord.com/app` before the invite step. The creation flow is a React multi-step dialog — detect each step via `[role="dialog"]` selectors and verify the final URL contains the new server name in the page title.
