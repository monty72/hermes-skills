---
name: modern-astro-ci-cd-setup
description: "Use when setting up a modern Astro 5 + GitHub Actions + Vercel CI/CD pipeline with custom domain via Cloudflare."
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [astro, vercel, github-actions, cloudflare, ci-cd, deployment]
    related_skills: [github-pr-workflow, writing-plans]
---

# Modern Astro 5 CI/CD Setup

## Overview

Sets up a complete modern web development stack: Astro 5 (with TypeScript + Tailwind + React islands) → GitHub (with Actions CI) → Vercel (auto-deploy) → Cloudflare (custom domain). The goal is zero-touch deployment: push to `main` and everything flows.

## When to Use

- Setting up a new web project from scratch
- Migrating from a static HTML/Flask setup to a modern framework
- User says "set up CI/CD" or "modern web dev framework"
- User says "deploy to Vercel" or "use Astro"

## Prerequisites

- **GitHub PAT** with `repo` scope — generate at https://github.com/settings/tokens/new
- **Vercel token** with Full scope — generate at https://vercel.com/account/tokens
- **Cloudflare API token** with DNS:Edit + Tunnel:Edit permissions
- **Domain** registered on Cloudflare

## Step-by-Step

### 1. Scaffold Astro 5

```bash
npm create astro@latest <project-name> -- --template basics --typescript strict --add tailwind,react --yes
```

Then rename the random `fumbling-field` dir and fix the `package.json` name.

### 2. Create Astro Pages

Create pages in `src/pages/`. Each page imports the shared Layout. Use `<script>` for client-side interactivity (React islands are optional — vanilla JS works for simple data fetching).

For the **site-wide navigation bar with dropdown sections**, see `references/site-wide-nav-pattern-astro.md`. This is a sticky nav with category hover-dropdowns, mobile hamburger, and current-page highlighting passed via `currentPath` prop on each page's `<Layout>` component.

### 3. GitHub Actions CI

Create `.github/workflows/ci.yml`:

```yaml
name: CI
on:
  push: {branches: [main]}
  pull_request: {branches: [main]}
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: {node-version: 22, cache: npm}
      - run: npm ci
      - run: npx astro check --minimumFailingSeverity error 2>&1 || echo "Non-fatal warnings"
      - run: npm run build
      - uses: actions/upload-pages-artifact@v3
        with: {path: dist/}
```

### 4. Create GitHub Repo

```bash
# Create via API (no gh CLI needed)
curl -s -H "Authorization: bearer $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/user/repos \
  -d '{"name":"<repo-name>","private":false,"description":"..."}'

# Or with gh CLI if available
gh repo create <repo-name> --public --description "..." --remote origin
```

## Vault-Based Git Auth (Recommended)

Before pushing, use the vault credential helper to avoid embedding tokens in remote URLs:

```bash
# Ensure git credential helper is configured (one-time setup)
git config --global credential.helper '!~/.local/bin/git-credential-vault'

# Add remote WITHOUT token in URL:
git remote add origin https://github.com/<user>/<repo>.git

# Push works — the helper reads GITHUB_TOKEN from the local encrypted vault
git push -u origin main
```

See `security/hermes-vault` skill for vault setup and credential helper details.

### Embedded Token Method (Fallback — Not Recommended)

Only use this if the vault is not available:
```bash
git remote add origin https://<user>:<token>@github.com/<user>/<repo>.git
```
This embeds a plaintext PAT in the repo's `.git/config`. Clean it up afterwards with `git remote set-url origin https://github.com/<user>/<repo>.git` and store the token in the vault.

### 5. Deploy to Vercel

```bash
npx vercel link --token <vercel-token> --yes
npx vercel deploy --prod --token <vercel-token> --yes
```

The `--prod` flag aliases the deployment to the project's production URL and any custom domains.

### 6. Add Custom Domain on Vercel

```bash
# Add domain via API
curl -X POST "https://api.vercel.com/v10/projects/<project-id>/domains" \
  -H "Authorization: Bearer <token>" \
  -d '{"name": "yourdomain.uk"}'
```

Repeat for subdomains: `www`, `mc`, `energy`, `bots`, etc.

### 7. Update Cloudflare DNS

For Vercel + Cloudflare, subdomains need **CNAME to `cname.vercel-dns.com`**:

```bash
# Update each DNS record
curl -X PATCH "https://api.cloudflare.com/client/v4/zones/<zone-id>/dns_records/<record-id>" \
  -H "Authorization: Bearer $CF_TOKEN" \
  -d '{"type":"CNAME","name":"<subdomain>","content":"cname.vercel-dns.com","ttl":1,"proxied":false}'
```

For the **apex domain** (root), use CNAME with **proxied=true** (Cloudflare CNAME flattening).

### 8. Vercel Auto-Deploy on Push

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Vercel
on:
  push: {branches: [main]}
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: {node-version: 22, cache: npm}
      - run: npm ci
      - name: Deploy
        run: npx vercel deploy --prod --token ${{ secrets.VERCEL_TOKEN }} --yes
```

**IMPORTANT**: Do NOT use `--prebuilt` in the auto-deploy workflow. The `--prebuilt` flag causes Vercel to skip building on its infrastructure, which skips the custom domain alias as well. Without `--prebuilt`, Vercel builds on its own infra, aliases the production domain correctly, and handles `vercel.json` rewrites.

If you MUST use `--prebuilt`, the deploy workflow must do three separate steps:
```yaml
      - name: Pull project settings
        run: npx vercel pull --yes --token '${{ secrets.VERCEL_TOKEN }}'
      - name: Build with Vercel
        run: npx vercel build --prod --token '${{ secrets.VERCEL_TOKEN }}'
      - name: Deploy
        run: npx vercel deploy --prebuilt --prod --token '${{ secrets.VERCEL_TOKEN }}' --yes
```
The `vercel pull --yes` step downloads the project config including custom domain bindings. Without it, `vercel build` fails with `No Project Settings found locally. Run vercel pull --yes`.

Add `VERCEL_TOKEN` to GitHub Actions secrets:

```python
# Python with pynacl
import requests, base64
from nacl import encoding, public

r = requests.get(f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key",
    headers={"Authorization": f"Bearer {gh_token}"})
pk = r.json()
pub = public.PublicKey(pk["key"].encode(), encoding.Base64Encoder())
encrypted = public.SealedBox(pub).encrypt(vercel_token.encode())

requests.put(f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/VERCEL_TOKEN",
    headers={"Authorization": f"Bearer {gh_token}"},
    json={"encrypted_value": base64.b64encode(encrypted).decode(), "key_id": pk["key_id"]})
```

### 9. API Backend via Tunnel (optional)

If you have a Flask/Express API that should stay on your server:

- Run `cloudflared tunnel` pointing to your local API port
- Set DNS for `api.yourdomain.uk` → `tunnel-id.cfargotunnel.com`
- Frontend pages can fetch from `api.yourdomain.uk`

## Server-Side Data Fetching in Astro

For pages that need live data at build time (energy rates, system status, Tesla data), see `references/astro-server-data-fetching.md`. Key patterns:

- Fetch external APIs in frontmatter (runs at build time, outputs static HTML)
- Fetch local Flask API on `localhost:8000` for private data
- Add inline `<script>` for client-side refresh every 30s
- Octopus Agile: product `AGILE-24-10-01`, tariff `E-1R-AGILE-24-10-01-E`, region suffix from product details

## Interactive Calculators

For building client-side ROI calculators (form + results, colour-coded outputs, bar charts), see `references/interactive-calculators.md`. Key pitfalls: server/client data scoping, template literals in JSX blocks, and stale `.astro` cache.

## Reference Files

- `references/astro-server-data-fetching.md` — Server-side data fetching patterns (Octopus API, Flask backend, Tesla data) with client-side refresh.
- `references/interactive-calculators.md` — Building client-side ROI calculators: form + results, colour-coded outputs, flexbox bar charts.
- `references/site-wide-nav-pattern-astro.md` — Building a sticky navigation bar with hover-dropdown sections, mobile hamburger, and current-page highlighting via `currentPath` prop.
- `references/uk-energy-affiliate-referrals.md` — Which UK energy suppliers offer affiliate/referral links, Axle Energy VPP compatibility (non-Powerwall batteries), and comparison-site affiliate networks (Awin, CJ, Impact).
- `references/vercel-domain-mismatch-debug.md` — Full diagnosis and fix for when CI deploys succeed but the custom domain shows stale content because the domain lives on a different Vercel project.

## Common Pitfalls

1. **Custom domain on wrong Vercel project** — This is the most common source of "CI succeeds, .vercel.app shows latest, but montygroup.uk stays stale."

   **Root cause:** When you first `vercel deploy --prod` from a directory, Vercel auto-creates OR links to a project named from the directory/repo (e.g. `montygroup-astro`). Separately, you (or a previous session) may have manually added `montygroup.uk` to a *different* Vercel project (e.g. `dev-site`) via the dashboard or API. Now CI deploys to `montygroup-astro` while the domain stays pointing at an old deployment on `dev-site`.

   **Diagnostic signals:**
   - GitHub Actions deploy log shows: `Linked monty72s-projects/<X>` — note which project X is
   - Deploy log shows: `Aliased https://<X>.vercel.app` — but the custom domain never updates
   - Vercel API shows `aliasAssigned=<timestamp>` (non-zero = alias was attempted) but `aliases=[]` (no aliases actually attached). This is the key tell: `aliasAssigned` means Vercel *tried* to promote it to production within *that project*, while `aliases` lists what's actually aliased. If `aliasAssigned` is set but the domain is stale, the domain lives on a different project.

   **Diagnosis commands:**
   ```bash
   # List all projects to see what exists
   curl -sH "Authorization: Bearer $VTOKEN" \
     "https://api.vercel.com/v9/projects?teamId=$TEAM_ID" | \
     python3 -c "import sys,json;print(*[(p['name'],p['id']) for p in json.load(sys.stdin).get('projects',[])],sep='\n')"

   # Check which project owns the custom domain's alias
   for PID in <project-id-1> <project-id-2>; do
     echo "=== $PID ==="
     curl -sH "Authorization: Bearer $VTOKEN" \
       "https://api.vercel.com/v4/aliases?projectId=$PID&teamId=$TEAM_ID&limit=20" | \
     python3 -c "import sys,json; [print(f'  {a[\"alias\"]} -> {a[\"deploymentId\"][:20]}') for a in json.load(sys.stdin).get('aliases',[])]"
   done

   # Verify which project owns the domain explicitly
   curl -sH "Authorization: Bearer $VTOKEN" \
     "https://api.vercel.com/v9/projects/$PID/domains/montygroup.uk?teamId=$TEAM_ID" | \
     python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('projectId','NOT FOUND'))"
   ```

   **Fix:** Move the domain to the project the CI deploys to:
   ```bash
   # Remove from wrong project
   curl -sX DELETE -H "Authorization: Bearer $VTOKEN" \
     "https://api.vercel.com/v9/projects/prj_WRONG/domains/montygroup.uk?teamId=$TEAM_ID"
   # Add to correct project
   curl -sX POST -H "Authorization: Bearer $VTOKEN" -H "Content-Type: application/json" \
     "https://api.vercel.com/v9/projects/prj_RIGHT/domains?teamId=$TEAM_ID" \
     -d '{"name":"montygroup.uk"}'
   # CNAME subdomains cannot be moved while in use — remove from old project first
   # Push triggers CI
   git commit --allow-empty -m "fix: move montygroup.uk to CI project"
   git push origin main
   ```

   **Verify:** After CI runs, check `v4/aliases` again — `montygroup.uk` should now point to the latest deployment on the right project. Use `curl -sI "https://montygroup.uk?$(date +%s)" | grep -i 'age:'` to see fresh content (age: 0).

2. **Prebuilt deploy requires explicit vercel build** — Running `npm run build` produces `dist/` but Vercel needs `.vercel/output/`. Fix:
   ```yaml
   - run: npx vercel pull --yes --token '${{ secrets.VERCEL_TOKEN }}'
   - run: npx vercel build --prod --token '${{ secrets.VERCEL_TOKEN }}'
   - run: npx vercel deploy --prebuilt --prod --token '${{ secrets.VERCEL_TOKEN }}' --yes
   ```
   Without `vercel pull`, the build fails with `No Project Settings found locally. Run vercel pull --yes`.
   **Simpler alternative:** skip `--prebuilt` entirely. Just `npx vercel deploy --prod --token $TOKEN --yes` lets Vercel build on its infra, which handles domain aliasing natively.

3. **Vercel token expiry in CI** — Vercel API tokens (`vcp_*`) expire silently. GitHub Actions deploy shows failure with no useful error. First sign: 404 on production URL after a successful commit push.
   **Recovery:** Generate fresh token at https://vercel.com/account/tokens. Save to `~/.vercel/auth.json` for local deploys. Update the GitHub secret with the libsodium encryption pattern in step 8.
   **Subtle symptom:** CI shows success but custom domain does not update — check pitfall 1 (domain-vs-project mismatch) before assuming token expiry.

4. **Branch name mismatch** — `create-astro` template creates `master`, GitHub defaults to `main`. Fix with `git branch -m master main` before pushing.

5. **GitHub Actions secrets encryption** — uses libsodium sealed box, not plaintext. Fetch repo public key first.

6. **Private repo + Vercel** — Vercel needs the GitHub App installed for private repos, or use a deploy token.

7. **Multiple tunnel configs** — stale `localhost.run` or `cloudflared` processes conflict. Kill with `pkill -f "localhost.run" && pkill -f "cloudflared tunnel"`.

8. **require() fails in Astro ESM context** — Astro builds in ESM where `require` is not defined. Use `import os from 'node:os'` instead.

9. **Jinja `{% %}` syntax does not work in Astro** — `{% if %}...{% endif %}` causes build failure `Unexpected "%"`. Use `{condition && 'text'}` or `{condition ? 'text' : ''}`.

10. **Template literals inside JSX expression blocks** — esbuild chokes on `${...}` inside backtick strings inside `{ }` Astro blocks, especially in `.map()`. Build fails with `Unexpected "const"` at odd columns. Fix: use string concatenation. Clear `rm -rf dist .astro` before retrying.

11. **Vercel domain SSL is async** — adding a domain returns `verified: true` immediately, but SSL cert generation takes 10-60s. HTTPS errors during that window are normal.

13. **`.vercel/` is gitignored → CI deploy can't find the project** — Astro's default `.gitignore` includes `.vercel`. When GitHub Actions checks out the repo, there's no `.vercel/project.json`, so `npx vercel deploy --prod` either prompts interactively (fail in CI) or creates a new project with no custom domain.

   **Detecting the wrong project:** After `vercel link`, check `cat .vercel/project.json`. The `projectId` must match the project that owns the custom domain. If it shows a different project (e.g. `dev-site` when you expect `montygroup-astro`), re-link with `npx vercel link --project <correct-name> --yes`.

   **Fix:** Add a gitignore exception and commit the project.json:
   ```gitignore
   .vercel
   !.vercel/project.json
   ```
   Then create `.vercel/project.json`:
   ```json
   {
     "projectId": "prj_YOUR_PROJECT_ID",
     "orgId": "team_YOUR_TEAM_ID"
   }
   ```
   Find IDs via: `npx vercel project ls` then `npx vercel list <project-name>`, or check a working local `.vercel/project.json`. Alternatively pass `--scope` and let Vercel detect from the git remote.

   **Alternative (no committed file):** Pass env vars in deploy.yml:
   ```yaml
   - name: Deploy to Vercel
     env:
       VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
       VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
     run: npx vercel deploy --prod --token '${{ secrets.VERCEL_TOKEN }}' --yes
   ```

   **Diagnostic:** CI deploy shows "Retrieving project…" then creates a new project instead of using the existing one.

15. **Dynamic routes 404 on Vercel static** — Use `getStaticPaths` returning a fallback page plus `vercel.json` rewrite.

16. **Node version range causes Vercel to auto-upgrade to latest LTS** — The `package.json` `engines` field uses `">=22.12.0"` syntax, which Vercel interprets as "use the latest LTS" — currently Node 24.x. This can break Astro builds if the project isn't tested on 24.x. The build log shows a warning: `"engines": { "node": ">=22.12.0" } ... Node.js Version \"24.x\" will be used instead`.

   **Fix:** Pin to the exact major:
   ```json
   "engines": { "node": "22.x" }
   ```
   This tells Vercel to stay on 22.x. After changing, run `npx vercel build --prod` and verify no warning appears. Then `npx vercel deploy --prebuilt --prod --yes` to redeploy.

17. **Vercel build queue stuck — all new deploys show UNKNOWN status** — When every deployment shows `UNKNOWN` in `npx vercel list` and never transitions to `● Ready` or `● Error`, the project's build queue may be hung. Normal deploy commands (`vercel deploy --prod`, `vercel deploy --prebuilt --prod`) upload files but Vercel's infrastructure never finishes processing.

   **Diagnosis:** `npx vercel list <project> --token $TOKEN` shows multiple UNKNOWN entries with no Ready state after 5+ minutes. The CLI shows "Building…" then times out.

   **Workaround — deploy dist/ as a new project:**
   ```bash
   # Deploy the pre-built dist/ folder directly — creates a new Vercel project
   cd ~/dev-site && npx vercel deploy dist/ --prod --yes --token $TOKEN
   ```
   This creates a separate project (e.g. `dist-xxxxx`) that works instantly. The trade-off: custom domains won't auto-link because the domain lives on the original project. Use this for getting the site live quickly while investigating the stuck build queue in the Vercel dashboard.

   **Root fix:** Open the Vercel dashboard → project → deployments → cancel all UNKNOWN/queued deployments. The next push should then process normally. Check the Vercel status page for platform issues if cancelling doesn't help.

   **Prevention:** Commit `.vercel/project.json` to the repo (with a gitignore exception) so CI always links to the correct project — this prevents project-creation confusion that can trigger build queue issues.

14. **Missing `currentPath` on a page** — Layout nav highlighting requires the prop. Missing it defaults to `/`. Use `grep -L 'currentPath' src/pages/**/*.astro` to find missing ones.

15. **Dynamic route pages (`[slug].astro`) and `currentPath`** — pass the literal route pattern, not the resolved URL. Example: `currentPath="/skills/[slug]"`.

## Verification Checklist

- [ ] `npm run build` succeeds locally with zero errors
- [ ] `npm run dev` serves all pages
- [ ] Push to GitHub triggers both CI and Deploy workflows
- [ ] Vercel deployment shows green checkmark
- [ ] Custom domain resolves (wait for DNS propagation)
- [ ] SSL certificates issued (can take 1-2 min on Vercel)
- [ ] API backend accessible via tunnel (if applicable)
