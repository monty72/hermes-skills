---
name: rest-graphql-debug
description: "Debug REST/GraphQL APIs: status codes, auth, schemas, repro."
version: 1.0.0
---

# REST / GraphQL API Debugging

## Overview

Systematically debug REST and GraphQL APIs — status codes, authentication, schemas, and reproduction scripts.

## REST Debugging

### Step 1: Isolate the request

```bash
# Test with curl
curl -sv https://api.example.com/endpoint 2>&1

# With method + body
curl -sv -X POST https://api.example.com/endpoint \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"key":"value"}' 2>&1
```

### Step 2: Check status codes

| Code | Meaning | What to check |
|------|---------|---------------|
| 200 | OK | Parse response |
| 201 | Created | Check Location header |
| 204 | No Content | Expected for deletes |
| 301/302 | Redirect | Follow with -L |
| 400 | Bad Request | Check request body format |
| 401 | Unauthorized | Check auth header/token |
| 403 | Forbidden | Check permissions |
| 404 | Not Found | Check URL path |
| 429 | Rate Limited | Check Retry-After header |
| 500 | Server Error | Check server logs |

### Step 3: Verify auth

```bash
# Check if token is valid
curl -sv https://api.example.com/me -H "Authorization: Bearer $TOKEN" | jq .

# Test without auth (expect 401)
curl -sv https://api.example.com/endpoint 2>&1 | grep -E "< HTTP|< 401"
```

### Step 4: Format response

```bash
curl -s https://api.example.com/endpoint | python3 -m json.tool
curl -s https://api.example.com/endpoint | jq '.'
```

### Step 5: Repro script

```python
import requests

url = "https://api.example.com/endpoint"
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}
data = {"key": "value"}

resp = requests.post(url, headers=headers, json=data)
print(f"Status: {resp.status_code}")
print(f"Headers: {dict(resp.headers)}")
print(f"Body: {resp.text[:2000]}")
```

## GraphQL Debugging

### Step 1: Test query

```bash
curl -sv -X POST https://api.example.com/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"query { viewer { name } }"}' | jq .
```

### Step 2: Introspect schema

```bash
# Get full schema
curl -s https://api.example.com/graphql \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"{ __schema { types { name kind fields { name } } } }"}' | jq .
```

### Step 3: Check errors

```json
{
  "errors": [
    {
      "message": "...",
      "locations": [{"line": 2, "column": 3}],
      "path": ["viewer", "name"]
    }
  ]
}
```

- Syntax errors → check query format
- Validation errors → field doesn't exist on type
- Execution errors → resolver threw
- Nullable vs non-nullable → check schema

### Step 4: Variables

```bash
curl -s -X POST https://api.example.com/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"query($id: ID!) { node(id: $id) { id name } }","variables":{"id":"123"}}'
```

## OAuth 2.0 PKCE From a Headless/CLI Environment

Many APIs (Tesla, GitHub, Google, Stripe) use the **Authorization Code + PKCE** flow. When you're on a headless server (no display), the native WebView popup won't open. Here's the general pattern to extract tokens manually.

### The Flow

```
1. Generate PKCE params (code_verifier, code_challenge, state) on the server
2. Build the auth URL with code_challenge + redirect URI
3. User opens URL in their browser (phone/laptop), logs in
4. Browser redirects to the callback URL with ?code=... in the address bar
5. User copies that URL (or just the code param) back to you
6. Exchange the code + code_verifier at the token endpoint for a refresh token
```

### Manual PKCE Token Extraction (Generic Python)

```python
import base64, hashlib, secrets, urllib.parse, requests

# Step 1: Generate PKCE params
CLIENT_ID = "ownerapi"  # or whatever the API uses
REDIRECT_URI = "https://auth.example.com/void/callback"  # MUST match app registration
SCOPES = "openid email offline_access"

code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).rstrip(b"=").decode()
state = secrets.token_urlsafe(16)

# Step 2: Build auth URL
auth_url = ("https://auth.provider.com/oauth2/v3/authorize?" +
    urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "state": state,
    }))
print(f"Open in browser:\n{auth_url}")

# Step 3: (User logs in, copies the resulting URL with ?code=...)
# Step 4: Paste the code from the redirect URL
auth_code = input("Paste the ?code= value from the redirect URL: ").strip()

# Step 5: Exchange for tokens
token_resp = requests.post("https://auth.provider.com/oauth2/v3/token", json={
    "grant_type": "authorization_code",
    "client_id": CLIENT_ID,
    "code": auth_code,
    "code_verifier": code_verifier,
    "redirect_uri": REDIRECT_URI,
}, timeout=30)

if token_resp.status_code == 200:
    token_data = token_resp.json()
    print(f"Refresh token: {token_data.get('refresh_token')}")
    print(f"Access token: {token_data.get('access_token')}")
else:
    print(f"Exchange failed: {token_resp.status_code} {token_resp.text}")
```

### Pitfalls

- **`redirect_uri` mismatch** — the URI in your auth URL must EXACTLY match what's registered with the provider. Even trailing slashes matter.
- **PKCE verifier lost** — if the user opens the URL but doesn't come back before the script exits, the `code_verifier` is lost and the `code` is unusable. **Save verifier+state to a file** before printing the URL.
- **Custom scheme redirects** (e.g., `tesla://auth/callback`, `csproject://auth`) — the browser can't open these and may redirect to an app. The code is still in the address bar before the redirect. Tap the URL bar before the app opens and copy it.
- **Rate limits** — most OAuth providers limit token exchanges per IP/client. If you get 429, wait and retry.
- **Localhost callback** — using `http://localhost:PORT/callback` works if the auth provider allows it AND the user's browser can reach localhost. Useful for fully automated flows where the user is on the same machine. Start a `http.server` to catch the redirect.

### Tesla-Specific Example (Real World)

For Tesla Energy (pyPowerwall / Powerwall / Fleet API), the Tesla authentication uses:

```
client_id = "ownerapi"
redirect_uri = "tesla://auth/callback"
scopes = "openid email offline_access"
auth_host = "https://auth.tesla.com"
```

The native pyPowerwall commands are:
- `python -m pypowerwall authtoken` — opens a GUI window (macOS PyObjC / Linux pywebview)
- `python -m pypowerwall setup -headless -email user@example.com` — prompts for a paste
- On Linux without a display: GUI fails with `Missing system libraries: python3-gi, gir1.2-webkit2-4.0`
- Workaround: run `authtoken` on a Mac/PC with a browser, paste the refresh token

See the `tesla-powerwall-local` skill for the full Powerwall + pyPowerwall setup.

## Common Issues

- **CORS**: Check `Access-Control-Allow-Origin` header
- **Rate limiting**: Add exponential backoff
- **Pagination**: Check `Link` header or `hasNextPage`
- **Timeouts**: Check if request completes within expected window
- **SSL**: Add `-k` for testing, fix cert for production
