# Token Health Audit — Quick Reference

Batch-check every vault-registered token against its API. Run this:

- After migrating tokens to the vault
- After key rotation
- When the user reports an API error
- Before and after stripping secrets from config files

## One-Shot Check Script

```bash
#!/bin/bash
export PATH="$HOME/.local/bin:$PATH"
source ~/.hermes/.env.local 2>/dev/null

check() {
  local name="$1" status="$2"
  if [ "$status" = "200" ] || [ "$status" = "OK" ]; then
    echo "  ✅ $name — $2"
  else
    echo "  ❌ $name — $2"
  fi
}

DS=$(hermes-vault get DEEPSEEK_API_KEY)
check "DeepSeek" "$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 \
  "https://api.deepseek.com/user/balance" -H "Authorization: Bearer $DS")"

TG=$(hermes-vault get TELEGRAM_BOT_TOKEN)
check "Telegram" "$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 \
  "https://api.telegram.org/bot$TG/getMe")"

HA=$(hermes-vault get HASS_TOKEN)
check "HA" "$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 \
  -H "Authorization: Bearer $HA" "http://192.168.1.146:8123/api/")"

PX=$(hermes-vault get PROXMOX_API_TOKEN)
PU=$(hermes-vault get PROXMOX_URL)
check "Proxmox" "$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 -k \
  -H "Authorization: $PX" "$PU/version")"

GH=$(hermes-vault get GITHUB_TOKEN)
check "GitHub" "$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 \
  -H "Authorization: token $GH" "https://api.github.com/repos/monty72/montygroup-astro")"

BV=$(hermes-vault get BRAVE_SEARCH_API_KEY)
check "Brave Search" "$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 \
  "https://api.search.brave.com/res/v1/web/search?q=test&count=1" \
  -H "X-Subscription-Token: $BV" -H "Accept: application/json")"

VC=$(hermes-vault get VERCEL_TOKEN)
check "Vercel" "$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 \
  -H "Authorization: Bearer $VC" "https://api.vercel.com/v1/user")"
```

## API Endpoints by Token

| Token Key | API Endpoint | Auth Header |
|-----------|-------------|-------------|
| DEEPSEEK_API_KEY | `api.deepseek.com/user/balance` | `Bearer <key>` |
| TELEGRAM_BOT_TOKEN | `api.telegram.org/bot<token>/getMe` | Embedded in URL |
| HASS_TOKEN | `http://192.168.1.146:8123/api/` | `Bearer <token>` |
| PROXMOX_API_TOKEN | `<PX-URL>/version` | `<full-token>` (includes prefix) |
| GITHUB_TOKEN | `api.github.com/repos/<user>/<repo>` | `token <pat>` |
| BRAVE_SEARCH_API_KEY | `api.search.brave.com/res/v1/web/search` | `X-Subscription-Token <key>` |
| VERCEL_TOKEN | `api.vercel.com/v1/user` | `Bearer <token>` |
