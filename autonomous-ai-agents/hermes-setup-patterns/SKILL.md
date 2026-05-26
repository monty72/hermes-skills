---
name: hermes-setup-patterns
description: "Common gotchas, workarounds, and setup patterns for configuring and installing Hermes Agent — gateway service, Telegram/Discord platforms, credential setup, and non-interactive automation of hermes CLI wizards."
version: 1.0.0
author: Agent
created_by: agent
---

# Hermes Setup Patterns

Known workarounds and patterns for Hermes setup that go beyond the CLI reference in the bundled `hermes-agent` skill. These cover non-obvious behaviors that can trip up automated or non-interactive setup.

## Gateway Service Installation (`hermes gateway install`)

### Two-Prompt Gotcha

`hermes gateway install` asks **two consecutive `[Y/n]` prompts**:

1. "Start the gateway now after installing the service?"
2. "Start the gateway automatically on login/boot with systemd?"

A single `echo "Y" | hermes gateway install` only answers the first prompt and then either hangs or exits — it does **not** reach the second prompt.

**Correct approach** — pipe both answers:

```bash
printf "Y\nY\n" | hermes gateway install
```

This answers "yes" to both prompts: start now + enable on boot.

### Linger for SSH Sessions

The installer automatically runs `sudo loginctl enable-linger $USER` so the user service survives SSH logout. If the user skips this or runs `hermes gateway start` manually later and the gateway dies on logout, run:

```bash
sudo loginctl enable-linger $USER
```

### Service Lifecycle

```bash
hermes gateway start      # Start the systemd user service
hermes gateway stop       # Stop it
hermes gateway restart    # Restart
hermes gateway status     # Check if running
journalctl --user -u hermes-gateway -f   # Watch live logs
systemctl --user reset-failed hermes-gateway   # Reset crash-loop state
```

## Checking Platform Status

Before running the gateway, check what's configured:

```bash
hermes config | grep -A 10 "Messaging"
```

Or just `hermes config` and look for the "Messaging Platforms" section.

## Running Gateway in Foreground (Testing)

```bash
hermes gateway run
```

This runs in the terminal foreground — good for testing. Press Ctrl+C to stop. When running in the background (via `terminal(background=true)`), verify readiness by checking the gateway log:

```bash
cat ~/.hermes/logs/gateway.log | grep -E "(connected|failed to connect)"
```

## Reading Gateway Logs

```bash
grep -E "(connected|failed|error)" ~/.hermes/logs/gateway.log | tail -20
journalctl --user -u hermes-gateway -n 50 --no-pager   # When running as a service
```

## Non-Interactive Setup

Some `hermes setup` wizards also have multi-prompt flows. If you hit a wizard that asks multiple questions, use `printf` with the expected number of answers rather than `echo`:

```bash
printf "answer1\nanswer2\nanswer3\n" | hermes setup [section]
```

## Web Search Backend Configuration

Hermes supports multiple web search backends. The Brave Search API has a generous free tier (2,000 queries/month) and is the easiest to set up.

### Setup Steps

1. Get a Brave Search API key from https://brave.com/search/api/ (free tier available)
2. Add the key to `.env`:
   ```
   BRAVE_SEARCH_API_KEY=BSA...
   ```
3. Configure the web tool to use it:
   ```bash
   hermes config set web.search_backend brave_free
   hermes config set web.extract_backend brave_free
   ```
4. Register it in the credential pool:
   ```bash
   hermes auth add
   # Or manually store in the vault if using hermes-vault
   source ~/.hermes/.env.local 2>/dev/null
   hermes-vault set BRAVE_SEARCH_API_KEY "BSA..."
   ```
5. Restart the gateway:
   ```bash
   hermes gateway restart
   ```

### Verification

The Brave backend is a plugin (`plugins/web/brave_free/plugin.yaml`). Check the plugin is available:

```bash
ls ~/.hermes/hermes-agent/plugins/web/brave_free/plugin.yaml
```

Then test in a new session — the web toolset should be available (requires `/reset` to pick up config changes).

### Available Backends

| Backend | Config value | API Key Env Var | Notes |
|---------|-------------|-----------------|-------|
| Brave Free | `brave_free` | `BRAVE_SEARCH_API_KEY` | Free, 2K queries/mo |
| Brave (paid) | `brave` | `BRAVE_SEARCH_API_KEY` | Paid, higher rate limits |
| Exa | `exa` | `EXA_API_KEY` | AI-native search, paid |
| Tavily | `tavily` | `TAVILY_API_KEY` | AI-optimized search, paid |
| Firecrawl | `firecrawl` | `FIRECRAWL_API_KEY` | Search + crawl + extract, paid |
| Parallel | `parallel` | `PARALLEL_API_KEY` | Search + extract, paid |
| SearXNG | `searxng` | None (self-hosted URL) | Self-hosted meta-search |

### Credential Loading

Web search API keys must be in `.env` — they're loaded by the gateway's `load_hermes_dotenv()` at startup. If using the vault, restore them to `.env` after vault migration:

```bash
python3 -c "
import os
path = os.path.expanduser('~/.hermes/.env')
with open(path) as f:
    content = f.read()
import subprocess
val = subprocess.run(['hermes-vault', 'get', 'BRAVE_SEARCH_API_KEY'], capture_output=True, text=True).stdout.strip()
content = content.replace('BRAVE_SEARCH_API_KEY=***', f'BRAVE_SEARCH_API_KEY={val}')
with open(path, 'w') as f:
    f.write(content)
print('Restored')
"
```

## Gateway Restart Protocol

Gateway restart kills the active agent session. Never do it while the user is mid-conversation:

1. Save any config changes to `.env` or `config.yaml`
2. **Wait for a natural break** in the conversation or ask the user
3. Only then: `hermes gateway restart`
4. Check logs to verify all platforms connected:
   ```bash
   grep -E "(connected|failed)" ~/.hermes/logs/gateway.log | tail -10
   ```

## Image Generation Setup

### Setup via OpenAI (`OPENAI_API_KEY`)

OpenAI's image generation (`gpt-image-2`) is available if you have an OpenAI API key with credits.

#### Setup Steps

1. Get an OpenAI API key from https://platform.openai.com/api-keys
2. Add to `.env`:
   ```
   OPENAI_API_KEY=sk-proj-...
   ```
3. The `image_gen` toolset is already enabled by default
4. Restart the gateway: `hermes gateway restart`
5. The agent can now generate images via the `image_gen` tool

#### Available Models

```
gpt-image-1, gpt-image-1-mini, gpt-image-1.5
gpt-image-2, gpt-image-2-2026-04-21
chatgpt-image-latest
```

DALL-E 3 is NOT available as a model name via the API for some accounts — use `gpt-image-2` instead.

#### Verification

```bash
curl -s --max-time 60 https://api.openai.com/v1/images/generations \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-image-2","prompt":"a cute cat","n":1,"size":"1024x1024"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if 'data' in d else d.get('error',{}).get('message','?'))"
```

#### Common Issues

- **"Billing hard limit has been reached"** — the key is valid but the account needs credits. Top up at https://platform.openai.com/settings/organization/billing
- **"The model 'dall-e-3' does not exist"** — use `gpt-image-2` instead

#### Bonus: OpenAI Key Unlocks Multiple Tools

A single `OPENAI_API_KEY` also covers:
- **Vision fallback** (gpt-4o analysis)
- **STT** (Whisper transcription) via `VOICE_TOOLS_OPENAI_KEY`
- **TTS** (voice responses)
- **Optional fallback model**

### Setup via FAL.ai (`FAL_KEY`)

FAL.ai is another image generation backend (flux models, recraft, etc.).

### Setup Steps

1. Sign up at https://fal.ai and get an API key from the dashboard
2. Add the key to `.env`:
   ```
   FAL_KEY=your-key-here
   ```
3. The `image_gen` toolset is already enabled by default — no config change needed
4. Restart the gateway: `hermes gateway restart`
5. Test in a new session with `/reset`

### Verification

```bash
curl -s -X POST "https://fal.run/fal-ai/flux-pro/v1.1-ultra" \
  -H "Authorization: Key $FAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"a cat","image_size":"square_hd","num_images":1}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('images',[{}])[0].get('url','')[:60] if 'images' in d else d.get('detail','unknown error'))"
```

### Alternative Providers

| Provider | Env Var | Model | Notes |
|----------|---------|-------|-------|
| FAL.ai | `FAL_KEY` | flux-pro, flux-klein, recraft | Popular, needs credit balance |
| OpenAI | `OPENAI_API_KEY` | gpt-image-2, dall-e-3 | Needs OpenAI API key with credits |

### Common Issues

- **"User is locked" / "Exhausted balance"** — top up at https://fal.ai/dashboard/billing
- **Image gen tool says "system dependency not met"** — check that `FAL_KEY` is in `.env` and the gateway has been restarted

## Terminal Output Redacts Secrets (Display vs Reality)

**Key insight:** When you read `.env` or check credential values via terminal commands, the shell/system may **mask** patterns that look like secrets (`sk-...`, `AIza...`, `eyJ...` JWT tokens, `***`) in displayed output. This means `grep DEEPSEEK_API_KEY .env` can show `DEEPSEEK_API_KEY=***` while the file actually contains the real key.

### How to Verify the True State

Don't trust displayed output — check programmatically:

```bash
# Check by value length (*** is 3 chars, real keys are 30+)
python3 -c "
import os
with open(os.path.expanduser('~/.hermes/.env')) as f:
    for line in f:
        if line.startswith('DEEPSEEK_API_KEY='):
            val = line.split('=', 1)[1].strip()
            print(f'len={len(val)}, starts={val[:10]}...')
"
# Real key = len > 10. Placeholder '***' = len == 3.
```

Or check the raw file bytes:

```bash
# Use od to see the actual characters (bypasses terminal masking)
sed -n '<line_number>p' ~/.hermes/.env | od -c
```

### Common Confusion Paths

1. You run `sed -i 's/***/real-key/' .env` — output says nothing changed. **Check with the Python length method above** — the file probably already has the real key and the shell is masking it.
2. You write to a temp file, read it back, and see `***`. **Same thing** — the terminal masks any value on output.
3. `python3 -c` that reads and prints the value also gets masked if it hits stdout.

**Never trust terminal display for credential values.** Always verify by length or byte inspection.

## Credential Restoration After Vault Sanitization

When using `hermes-vault` for secret management, stripping secrets from `.env` can leave the gateway unable to read credentials. The restoration process:

### Problem

During vault migration, the agent replaces real secret values in `.env` with `***`. The gateway reads `.env` via `load_hermes_dotenv()` (python-dotenv) and gets `***` instead of the real key.

### Restoration

```bash
export PATH="$HOME/.local/bin:$PATH"
source ~/.hermes/.env.local 2>/dev/null

python3 << 'PYEOF'
import os, subprocess

def vault_get(key):
    r = subprocess.run(["hermes-vault", "get", key], capture_output=True, text=True)
    return r.stdout.strip()

env_path = os.path.expanduser("~/.hermes/.env")
with open(env_path) as f:
    content = f.read()

key_map = {
    "DEEPSEEK_API_KEY": "DEEPSEEK_API_KEY",
    "TELEGRAM_BOT_TOKEN": "TELEGRAM_BOT_TOKEN",
    "HASS_TOKEN": "HASS_TOKEN",
    "GOOGLE_API_KEY": "GOOGLE_API_KEY",
    "BRAVE_SEARCH_API_KEY": "BRAVE_SEARCH_API_KEY",
    "FAL_KEY": "FAL_KEY",
}

for vault_key, env_key in key_map.items():
    val = vault_get(vault_key)
    if val and len(val) > 5 and val != "***":
        old = f"{env_key}=***"
        new = f"{env_key}={val}"
        if old in content:
            content = content.replace(old, new)
            print(f"Restored: {env_key}")

with open(env_path, 'w') as f:
    f.write(content)
print("Done")
PYEOF
```

### Pitfall: Terminal Output Redaction During Vault Operations

When running `hermes-vault get KEY` or `hermes-vault set KEY VALUE`, the terminal output displays the value as `***`. This is **not** the vault storing bad data — it's the terminal masking secrets on display.

However, there IS a real pitfall: **if you vault a value that is already `***`** (because `.env` was sanitized before vaulting), the vault stores `***` as the actual encrypted value. This creates a circular problem where the vault only has the placeholder.

**Prevention:** Always get the real key from the provider dashboard and vault it directly, never vault from a sanitized `.env`.

**Detection:**
```bash
python3 -c "
import subprocess
r = subprocess.run(['hermes-vault', 'get', 'SOME_KEY'], capture_output=True, text=True)
print(f'len={len(r.stdout.strip())}')
"
# len = 3 → vaulted '***' (corrupt)
# len > 10 → real key
```

If the vault was initialized after the `***` replacement, the vault itself may store `***` as the credential value. The real key must be re-obtained from the original source (provider dashboard) and re-added:

```bash
hermes-vault set DEEPSEEK_API_KEY "real-key-here"
```

Check vault contents safely:
```bash
python3 -c "
import subprocess
r = subprocess.run(['hermes-vault', 'get', 'DEEPSEEK_API_KEY'], capture_output=True, text=True)
val = r.stdout.strip()
print(f'Vaulted key: len={len(val)}, starts={val[:10]}...')
"
```

Value length of 3 = `***` (stale). Value length > 10 = real.

### Home Assistant Token Restoration (Specific Example)

HA auth failures after vault migration are typically caused by `HASS_TOKEN=***` in `.env`:

1. Get token from vault: `hermes-vault get HASS_TOKEN`
2. Restore to `.env` using the script above
3. Verify: `curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $HASS_TOKEN" http://192.168.1.146:8123/api/`
4. Restart gateway: `hermes gateway restart`
5. Check logs: `grep homeassistant ~/.hermes/logs/gateway.log`

## Model Cost Management

See `references/model-cost-management.md` for the full strategy — cheapest model per provider, auto-cron job for daily cheapest check, and switching instructions.

Key points:
- DeepSeek `deepseek-v4-flash` is generally the cheapest model available
- OpenAI `gpt-5.4-nano` is the cheapest OpenAI model
- Set `fallback_providers` as a JSON string in config.yaml for reliability
- GPT-5.x models use `max_completion_tokens` not `max_tokens`

## Image Generation via OpenAI (Response Format Quirk)

OpenAI's `gpt-image-2` model returns images as `b64_json` (base64 PNG data), **not** as a URL. The response has no `url` field:

```json
{
  "created": ...,
  "data": [{"b64_json": "iVBORw0KGgo..."}],
  "output_format": "png"
}
```

The `url` field doesn't even exist in the response — it's `b64_json` only. This is different from DALL-E 3 which returns a URL. Code that expects `data[0].url` will crash with `KeyError`.

To display the image, save the base64 to a file:
```python
import base64
png_data = base64.b64decode(response["data"][0]["b64_json"])
with open("/tmp/output.png", "wb") as f:
    f.write(png_data)
```

Also note: `gpt-image-2` accepts `size: "1024x1024"` and `quality: "standard"|"low"`.

## Resources

- Docs: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/
- Config reference: https://hermes-agent.nousresearch.com/docs/user-guide/configuration
- The bundled `hermes-agent` skill (`autonomous-ai-agents/hermes-agent`) has the full CLI reference
- FAL.ai docs: https://fal.ai/docs
- Model cost management: `references/model-cost-management.md`
