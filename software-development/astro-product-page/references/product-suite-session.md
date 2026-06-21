# Product Suite Session — June 2026

## Site Context
- **Repo:** `monty72/montygroup-astro` at `~/dev-site`
- **Framework:** Astro 5 + Tailwind
- **Hosting:** Cloudflare Pages (auto-deploy via GitHub Actions, workflow `deploy-cloudflare.yml`)
- **Hub page:** `src/pages/tools/index.astro`
- **Products dir:** `public/products/`
- **Site URL:** `montygroup.uk`

## Products Created/Managed

### 1. Azure WAF Review Toolkit (£29)
- **Page:** `src/pages/tools/waf-review-toolkit.astro`
- **Generation script:** `scripts/generate-waf-toolkit.py` (fpdf2 + openpyxl)
- **Files:** `waf-review-scorecard.xlsx`, `waf-review-guide.pdf`, `waf-review-toolkit.zip`
- **Key pattern:** 90 questions across 6 WAF pillars, radar chart in Excel, 22-page PDF guide

### 2. ADR Template Pack (£19)
- **Page:** `src/pages/tools/azure-adr-templates/index.astro`
- **Files:** `adr-template-pack.zip` (Markdown template, YAML template, worked AKS example, README)
- **Key pattern:** Two formats (human-readable Markdown + machine-parseable YAML) + completed example

### 3. Platform Engineering Playbook (£39)
- **Page:** `src/pages/tools/platform-engineering-playbook/index.astro`
- **Generation script:** `scripts/generate-playbook.py` (fpdf2, 11 chapters)
- **File:** `platform-engineering-playbook.pdf`
- **Key pattern:** 10 chapters + 90-day implementation plan

### 4. Backstage Plugin Starters (£39)
- **Page:** `src/pages/tools/backstage-plugin-starters/index.astro`
- **File:** `backstage-plugin-starters.zip` (24.8KB, 27 files across 4 starter templates)
- **Templates:** Full plugin scaffold, widget template, scaffolder action, entity provider
- **Key pattern:** Real TypeScript code following Backstage v1.30+ conventions, Jest tests included

## Name Scrubbing Session
- All personal references (Matt Hogarth, Royal Mail, personal email) removed from site and artefacts
- `src/pages/matt.astro` → `src/pages/about.astro` (generic About page)
- WAF guide PDF "About the Author" section → "About This Toolkit" (no personal name)
- Playbook PDF author line removed
- ADR example "Author: Matt Hogarth" removed
- All ZIPs regenerated with clean files
- Memory updated with scrubbed site state

## Key Commands
```bash
# Build
cd ~/dev-site && npm run build

# Check build routes
# Look for "N page(s) built in Xs" — count should include new product page

# Generate WAF toolkit
python3 scripts/generate-waf-toolkit.py

# Generate playbook
python3 scripts/generate-playbook.py

# Verify PDF is clean
pdftotext public/products/waf-review-guide.pdf - | grep -i "matt\|hogarth\|royal mail"

# Deploy
git add -A && git commit -m "msg" && git push

# Check deploy status
gh run list --workflow deploy-cloudflare.yml --limit 1 --json conclusion,status

# Verify live
curl -s https://montygroup.uk/tools/ | grep -c "Available Now"
```
