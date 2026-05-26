# Real-World Example: Tesla OAuth PKCE (May 2026)

## Context
PW3 owner needed to set up pyPowerwall Cloud mode from a headless Debian server. The standard `pypowerwall authtoken` command failed because Linux had no display (Missing system libraries: `python3-gi`, `gir1.2-webkit2-4.0`).

## What Worked (Eventually)
The intended solution — `pypowerwall authtoken` on a Mac/PC with a browser — was not yet completed. The `setup -headless` flow also needs a refresh token pasted in.

## What Was Discovered

### Direct API to PW3 (failed)
```
POST https://192.168.1.108/api/login/Basic
Authorization: Basic <base64("Customer:password")>
```
- All known/default passwords returned 401
- JSON body method (`{"username":"customer","password":"..."}`) also 401 on PW3
- Root URL `https://192.168.1.108/` returns 404 (no web UI) on PW3 firmware 26.10.3
- After 6+ rapid attempts, rate-limited at 429
- **Lesson:** PW3 has the `/api/login/Basic` endpoint but no web portal to set the password — it was never configured. Cloud mode is the only practical path if no password was set.

### Manual PKCE URL Generation
The general PKCE pattern was successful at generating the auth URL. Key findings:
- Tesla uses `client_id=ownerapi`, `redirect_uri=tesla://auth/callback`
- The custom scheme `tesla://` triggers the Tesla app on phones — browser wants to hand off before the user can copy the code from the address bar
- Workaround: Set `redirect_uri` to something the browser CAN load (e.g., `https://auth.tesla.com/void/callback`) — still shows the code in the address bar
- Always save `code_verifier` + `state` to `/tmp/` before printing the URL, in case the user doesn't come back immediately

### pyPowerwall Headless Setup Caveats
- `pip install pypowerwall` blocked by `error: externally-managed-environment` on Debian 13
- Fix: `pipx install pypowerwall` or `python3 -m venv ~/pw-venv && source ~/pw-venv/bin/activate && pip install pypowerwall`
- `pypowerwall setup` opens native WebView via pywebview: needs `python3-gi` + `gir1.2-webkit2-4.0` system packages
- `pypowerwall setup -headless` correctly detects SSH/remote session and prompts for a paste
