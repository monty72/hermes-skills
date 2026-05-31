---
name: web-app-security-hardening
description: "Audit and harden public-facing web applications — check for exposed internal infrastructure, fix CORS wildcards, add HTTP security headers, secure API endpoints, check repos for secrets, and mitigate BREACH attacks."
version: 1.0.0
author: Hermes Agent
tags: [security, audit, webapp, hardening, csp, cors, headers]
---

# Web Application Security Hardening

Systematic audit and hardening of public-facing web applications. Covers the full cycle: discovery of exposures → fix → deploy → verify.

## When to Use

- User reports a security audit was done but has remaining items
- User asks "check our web app for security issues" or "harden the security"
- During a deployment review, before launching a new public-facing site
- When onboarding a new web application into the infrastructure

## Workflow

### Phase 1: Reconnaissance — What's publicly exposed?

Check what the public internet can see about the application:

**1. Live HTTP response headers**
```bash
curl -sI 'https://targetdomain.com' 2>&1
```
Check for: `Server`, `X-Powered-By`, `access-control-allow-origin`, missing security headers (CSP, XFO, XCTO, HSTS, Permissions-Policy, Referrer-Policy).

**2. Page source review**
Browse the live page (or extract via `web_extract` / browser). Look for:
- Internal IP addresses (192.168.x.x, 10.x.x.x, 172.16-31.x.x)
- Internal hostnames (proxmox.lan, hass.local, etc.)
- Internal API endpoints (`/api/status`, `/api/health`, `/api/internal/...`)
- Comments containing developer credentials, internal links, or debug info
- Client-side JavaScript polling internal services (`fetch('http://192.168.1.x:...')`)
- Quick links to Proxmox, Home Assistant, routers, or other infrastructure

**3. DNS & subdomain scan**
```bash
curl -s "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); [print(f'{r[\"type\"]:5} {r[\"name\"]:40} -> {r[\"content\"]}') for r in d.get('result',[])]"
```
Identify any subdomains that point to internal IPs or expose internal services.

**4. GitHub repo review** (if repo is public)
```bash
curl -s "https://api.github.com/repos/$ORG/$REPO" \
  -H "Authorization: Bearer $GIT_TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Private: {d.get(\"private\")}')"
```
- If public, check `.gitignore` excludes `.env`, secrets, config files
- Check commit history for leaked tokens (`VERCEL_TOKEN`, `API_KEY`, etc.)
- Recommend making private if it contains internal architecture docs

**5. Checklist report**
```
🔴 CRITICAL: [internal IPs exposed, no auth on API, etc.]
🟡 MEDIUM: [missing headers, CORS wildcard, etc.]
🟢 INFO: [recommendations, non-critical observations]
```

### Phase 2: Fix Exposures

**1. Internal IPs / Infrastructure References**
- Remove all hardcoded IPs, internal URLs, and infrastructure links from page source
- Replace specific hostnames with generic labels ("Proxmox" → "Hypervisor")
- Remove client-side health check polling to internal endpoints
- Remove quick links to Proxmox UI, Home Assistant, GitHub, Vercel dashboard
- Keep only server-rendered, decontextualised system stats (OS, CPU, RAM, uptime) — no IPs

**2. CORS Policy**
- **NEVER** use `Access-Control-Allow-Origin: *` on production APIs with auth
- Restrict to specific origins from an allowlist:
  ```
  ALLOWED_ORIGINS = [
      "http://localhost:3000",
      "https://production-domain.com",
      "https://api.production-domain.com",
  ]
  ```
- Add proper CORS preflight support (`OPTIONS` handler) with `Access-Control-Allow-Methods`, `Access-Control-Allow-Headers`, `Access-Control-Max-Age`
- Fall back to the primary domain (not `*`) for unknown origins
- For Python stdlib HTTP server, implement `_get_origin(headers)` function and use it in all response paths

**3. HTTP Security Headers**
Add these to every response (via server code, config, or edge/firewall rules):

| Header | Example Value | Purpose |
|--------|---------------|---------|
| `Content-Security-Policy` | `default-src 'self'; script-src 'self' 'unsafe-inline'; ...` | XSS, data injection, BREACH |
| `X-Content-Type-Options` | `nosniff` | MIME type sniffing |
| `X-Frame-Options` | `DENY` | Clickjacking |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Referrer leakage |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=(), interest-cohort=()` | Feature restrictions |
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains; preload` | HTTPS enforcement |

**CSP Construction Guidelines:**
- Start with `default-src 'self'` and add explicit overrides per directive type
- `script-src` may need `'unsafe-inline'` and `'unsafe-eval'` for Astro/Vite/Next.js apps
- `style-src` may need `https://fonts.googleapis.com` for Google Fonts
- `font-src` may need `https://fonts.gstatic.com` to load the font files
- `img-src` should include `data:` for inline images
- `connect-src` restricts fetch/XHR/WebSocket destinations — include the site's own domain
- `frame-ancestors 'none'` prevents the page from being iframed
- `base-uri 'self'` restricts `<base>` tag injection
- `form-action 'self'` restricts form submission targets

**4. API Endpoint Authentication**
- All API endpoints should require authentication, including `/api/health` and `/api/status`
- Use Basic Auth (for simple setups), API keys, or JWT depending on context
- For Python stdlib HTTP server, implement a shared `_check_auth(headers)` method:
  ```python
  AUTH_USER = os.environ.get("MC_USER", "admin")
  AUTH_PASS = os.environ.get("MC_PASS", "default-change-me!")
  
  def _check_auth(headers):
      auth = headers.get("Authorization", "")
      if not auth.startswith("Basic "):
          return False
      decoded = base64.b64decode(auth[6:]).decode()
      user, pwd = decoded.split(":", 1)
      return user == AUTH_USER and pwd == AUTH_PASS
  ```
- Apply to EVERY route handler (GET, POST, OPTIONS) that exposes data
- Health endpoints should return minimal info: `{"status": "ok", "service": "name", "timestamp": "..."}`

**5. BREACH Attack Mitigation**
- **What it is:** BREACH exploits HTTP compression (gzip/deflate) combined with reflected content. If the page reflects user input AND contains secrets (CSRF tokens), compression size differences leak secrets byte-by-byte.
- **Assessment:** Is user input reflected on the page? (forms, search bars, error messages containing input). If NO user reflection → BREACH does not apply. If YES → mitigate.
- **Mitigations:**
  - Add a restrictive CSP (primary defense — prevents the JS needed to exploit)
  - Disable HTTP compression on sensitive pages (Vercel: not fully controllable at edge)
  - Add random CSRF tokens/nonces to every response as "secret hiding"
  - Add random byte padding to response bodies (defeats size oracle)

### Phase 3: Deployment & Verification

**1. Vercel/Cloudflare Edge Headers**
For Vercel-deployed apps, add headers to `vercel.json`:
```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" },
        { "key": "Permissions-Policy", "value": "camera=(), microphone=(), geolocation=(), interest-cohort=()" },
        { "key": "Content-Security-Policy", "value": "default-src 'self'; ..." },
        { "key": "Strict-Transport-Security", "value": "max-age=63072000; includeSubDomains; preload" }
      ]
    }
  ]
}
```

**2. GitHub Repo Privacy**
```bash
curl -s -X PATCH "https://api.github.com/repos/$ORG/$REPO" \
  -H "Authorization: Bearer $GIT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"private": true}'
```

**3. Verify**
```bash
# Check live headers
curl -sI 'https://targetdomain.com' | grep -iE 'access-control|x-content|x-frame|content-security|strict-transport|permissions-policy|referrer'

# Verify CORS is restricted
curl -sD - 'https://api.targetdomain.com/endpoint' -H 'Origin: https://evil.com' | grep -i 'access-control-allow-origin'

# Check auth is required
curl -s 'https://api.targetdomain.com/api/health'  # should return 401
curl -s 'https://api.targetdomain.com/api/health' -u 'user:pass'  # should return 200
```

**4. Git tag pre-fix state**
Before deploying fixes, tag the current state for rollback:
```bash
git tag pre-security-fix-$(date +%Y%m%d-%H%M%S)
git push origin --tags
```

## Pitfalls

- **CSP breaks functionality**: The initial CSP should be permissive enough to not break the site. Use `'unsafe-inline'` and `'unsafe-eval'` for Astro/Next.js, then tighten later. Test thoroughly before deploying.
- **HSTS preload is permanent**: Once submitted to the HSTS preload list, you cannot remove your domain for the duration of `max-age`. Start with `max-age=31536000` (1 year), not the full `63072000` (2 years), until you're confident.
- **`git tag pre-security-fix` only saves if you push**: Tags are local by default. Remember `git push origin --tags` or they're useless for rollback.
- **CORS fallback to primary domain**: When restricting origins, the fallback for unknown origins should be the primary domain (not `*`). The response still carries CORS headers, just locked to the safe origin — the browser enforces the restriction.
- **BREACH is site-specific**: On static sites with zero user reflection, BREACH is not exploitable. Don't recommend compression disablement on static sites — it adds latency with no security benefit.
- **API tunnels pointing to dead ports**: If an API is exposed via Cloudflare Tunnel, verify the backend port is actually listening (`ss -tlnp | grep <PORT>`). A tunnel to a dead port produces HTTP 530 errors.
- **Repo privacy breaks existing clones**: After making a repo private, existing clones on other machines will fail to `git pull` until the user re-authenticates (new SSH key or token). Update all affected machines.
