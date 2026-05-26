# Hermes Credential Management

## Overview

Hermes has **three layers** where credentials (API keys, tokens) live, and understanding the relationship between them is critical for troubleshooting gateway platform failures.

| Layer | File | How it's loaded | Gateway impact |
|-------|------|-----------------|----------------|
| **Primary (.env)** | `~/.hermes/.env` | `python-dotenv` via `hermes_cli/env_loader.py::load_hermes_dotenv()` — loaded at startup | **Critical.** Gateway reads EVERYTHING from here. If a key is `***` or missing here, that platform won't connect. |
| **Credential Pool** | `~/.hermes/auth.json` | Managed via `hermes auth add/list/remove/reset` — used for provider API key rotation and OAuth tokens | Used at runtime for API calls, but **not** a substitute for `.env` at gateway startup |
| **Local Vault (hermes-vault)** | `~/.hermes-vault/vault.json` (AES-256-GCM encrypted) | Managed via `hermes-vault` CLI — reads via `hermes-vault get KEY` | NOT read by gateway. Only accessible via the vault CLI tool. |

## The Critical Gap

The gateway **only loads `~/.hermes/.env`**. If you strip secrets from `.env` and move them to the vault, the gateway will fail to connect to those platforms with errors like:

```
ERROR gateway.platforms.homeassistant: Auth failed: {'type': 'auth_invalid', 'message': 'Invalid access token or password'}
```

Even if the credential pool (`auth.json`) has the real key, the gateway bootstrap step reads from `.env` — not the pool.

## How `env_loader.py` Works

Source: `~/.hermes/hermes-agent/hermes_cli/env_loader.py`

```python
def load_hermes_dotenv(*, hermes_home=None, project_env=None):
    user_env = Path(hermes_home or ...) / ".env"
    
    if user_env.exists():
        _load_dotenv_with_fallback(user_env, override=True)
    
    if project_env_path and project_env_path.exists():
        _load_dotenv_with_fallback(project_env_path, override=not loaded)
    
    _apply_external_secret_sources(home_path)  # Bitwarden only, not hermes-vault
```

Key points:
- Only loads `~/.hermes/.env` (and optionally a project `.env`)
- Does NOT load `.env.local` — `.local` files are ignored
- Bitwarden Secrets Manager is the ONLY external secret source supported out of the box
- The `hermes-vault` is NOT integrated into the startup flow

## Credential Pool Startup Interaction

At startup, the credential pool in `auth.json` does NOT feed into the gateway's platform connection logic. Platform adapters (Telegram, Discord, Home Assistant, etc.) read their tokens directly from `os.environ` (populated by `.env` loading), not from the pool.

The pool is used at runtime for:
- LLM provider API key rotation (DeepSeek, OpenRouter, etc.)
- OAuth token refresh
- Automatic failover between multiple keys

## Troubleshooting Gateway Auth Failures

### Step 1: Check the logs
```bash
tail -30 ~/.hermes/logs/gateway.log
```

Look for:
- `Auth failed` — wrong or missing token
- `No ... token configured` — key not in `.env` at all
- `Invalid access token or password` — stale/wrong key

### Step 2: Verify the key in .env
```bash
# Check if the key is present (not ***)
python3 -c "
import os
with open(os.path.expanduser('~/.hermes/.env')) as f:
    for line in f:
        if line.startswith('HASS_TOKEN='):
            val = line.split('=', 1)[1].strip()
            print(f'Key length: {len(val)}')
            print(f'Is placeholder: {val == \"***\"}')
"
```

### Step 3: Restore a key from the vault
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

key_map = {"HASS_TOKEN": "HASS_TOKEN", "DEEPSEEK_API_KEY": "DEEPSEEK_API_KEY", "TELEGRAM_BOT_TOKEN": "TELEGRAM_BOT_TOKEN", "GOOGLE_API_KEY": "GOOGLE_API_KEY"}

for vault_key, env_key in key_map.items():
    val = vault_get(vault_key)
    if val and len(val) > 5 and val != "***":
        old = f"{env_key}=***"
        new = f"{env_key}={val}"
        if old in content:
            content = content.replace(old, new)

with open(env_path, 'w') as f:
    f.write(content)
PYEOF
```

### Step 4: Restore a key from the credential pool
```bash
python3 << 'PYEOF'
import os, json, subprocess

auth_path = os.path.expanduser("~/.hermes/auth.json")
with open(auth_path) as f:
    auth = json.load(f)

# Google keys live under "gemini" in the pool
for cred in auth.get("credential_pool", {}).get("gemini", []):
    key = cred.get("access_token", "")
    # Bitwarden-style value: the pool stores the raw token
    if key and key != "***":
        env_path = os.path.expanduser("~/.hermes/.env")
        with open(env_path) as f:
            content = f.read()
        content = content.replace("GOOGLE_API_KEY=***", f"GOOGLE_API_KEY={key}")
        with open(env_path, 'w') as f:
            f.write(content)
        print(f"Restored GOOGLE_API_KEY from pool: {key[:10]}...")
        break
PYEOF
```

### Step 5: Restart the gateway
```bash
hermes gateway restart
```

### Step 6: Verify in logs
```bash
sleep 3 && grep -E "^(✓|✗) (telegram|homeassistant|discord)" ~/.hermes/logs/gateway.log
```

## Platform-Specific Auth Notes

### Home Assistant
- Uses a **long-lived access token** from Home Assistant Profile page
- Stored as `HASS_TOKEN` in `.env`
- Format: `eyJhbGciOiJIUzI1NiIs...` (JWT-like base64 string)
- Connect URL: `HASS_URL=http://192.168.1.146:8123`
- Observed error when token is wrong: `Auth failed: {'type': 'auth_invalid', 'message': 'Invalid access token or password'}`
- Even with correct token, HA may log `No watch_domains, watch_entities, or watch_all configured. All state_changed events will be dropped.` — this is a warning, not an error.

### Telegram
- Stored as `TELEGRAM_BOT_TOKEN` in `.env`
- Format: `8784391265:AAH...` (bot token from @BotFather)
- Also needs `TELEGRAM_ALLOWED_USERS` and `TELEGRAM_HOME_CHANNEL`
- Observed error when token is wrong: silent failure or "Connection refused"

### Discord
- Stored as `DISCORD_BOT_TOKEN`
- Error when missing: `No bot token configured`
- **Must enable** Message Content Intent in Bot → Privileged Gateway Intents

### DeepSeek LLM
- Stored as `DEEPSEEK_API_KEY` in `.env`
- Format: `sk-dc...` (starts with `sk-`)
- Credential pool status: `auth failed invalid_request_error (401)` = wrong key
- `rate-limited (429)` = quota exceeded, will auto-retry
- Reset with: `hermes auth reset deepseek`

## Preventing Token Loss

When stripping secrets from `.env` and moving to vault:

1. **Store in vault first** before stripping from `.env`
2. **Verify vault round-trip works** before removing from `.env`
3. **Keep .env.local as a fallback** with `KEY=VALUE` format (not `export KEY=VALUE` — `python-dotenv` reads `KEY=VALUE` without `export` prefix)
4. The credential pool (`auth.json`) is NOT a suitable permanent store for platform tokens — it's designed for LLM provider keys with auth-type tracking and exhaustion/retry state

## Why Terminal Masks Secret Output

The terminal tool redacts values matching credential patterns (`sk-`, `AIza`, `eyJ...`, etc.) on display. This means `grep` / `cat` output will show `***` even when the file has the real key. To verify the actual value:

```bash
# Check by length
python3 -c "
with open(os.path.expanduser('~/.hermes/.env')) as f:
    for line in f:
        if line.startswith('DEEPSEEK_API_KEY='):
            val = line.split('=', 1)[1].strip()
            print(f'Key length: {len(val)}')
            print(f'Starts with sk-: {val.startswith(\"sk-\")}')
"
```
