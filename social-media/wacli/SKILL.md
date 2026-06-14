---
name: wacli
description: Send WhatsApp messages to other people or search/sync WhatsApp history via the wacli CLI (not for normal user chats). Install is via `go install github.com/openclaw/wacli/cmd/wacli@latest` (package renamed from steipete/wacli).
homepage: https://wacli.sh
metadata: {"openclaw":{"emoji":"📱","requires":{"bins":["wacli"]},"install":[{"id":"brew","kind":"brew","formula":"steipete/tap/wacli","bins":["wacli"],"label":"Install wacli (brew)"},{"id":"go","kind":"go","module":"github.com/openclaw/wacli/cmd/wacli@latest","bins":["wacli"],"label":"Install wacli (go)"}]}}
---

# wacli

WhatsApp CLI for syncing, searching, and sending messages from the terminal. Useful for replying to estate agents, handling property enquiries, or any third-party WhatsApp communication the user delegates.

## Installation

```
go install github.com/openclaw/wacli/cmd/wacli@latest
```

**Pitfall:** The package was renamed from `steipete/wacli` → `openclaw/wacli`. Using the old import path will fail with `module declares its path as .../openclaw/wacli but was required as .../steipete/wacli`. Always use `openclaw`.

After install, ensure `$HOME/go/bin` is on your PATH.

## Authentication

Two methods — QR or phone number.

**QR (headless server friendly):**
```
wacli auth --qr-format terminal
# Shows QR code as ASCII art — share the screenshot with the user to scan
```

**Phone number (better for remote/Telegram users):**
```
wacli auth --qr-format text --phone "+447123456789"
# Outputs a pairing code like XN8W-YB7B
```
User goes to WhatsApp → Linked Devices → Link a Device → Link with phone number → enters the code.

**Check status:**
```
wacli auth status
```

## Usage

### Read messages
```
wacli chats list --limit 20 --query "name or number"
wacli messages search "query" --limit 20 --chat <jid>
wacli messages search "invoice" --after 2025-01-01 --before 2025-12-31
```

### Send messages
```
wacli send text --to "+447123456789" --message "Thanks for your message"
wacli send file --to "+447123456789" --file /path/doc.pdf --caption "Documents"
wacli send text --to "1234567890-123456789@g.us" --message "Group message"
```

### Sync
```
wacli sync --follow          # continuous sync
wacli history backfill --chat <jid> --requests 2 --count 50
```

## Use Cases

- **Property agent comms:** User shares a WhatsApp thread ID, you read and reply on their behalf
- **Delegated negotiation:** User says "handle the back-and-forth on St. Anns Road" — you monitor the thread and respond autonomously
- **Forwarding:** Read agent messages on WhatsApp, summarise/amplify to user on their preferred channel (Telegram)

## Pitfalls

- JIDs: direct chats look like `<number>@s.whatsapp.net`; groups look like `<id>@g.us`
- Always require explicit recipient + message text before sending
- Backfill requires the user's phone to be online
- Store in ~/.wacli (override with --store)
- Use `--json` for machine-readable output when parsing in scripts
