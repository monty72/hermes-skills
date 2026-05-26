# pyPowerwall Cloud Setup — Full Session Transcript (May 2026)

## Context

PW3, UK (G99), 27 kWh / 2 units, firmware **26.10.3**, commissioned Jan 2026.
Gateway at 192.168.1.108.
No customer password was ever configured — all attempts returned 401.

## Steps Taken

### 1. Direct API (failed for PW3)
```
POST /api/login/Basic
Authorization: Basic Q3VzdG9tZXI6UFdEX0FUVElQVA==
```
- JSON body `{"username":"customer","password":"..."}` → also 401
- All default passwords (password, admin, tesla, CNTUN, RXWBPCNTUN) → 401
- Rate limit at 429 after ~6 rapid attempts

### 2. Root URL check
`curl -sk https://192.168.1.108/` → 404
`curl -sk https://192.168.1.108/api/login/Basic -X POST` → 405 (correct: expects POST)

### 3. Browser attempt
`browser_navigate` to PW3 IP → `ERR_CERT_AUTHORITY_INVALID`
PW3 uses self-signed certs; headless Chromium can't bypass this.

### 4. Physical reset
- Reset button: pinhole on back panel of PW3
- 10s hold recommended
- User reported reset done but couldn't complete browser flow
- Possible: reset needs power cycle, or gateway password was never set via web UI

### 5. pyPowerwall installation (Debian 13)
```
pip install pypowerwall
→ error: externally-managed-environment
Fix: pipx install pypowerwall
```

### 6. pyPowerwall GUI setup (failed)
```
pypowerwall setup
→ ModuleNotFoundError: No module named 'gi'
→ Missing python3-gi gir1.2-webkit2-4.0
```

### 7. Headless mode
```
pypowerwall setup -headless -email user@me.com
→ Prompts for refresh token (need to get one from a machine with display)
```

### 8. Manual PKCE OAuth flow (tried, not completed)
- Generated auth URL with PKCE challenge
- User opened URL but couldn't capture the `code` parameter from `tesla://auth/callback` redirect
- **Key insight:** `ownerapi` client only accepts `tesla://auth/callback` as redirect URI — can't complete in a regular browser
- Need either (a) the Tesla app to intercept, or (b) pywebview GUI on Linux

## What Works

- `pipx install pypowerwall` installs cleanly on Debian 13
- `pypowerwall get -cloud` is the right command once auth is set up
- Auth file lives at `~/.pypowerwall/.pypowerwall.auth` as JSON
- The `teslapy` library bundled with pypowerwall handles OAuth and token refresh

## What Doesn't Work on PW3 Firmware 26.x

- ❌ No web UI at `https://<gateway>/`
- ❌ `/api/login/Basic` has no configured password (401 always)
- ❌ Headless Chromium can't accept PW3 self-signed cert
- ❌ `ownerapi` + `https://` redirect URL not registered — must use `tesla://`
