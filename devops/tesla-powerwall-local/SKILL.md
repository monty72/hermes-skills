---
name: tesla-powerwall-local
description: Monitor and manage Tesla Powerwall and solar — local gateway API, pyPowerwall (cloud/TEDAPI/v1r LAN), and OAuth setup. Supports PW2, PW+, and PW3.
tags: [tesla, powerwall, energy, solar, pypowerwall, powerwall-3, monitoring]
---

# Tesla Powerwall Monitoring

Monitor and control Tesla Powerwall 2/+/3 and solar systems. Covers the local Gateway API, pyPowerwall library (cloud Owners API, Fleet API, TEDAPI Wi-Fi, v1r LAN), and direct curl-based polling.

## Connection Modes Summary

| Mode | Credentials Needed | Works on | Data Available |
|------|-------------------|----------|----------------|
| **Cloud (Owners API)** | Tesla account login | PW2/+/3, solar-only | Full data via cloud |
| **Fleet API** | Tesla developer app + PEM key | PW2/+/3, solar-only | Full data, official |
| **Local Gateway API** | Customer password (set via web UI) | PW2, PW+ only | Power, battery, grid |
| **TEDAPI Wi-Fi** | Gateway WiFi password (QR sticker) | PW2/+/3 | Full + vitals + strings |
| **v1r LAN** | RSA key + wired LAN + gateway password | PW3 only | Full + control |

**Critical PW3 fact:** Powerwall 3 does NOT have a local web portal or customer password portal on firmware 26.x+. The root URL returns 404. `/api/login/Basic` exists but was never configured with a password from a web UI — all password attempts return 401. **Cloud mode is the path of least resistance for PW3.**

## Quick Start — Cloud Mode (Easiest for PW3)

See `references/pypowerwall-installation-debian.md` for Debian 13+ install workarounds.

```bash
# Install
pipx install pypowerwall
# OR if pipx unavailable: python3 -m venv ~/pw-venv && ~/pw-venv/bin/pip install pypowerwall

# Setup — opens browser for Tesla login
pypowerwall setup -email your@email.com

# Test
pypowerwall get -cloud
```

### Headless/Remote Server Setup

If the machine has no display, use the two-machine flow:

**On a machine with a display:**
```bash
pipx install pypowerwall
pypowerwall authtoken   # opens Tesla login popup, prints refresh_token
```

**On the headless machine:**
```bash
pypowerwall setup -headless -email your@email.com
# Paste the refresh token when prompted
```

## OAuth PKCE Flow (Manual)

When the above doesn't work (e.g. GUI deps missing, no display at all), use the manual PKCE flow:

```python
import base64, hashlib, secrets, urllib.parse, requests

cv = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
cc = base64.urlsafe_b64encode(hashlib.sha256(cv.encode()).digest()).rstrip(b"=").decode()
st = secrets.token_urlsafe(16)

url = ("https://auth.tesla.com/oauth2/v3/authorize?" + urllib.parse.urlencode({
    "client_id": "ownerapi",
    "code_challenge": cc,
    "code_challenge_method": "S256",
    "redirect_uri": "tesla://auth/callback",
    "response_type": "code",
    "scope": "openid email offline_access",
    "state": st,
}))
print(f"Open this URL: {url}")
```

User opens URL, logs in, Tesla app tries to handle the `tesla://` redirect. The auth code is in the URL before the redirect. User pastes the code, then:

```python
resp = requests.post("https://auth.tesla.com/oauth2/v3/token", json={
    "grant_type": "authorization_code",
    "client_id": "ownerapi",
    "code": auth_code,
    "code_verifier": cv,
    "redirect_uri": "tesla://auth/callback",
}).json()
print(resp["refresh_token"])
```

Save to `~/.pypowerwall/.pypowerwall.auth`:
```json
{"refresh_token": "...", "email": "user@example.com", "region": "us"}
```

## Direct Tesla Owners API (No pyPowerwall)

Once you have an access_token, bypass pyPowerwall entirely:

```python
import requests
headers = {"Authorization": f"Bearer {access_token}"}

# List products (find energy_site_id)
resp = requests.get("https://owner-api.teslamotors.com/api/1/products", headers=headers)
site_id = resp.json()["response"][0]["energy_site_id"]

# Live status
live = requests.get(f"https://owner-api.teslamotors.com/api/1/energy_sites/{site_id}/live_status", headers=headers)
data = live.json()["response"]

# Token refresh
resp = requests.post("https://auth.tesla.com/oauth2/v3/token", json={
    "grant_type": "refresh_token", "client_id": "ownerapi",
    "refresh_token": refresh_token,
}).json()
```

## pyPowerwall vs Teslapy Cache Mismatch

⚠️ pyPowerwall `cloudmode=True` reads `~/.pypowerwall/.pypowerwall.auth`, but the bundled `teslapy` library saves to `cache.json` with a different format. If `authtoken` ran on Windows/Mac, the auth file may not exist. Extract `refresh_token` from `cache.json`'s `sso.refresh_token` and create `.pypowerwall.auth` manually on the target machine.

## pyPowerwall Usage

### Basic Queries

```python
import pypowerwall
pw = pypowerwall.Powerwall("", "", "user@example.com", "Europe/London", cloudmode=True)
print(pw.power())      # {site, solar, battery, load} in watts
print(pw.level())      # Battery %
print(pw.grid_status())  # "UP" / "DOWN"
print(pw.site_name())  # Site name
print(pw.version())    # Firmware
```

### CLI Queries

```bash
pypowerwall get -cloud                    # Cloud mode
pypowerwall get -local -host IP -pass PW  # Local Gateway (PW2)
pypowerwall get -tedapi -gw_pwd PASSWORD  # TEDAPI Wi-Fi
pypowerwall get -v1r -host 10.42.1.x -gw_pwd PASSWORD  # v1r LAN (PW3)
```

## PW3 Local API (curl)

Even without the customer-password web portal, the PW3 Gateway API endpoints exist:

```bash
# Authentication
curl -sk -X POST "https://192.168.1.108/api/login/Basic" \
  -H "Authorization: Basic $(echo -n 'Customer:PASSWORD' | base64)"

# After auth (cookie-based):
curl -sk -c cookies.txt "https://192.168.1.108/api/meters/aggregates"
curl -sk -b cookies.txt "https://192.168.1.108/api/system_status/soe"
curl -sk -b cookies.txt "https://192.168.1.108/api/system_status/grid_status"
```

If you know the password, this works for PW3 on firmware 26.x. If not, use Cloud mode.

## NetZero — Alternative Config Control for PW3

NetZero (netzero.energy) provides a REST API for Powerwall configuration control that works via Tesla cloud — no local gateway password needed. Useful when cloud-mode pyPowerwall provides monitoring but you need to programmatically change config (backup reserve, operational mode, exports, grid charging).

```bash
export TOKEN=$(hermes-vault get NETZERO_API_TOKEN)
# Read config
curl -H "Authorization: Bearer $TOKEN" \
  https://api.netzero.energy/api/v1/{site_id}/config
# Update config
curl -H "Authorization: Bearer $TOKEN" \
  --json '{"backup_reserve_percent": 50}' \
  https://api.netzero.energy/api/v1/{site_id}/config
```

See `netzero-powerwall-api` skill for full documentation and pitfalls.

## Known Pitfalls

- **PW3 has no web UI** — `https://<gateway>/` returns 404 on firmware 26.x. This is NORMAL. The API is still there.
- **Self-signed cert blocks browsers** — `browser_navigate` in Hermes fails with `ERR_CERT_AUTHORITY_INVALID`. Use `curl -sk` instead.
- **PW3 auth was never set up** — if you bought through an installer, no customer password may exist. `/api/login/Basic` exists but returns 401 for everything.
- **Rate limiting** — 6+ rapid login attempts trigger 429 status. Wait 60s before retrying.
- **`ownerapi` + `https://` redirect doesn't work** — the Tesla `ownerapi` OAuth client only accepts `tesla://auth/callback` as redirect URI. Can't complete OAuth in a plain browser — needs the native Tesla app or the pywebview GUI.
- **Debian 13+ blocks system pip** — use `pipx` or a venv instead.
- **GUI deps missing on Linux** — `sudo apt install python3-gi gir1.2-webkit2-4.0` for the pywebview popup.
- **User confusion: auth URL vs callback URL** — users often paste back the same auth URL they opened, not the callback URL they landed on after login. When asking for the redirect URL, say "Copy the address bar URL AFTER you log in — it starts with tesla://auth/callback?code=..."
- **User pastes auth URL 5+ times without logging in** — a common pattern: the user copies the auth URL from the agent's message and pastes it right back, thinking it's the output they need to return. PIVOT AFTER 2 ATTEMPTS. Do NOT keep asking — switch to the two-machine `authtoken` flow or manual token injection (via `cache.json` extraction). Repeating wastes many turns.
- **`authtoken` can succeed silently** — `pypowerwall authtoken` may print "Login cancelled or timed out" due to a GUI/webview error, but STILL save valid tokens to `~/.pypowerwall/cache.json` if the browser login completed before the webview failed. Always check `cache.json` for `sso.refresh_token` before declaring auth dead. If tokens were saved, extract and manually create `.pypowerwall.auth`.
- **Tesla OAuth on mobile is unreliable** — the Tesla app intercepts the `tesla://auth/callback` redirect before the user can read the code from the address bar. iPhone's "Open Links in Apps" toggle (Settings → Safari → turn OFF) helps but is not reliable. The two-machine flow (`authtoken` on a desktop) is far more dependable. Prefer recommending the desktop GUI approach first, falling back to manual PKCE code extraction only as a last resort — and even then, expect failure.
- **Debian "externally managed" Python** — `pip install` fails with PEP 668 error. Always use `pipx install pypowerwall` or `python3 -m venv ~/pw-venv && venv/bin/pip install pypowerwall`. The `--break-system-packages` flag works but is a blunt instrument.
- **PW3 reset button needs a long press** — recommend a 10-second hold for the Gateway 3 pinhole reset button. Shorter presses may not trigger the password wipe. After reset, wait 2 minutes for the gateway to reboot, then visit `https://192.168.1.108` in a browser to set the new password. If no browser login screen appears, the reset may not have taken.
- **Access tokens aren't the same as auth codes** — users may paste a JWT (starts with `eyJ`) thinking it's the auth code. The auth code is a short random string, not a JWT. The refresh token is also a JWT starting with `eyJ` — distinguish carefully.
