---
name: static-site-deployment
description: "Deploy static HTML/CSS sites to public URLs — Surge.sh, localhost.run tunnels, GitHub Pages, or raw file hosts."
version: 1.0.0
author: Hermes Agent
---

# Static Site Deployment

## Overview

Deploy static HTML/CSS/JS sites to public URLs. Covers multiple strategies ordered by reliability and feature set.

## Method Selection

| Method | Auth needed | Permanent URL | Custom domain | Best for |
|--------|------------|---------------|---------------|----------|
| **Vercel + GitHub Actions** | GitHub token + Vercel access token (gen at vercel.com/account/tokens) | ✓ (preview + prod) | ✓ | **RECOMMENDED** for framework-based sites (Astro, Next.js, SvelteKit) — auto-deploys on git push, preview deployments on PRs, edge CDN, fast builds (<30s) |
| **Cloudflare Tunnel (named)** | Cloudflare API token (Tunnel + DNS scopes) | ✓ (on your domain) | ✓ | Local servers behind NAT/CGNAT, permanent HTTPS on your own domain — see `cloudflare-dns-management` skill |
| **Cloudflare DNS + Proxmox LXC** | Cloudflare API token | ✓ | ✓ (with Cloudflare proxy/SSL) | Self-hosted production on your own hardware with HTTPS |
| **Surge.sh** | Email + password | ✓ (subdomain) | ✓ | Production, fast iteration for raw HTML/CSS |
| **localhost.run** | None | ✗ (changes per session) | ✗ | Dev previews, demos |
| **GitHub Pages** | GitHub token | ✓ (org/user pages) | ✓ | Simple static hosting |
| **Python http.server** | None | ✗ (local only) | ✗ | Dev testing |

### When to use each

- **Framework-based sites** (Astro, Next.js, SvelteKit, etc.) → **Vercel + GitHub Actions**. The build tool handles the framework; Vercel auto-deploys every push, handles SSL/custom domains, and builds in <30s.
- **Raw HTML/CSS/JS** (one-off pages, resource hubs) → **Vercel** (create repo, `npx vercel deploy --prod --token $TOKEN --yes`) or **Cloudflare Tunnel** if you own a domain.
- **Internal tools** → **Proxmox LXC** + Cloudflare Tunnel for private access.
- **Quick file transfer** → **localhost.run** (no account needed).

## Prerequisites

```bash
# Surge
npm install -g surge

# localhost.run (no install needed — uses ssh)
# SSH must be available

# GitHub Pages
# Install gh CLI and authenticate
```

## Method 1: Surge.sh (Recommended)

```bash
# First-time login (interactive)
npx surge ./dist my-project.surge.sh

# With token (non-interactive)
SURGE_TOKEN="your-token" surge ./dist my-project.surge.sh

# Custom domain
surge ./dist custom-domain.com

# Teardown
surge teardown my-project.surge.sh

# List deployments
surge list
```

**Pitfalls:**
- First run prompts interactively for email/password — can't auto-answer
- No SURGE_TOKEN by default; generate via `surge token` after login
- The npm package `here-now` does NOT exist. Do not try to install it.

## Method 2: localhost.run (No Auth, Dev Previews)

This method creates a temporary HTTPS tunnel to a local server. Works with zero setup.

```bash
# Step 1: Kill any old tunnels first (avoids port conflicts)
kill $(pgrep -f 'ssh.*localhost.run') 2>/dev/null

# Step 2: Start a local HTTP server
cd ./dist && python3 -m http.server 8080 &

# Step 3: Create tunnel (background)
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 \
  -R 80:localhost:8080 nokey@localhost.run

# The output prints the URL: https://<hash>.lhr.life
```

## Pitfalls:
- **URL changes every session** (random hash) — must re-fetch each time
- **Tunnel is SLOW to connect** — it can take 15-45s to print the URL. Don't panic. Use `process(action='wait', timeout=60)` on the background process. If the URL doesn't appear after 60s, the remote forward likely failed and you should kill + retry.
- **Tunnel connection requires patience on first connect** — localhost.run needs to allocate a hostname, set up TLS termination, and forward the connection. The SSH debug output shows `remote forward success` but the actual URL line (`<hash>.lhr.life tunneled with tls termination`) comes later. Poll the output periodically rather than blocking indefinitely.
- **Always kill old tunnels before starting new ones** — leftover SSH processes for the same port cause race conditions and silent failures. `kill $(pgrep -f 'ssh.*localhost.run')` as step zero. Use `sleep 2` after kill to ensure ports are freed.
- **Kill old HTTP servers too** — `fuser -k PORT/tcp` before starting a fresh server on that port. Stale servers block binding. Also `sleep 1` after fuser.
- **Tunnel URL may return 503 for first 30 seconds** while the TLS termination propagates through localhost.run's infrastructure. After the URL prints, wait 5-10 seconds before sending it to the user. The 503 resolves automatically.
- **Multiple tunnel processes for the same port silently fail** — the first SSH negotiated the port, subsequent ones sit idle and never print a URL. Always kill ALL stale tunnels (`pgrep -f 'ssh.*localhost.run'`) before starting.
- Tunnel drops if SSH disconnects — restart it
- Only one tunnel per port
- Session timeout after inactivity
- **If the tunnel establishes but the URL doesn't appear** (output has "welcome" banner but no `lhr.life` line), the remote forward failed. Kill and retry with `-v` flag to debug.

## Method 3: GitHub Pages

```bash
# Step 1: Create repo with gh CLI
gh auth login
gh repo create my-site --public --push

# Step 2: Set up gh-pages branch or docs folder
git checkout -b gh-pages
cp -r ./dist/* .
git add -A && git commit -m "deploy"
git push origin gh-pages

# Step 3: Enable Pages
gh api repos/:owner/:my-site/pages \
  -f source.branch=gh-pages
```

## Method 4: Quick Share (Temporary)

```bash
# gofile.io — no auth, permanent download page
SERVER=$(curl -s https://api.gofile.io/servers | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['servers'][0]['name'])")
curl -s -F "file=@index.html" "https://${SERVER}.gofile.io/contents/uploadfile"

# Returns downloadPage URL
```

**Pitfalls:**
- Download page, not a rendered preview — HTML is served as a file download, not a live website
- gofile.io blocks certain file types (no .exe, .dmg, etc.)
- No guarantee of uptime or persistence
- Not suitable for HTML dashboards — use Surge or localhost.run instead

## Method 6: Vercel (Astro + GitHub Actions)

Full-stack CI/CD: Astro framework → GitHub Actions → Vercel deploy. This is the recommended path for any framework-based project.

### Prerequisites

- GitHub repo with code pushed
- Vercel access token (generate at https://vercel.com/account/tokens — "Full" scope)
- Public GitHub repo (or GitHub Vercel App installed for private repos)

### One-shot deploy (no GitHub integration needed)

```bash
cd /path/to/project

# Link project to Vercel (creates .vercel/project.json)
npx vercel link --token $VERCEL_TOKEN --yes --cwd .

# Deploy to production
npx vercel deploy --prod --token $VERCEL_TOKEN --yes

# Output: production URL, and aliased custom domain if configured
```

### Add custom domains

After deployment, attach domains via API:

```bash
# Find project ID from .vercel/project.json
PROJECT_ID=$(cat .vercel/project.json | python3 -c "import sys,json; print(json.load(sys.stdin)['projectId'])")

# Add root domain
curl -s -X POST "https://api.vercel.com/v10/projects/$PROJECT_ID/domains" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "example.com"}'

# Add subdomains
for sub in www mc energy bots childminding dev; do
  curl -s -X POST "https://api.vercel.com/v10/projects/$PROJECT_ID/domains" \
    -H "Authorization: Bearer $VERCEL_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"${sub}.example.com\"}"
done
```

### Set up GitHub Actions auto-deploy

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Vercel
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Vercel
        run: npx vercel --prod --token ${{ secrets.VERCEL_TOKEN }} --yes
```

Then add `VERCEL_TOKEN` as a GitHub Actions secret on the repo.

### Git push with PAT (no gh CLI)

When `gh` is unavailable, create the repo and push via API + git:

```bash
# 1. Create repo via API
curl -s -X POST -H "Authorization: bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/user/repos \
  -d '{"name":"my-repo","private":false,"description":"...","auto_init":false}'

# 2. Set local git identity (required if no global config)
git config user.email "you@example.com"
git config user.name "Your Name"

# 3. Init and commit
cd /path/to/project
git init
git branch -m main
git add -A
git commit -m "Initial commit"

# 4. Add remote with token embedded
GH_USER=$(curl -s -H "Authorization: bearer $GITHUB_TOKEN" \
  https://api.github.com/user | python3 -c "import sys,json; print(json.load(sys.stdin)['login'])")
git remote add origin https://$GH_USER:$GITHUB_TOKEN@github.com/$GH_USER/my-repo.git
git push -u origin main
```

### Switch DNS to Vercel

When migrating from Cloudflare Tunnel to Vercel, update DNS:

1. In Cloudflare, change CNAME records from `<tunnel-id>.cfargotunnel.com` to `cname.vercel-dns.com`
2. Subdomains: `proxied: false` (DNS-only), apex: `proxied: true` (CNAME flattening via Cloudflare proxy)
3. Vercel auto-generates SSL certs for all connected domains
4. The API backend can stay on a separate tunnel subdomain: `api.example.com → <tunnel-id>.cfargotunnel.com`

```bash
# Update subdomains in bulk
for record_id in <subdomain-record-ids>; do
  curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$record_id" \
    -H "Authorization: Bearer $CF_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"type":"CNAME","name":"'"$SUB"'","content":"cname.vercel-dns.com","ttl":1,"proxied":false}'
done
```

### Pitfalls

- `npx vercel link --token $TOKEN` fails with `option requires argument: --token` if the token value is missing or empty
- Vercel + GitHub integration requires the Vercel GitHub App to be installed; without it, `Link GitHub repository` fails. Use the deploy hook or standalone deploy command as workaround
- After adding a domain on Vercel, it says "verified" immediately, but SSL cert generation is async (takes 10-60s)
- `vercel deploy` uploads the entire cwd unless `.vercelignore` is set. Node_modules is auto-ignored by Vercel
- The Vercel CLI resolves `--token` as requiring an arg: `vercel --token` without a value prints help instead of an error. Always pass `--token $TOKEN` where `$TOKEN` is set
6. **`npm create astro@latest` generates a random placeholder name** (e.g. "fumbling-field") in package.json — rename to match the project immediately
7. **`require()` fails in Astro's ESM context** — `.astro` frontmatter runs in ESM. Never use `require('os')`, `require('fs')` etc. Use `import os from 'node:os'` instead for server-side system metrics in frontmatter.
8. **Template literals in JSX expression blocks** — esbuild can choke on backtick template literals inside `{ }` expression blocks in `.astro` files. The error looks like `Unexpected "const"` at column 776 (a transpiled single-line column). Fix: use string concatenation (`'foo' + bar`) instead of backticks inside JSX blocks (`\`foo ${bar}\``).
- `cloudflared tunnel run --config path` vs `cloudflared tunnel --config path run` — the options must come BEFORE the subcommand. `cloudflared tunnel run` interprets `--config path` as an unknown flag and prints help instead of running. Correct: `cloudflared tunnel --config path run`.

Deploy to a Proxmox LXC container on your own hardware. The LAN IP is permanent. See **`proxmox-host-creation`** skill for full provisioning details.

### Quick Redeploy (container already set up)

```bash
# From Hermes VM, copy files to container (if SSH works)
scp -o StrictHostKeyChecking=no -r ./dist/* root@<container-ip>:/var/www/<sitename>/

# OR via Proxmox shell (pct push)
curl -s http://192.168.1.6:8000/index.html > /tmp/site.html \
  && pct push 200 /tmp/site.html /var/www/<sitename>/index.html \
  && rm /tmp/site.html
```

### Making it Internet-Accessible

See **`cloudflare-dns-management`** skill for:
- Creating DNS A records pointing to the container IP
- Cloudflare proxied (orange cloud) for SSL/DDoS protection
- Setting up Cloudflare Tunnel for port-free ingress
- Permanent HTTPS via Cloudflare edge

For Mission Control-style dashboards:

```bash
mkdir -p ./dist
# Write index.html to ./dist/
# Deploy:
npx surge ./dist mission-control.surge.sh
# OR for temp preview:
cd ./dist && python3 -m http.server 8080 &
ssh -R 80:localhost:8080 nokey@localhost.run
```

See also: `cloudflare-dns-management` (DNS records, tunnels, HTTPS), `proxmox-host-creation` (LXC containers, nginx setup)

## References

| File | Content |
|------|---------|
| `references/localhost-run-tunnel.md` | Detailed localhost.run tunnel usage |
| `references/tunnel-503-propagate.md` | Diagnosing and recovering from 503 errors |
| `references/astro-vercel-cicd-pattern.md` | Full Astro 5 scaffold with GitHub Actions CI/CD and Vercel deployment |
| `references/vercel-tunnel-migration.md` | Migrating from Cloudflare Tunnel to Vercel (DNS swap, API subdomain, tunnel ingress update) |

## Verification

```bash
# After deploy, verify the URL responds
curl -sI https://your-deployed-url.example.com | head -5
```

If the tunnel URL returns 503, see `references/tunnel-503-propagate.md` for diagnosis and recovery.
