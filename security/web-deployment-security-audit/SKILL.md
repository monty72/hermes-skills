---
name: web-deployment-security-audit
description: Audit web deployments for common security exposures — IP leaks, missing headers, CORS misconfig, BREACH vectors, and repo secrets — before/after deploy.
category: security
version: 1.0.0
author: Agent
tags: [security, audit, web, hardening, deployment]
---

# Web Deployment Security Audit

Run a systematic security audit on any web deployment (Astro, Next.js, static site, API backend). Designed as a pre/post-deployment checklist.

## Audit Dimensions

### 1. IP & Infrastructure Exposure

Check what the public site reveals about your internal network.

```bash
# View the live page source for IPs, hostnames, internal URLs
curl -s https://example.com | grep -oE '(192\.168\.[0-9]+\.[0-9]+|10\.[0-9]+\.[0-9]+\.[0-9]+|172\.(1[6-9]|2[0-9]|3[0-1])\.[0-9]+\.[0-9]+)' | sort -u

# Check for leaked repo URLs, internal dashboard links, API endpoints
curl -s https://example.com | grep -oiE '(github\.com|gitlab|localhost|:3000|:8081|:8000|:8123|proxmox|hass|homeassistant|powerwall|grafana|prometheus)'

# Check client-side JS for API calls to internal services
curl -s https://example.com | grep -oE 'src="[^"]*\.js"' | while read -r match; do
    url=$(echo "$match" | sed 's/src="//;s/"//')
    curl -s "https://example.com$url" 2>/dev/null | grep -oiE '(192\.168\.|10\.|localhost|api/health|api/status|internal)'
done
```

**Red flags:** Any RFC 1918 IP, internal hostname, or `localhost` reference in public HTML/JS.

**Fixes:**
- Remove hardcoded IPs from components and config — use environment variables or server-side rendering
- Remove internal quick-links (Proxmox UI, HASS, dashboards)
- Remove client-side polling of `/api/health`, `/api/status` — serve health data server-rendered only
- Strip internal context from server-rendered system stats (OS version, CPU model, RAM details)

### 2. Security Headers

Verify the live site sends proper security headers.

```bash
curl -sI https://example.com | grep -iE '(content-security-policy|x-frame-options|x-content-type-options|strict-transport-security|permissions-policy|referrer-policy)'
```

**Required headers:**
| Header | Value | Purpose |
|--------|-------|---------|
| `Content-Security-Policy` | `default-src 'self'; ...` | Prevents XSS, data injection |
| `X-Content-Type-Options` | `nosniff` | Prevents MIME sniffing |
| `X-Frame-Options` | `DENY` | Prevents clickjacking |
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains` | Enforces HTTPS |
| `Permissions-Policy` | `camera=(), microphone=(), ...` | Restricts browser features |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Controls referrer leakage |

**Where to set them (in priority order):**
1. **Vercel/edge** — `vercel.json` `headers` array (applies to all routes)
2. **HTML meta tags** — fallback for CSP (less reliable than real headers)
3. **Server middleware** — for SSR apps, set headers in response middleware

**CSP example for Astro/Next.js static sites:**
```
default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'
```

**Verification:**
```bash
curl -sI https://example.com | grep -i 'content-security-policy'
# CSP violations: Open browser DevTools Console on the live site
```

### 3. CORS Configuration

Check for overly permissive CORS on API endpoints.

```bash
# Test with a malicious origin
curl -s -D - -H 'Origin: https://evil.com' https://api.example.com/endpoint | grep -i 'access-control-allow-origin'
```

**Red flags:**
- `Access-Control-Allow-Origin: *` — allows any site to read the response
- Reflecting the `Origin` header value verbatim without validation

**Safe defaults:**
- For public APIs: whitelist specific origins (`https://yourdomain.com`, `http://localhost:3000`)
- For internal APIs: require authentication and restrict origins
- For same-origin proxied APIs (Next.js `/api/*` → backend): CORS not needed on the backend since requests come through the same-origin proxy

**Fixes:**
- Backend: validate `Origin` against an allowlist; fall back to a safe default
- Add `Vary: Origin` header so CDN caches correctly per origin
- Add CORS preflight (`OPTIONS`) handler with restricted `Access-Control-Allow-Methods` and `Access-Control-Allow-Headers`

### 4. BREACH Attack Vector

BREACH exploits HTTP compression combined with reflected content to extract secrets byte-by-byte.

**Risk assessment:**
- **Static sites** (no user input reflected) — risk is negligible
- **Dynamic sites** that reflect query params, form input, or URL paths in the response — risk is real

**Mitigations (apply all three for dynamic sites):**
1. Add a restrictive CSP with `frame-ancestors 'none'`
2. Disable compression on sensitive endpoints via edge config (Page Rules on Cloudflare, `res.setHeader` on Vercel)
3. Add random padding/CSRF tokens to response bodies to break byte-by-byte extraction

**Verification:**
```bash
# Check if compression is enabled
curl -sI -H 'Accept-Encoding: gzip, deflate' https://example.com | grep -i 'content-encoding'
```

### 5. Repository Secrets

Check the GitHub repo for exposed secrets in commit history and file contents.

```bash
# Check repo privacy
curl -s "https://api.github.com/repos/owner/repo" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Private: {d.get(\"private\")}')"

# Check for tracked .env or credential files
curl -s "https://api.github.com/repos/owner/repo/git/trees/main?recursive=1" | python3 -c "
import sys,json; d=json.load(sys.stdin)
for f in d.get('tree',[]):
    p = f['path']
    if any(x in p for x in ['.env', 'credential', 'secret', 'token', '.pem', 'password', 'config.json']):
        print(f'  {f[\"type\"]:4} {p}')
"

# Check recent commits for secret-leak patterns in commit messages
curl -s "https://api.github.com/repos/owner/repo/commits?per_page=10" | python3 -c "
import sys,json; d=json.load(sys.stdin)
for c in d:
    msg = c['commit']['message'][:80]
    if any(x in msg.lower() for x in ['token', 'key', 'secret', 'password', 'credential']):
        print(f'  ⚠️  {c[\"sha\"][:8]} {msg}')
"

# Check .gitignore
curl -s "https://api.github.com/repos/owner/repo/contents/.gitignore" | python3 -c "
import sys,json,base64; d=json.load(sys.stdin); print(base64.b64decode(d.get('content','')).decode())
"
```

**Red flags:**
- Public repo when it should be private (contains architecture docs, personal emails, infra topology)
- `.env` or credential files tracked in git history
- Commit messages mentioning tokens, keys, or passwords
- No `.gitignore` excluding `.env`, `.env.local`, `credentials`

**Fixes:**
- Make the repo private (GitHub → Settings → Danger Zone)
- If a token was committed: rotate it immediately, then purge from git history (`git filter-repo`)
- Add `.env`, `.env.local`, `.env.production`, `credentials`, `*.pem`, `*.key` to `.gitignore`

### 6. Vercel/Edge Configuration

Check `vercel.json` for security settings.

```bash
# Download vercel.json from GitHub
curl -s "https://api.github.com/repos/owner/repo/contents/vercel.json" | python3 -c "
import sys,json,base64; d=json.load(sys.stdin)
print(base64.b64decode(d.get('content','')).decode())
"
```

**Required checks:**
- Are security headers configured in the `headers` array?
- Is `cleanUrls: true` set?
- Are there any rewrites/redirects that could expose internal paths?

## Report Template

```
## Security Audit: <domain>

### 🔴 Critical
[List IP exposures, hardcoded secrets, missing auth on endpoints]

### 🟡 Medium
[List missing headers, CORS wildcard, repo privacy, BREACH risk]

### ✅ Fixed
[List items already fixed this session]

### ❌ Remaining
[List items needing user action]

### Pre-fix tag
git tag pre-security-fix-<date>-<timestamp>
```

## Workflow

1. **Tag pre-fix state**: `git tag pre-security-fix-$(date +%Y%m%d-%H%M%S)` before making changes
2. **Fix dimension 1→5** in priority order (IP exposure → headers → CORS → BREACH → repo)
3. **Verify each fix** with the commands in each section
4. **Push fixes** to main, Vercel auto-deploys
5. **Re-run audit** to confirm everything is fixed
6. **Document remaining items** in the report

## Pitfalls

- **Mission Control dashboards** are the most common source of IP leaks — they aggregate all services in one page, making it easy to accidentally include internal URLs
- **CSP 'unsafe-inline' on script-src** — Astro/Next.js need this for hydration; it's a pragmatic trade-off. Remove only if you audit every inline script
- **BREACH on static sites** is often flagged by security scanners even when not exploitable. Document the risk assessment to avoid repeated flags
- **vercel.json headers don't override HTML meta tags** — both are applied. Meta tags are a useful fallback for non-Vercel deployments
- **CORS wildcard for static assets** (fonts, images) is fine — restrict it for API responses only
- **Vercel auto-compresses** all responses — can't disable at edge. For dynamic endpoints, use Vercel Edge Middleware to add random padding
