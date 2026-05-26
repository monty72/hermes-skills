# Tesla OAuth PKCE Flow — Technical Notes

## The redirect_uri Problem

The Tesla `ownerapi` OAuth client (`client_id=ownerapi`) has its redirect URI registered as:

```
tesla://auth/callback
```

This is a **custom URL scheme** that only the native Tesla app can handle. **No HTTPS redirect URI is registered** for the `ownerapi` client. This means:

- ❌ Opening the auth URL in a regular browser and waiting for a redirect back to `https://...` will fail with:
  ```
  The 'redirect_uri' supplied is not registered for this 'client_id'
  ```
- ✅ Opening the auth URL will try to open the Tesla app (which registers the `tesla://` scheme)
- ⚠️ The auth code IS in the URL before the redirect — it can be captured if you look at the address bar before the Tesla app intercepts

## Workflows That Work

### 1. pywebview native window (Linux/Mac)
`pypowerwall setup` opens a native WebView that intercepts the `tesla://` redirect before the OS handles it. This is the intended flow.

**Need:** `python3-gi` + `gir1.2-webkit2-4.0` on Linux, or just `pip install pywebview` on macOS.

### 2. Two-machine flow
- Machine A (with display): `pypowerwall authtoken` → pops WebView, user logs in, prints refresh_token
- Machine B (headless): `pypowerwall setup -headless` → prompts to paste refresh_token

### 3. Manual PKCE + code capture
- User opens auth URL on phone
- Tesla app intercepts the `tesla://` redirect
- User reads the code from the URL before the app takes over
  - iPhone: the URL briefly appears at the top of the screen
  - Android: the "Open with" dialog shows the URL
- Paste the code back into the exchange script

PKCE state must match — each auth URL is one-time use. If the exchange fails, generate a fresh URL.

## Token Exchange Endpoint

```
POST https://auth.tesla.com/oauth2/v3/token
{
  "grant_type": "authorization_code",
  "client_id": "ownerapi",
  "code": "<one-time-code>",
  "code_verifier": "<SHA256-of-random-32-bytes-urlsafe-no-padding>",
  "redirect_uri": "tesla://auth/callback"
}
```

Returns `{ "access_token": "...", "refresh_token": "...", "expires_in": 28800 }`.

Refresh is:
```
POST https://auth.tesla.com/oauth2/v3/token
{
  "grant_type": "refresh_token",
  "client_id": "ownerapi",
  "refresh_token": "..."
}
```

## pyPowerwall Auth File Structure

`~/.pypowerwall/.pypowerwall.auth`:
```json
{
  "refresh_token": "...",
  "email": "user@example.com",
  "region": "us"
}
```

`~/.pypowerwall/.pypowerwall.site`:
```json
{
  "email": "user@example.com",
  "sites": []
}
```

After authenticating, running `pypowerwall get -cloud` auto-discovers sites and fills in the sites array.
