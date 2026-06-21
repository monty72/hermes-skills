---
name: astro-product-page
description: "Create consistent product/landing pages for digital goods on an Astro + Tailwind marketing site. Covers page structure, artefact generation (PDFs, ZIPs, starter templates), bundling, hub integration, and deployment. Use when adding a new paid/free digital product to an existing site."
version: 1.0.0
author: Hermes Agent
related_skills: [modern-astro-ci-cd-setup]
---

# Astro Product Page

Use this skill when adding a **digital product** (template, toolkit, playbook, starter pack) to an existing **Astro + Tailwind marketing site**. This is a content-authoring task on a pre-existing site — not initial site build.

## Trigger Patterns

- "Add a product page for {tool/template}"
- "Work on {product name} next"
- "Create a download page for {digital good}"
- "Build out the products area"
- Making a "coming soon" product available

## Product Page Structure

### 1. Directory & Layout

Each product gets its own directory under the tools/products section:

```
src/pages/tools/<product-slug>/
  └── index.astro
```

Use a `Layout` import with `currentPath="/tools"` for consistent breadcrumb styling.

### 2. Component Pattern

The page uses these sections in order — maintain this structure for consistency:

```astro
---
import Layout from '../../../layouts/Layout.astro';

const features = [
  { icon: '📦', title: 'Feature Name', desc: 'One-line description' },
  // 6 features max — grids look best at 2/3 columns
];
---

<Layout currentPath="/tools" title="Product Name — MontyGroup">

  <!-- 1. Back link -->
  <div class="mb-4">
    <a href="/tools/" class="content-header-back">← Back to Tools</a>
  </div>

  <!-- 2. Hero — icon + title + tagline + badge + price + (future buy button) -->
  <div class="section-card mb-6">
    <div class="flex items-start gap-4">
      <span class="text-4xl shrink-0">{emoji}</span>
      <div>
        <h1 class="text-2xl font-bold text-lo-text mb-1">Product Name</h1>
        <p class="text-lo-text-muted text-sm mb-3">Tagline</p>
        <div class="flex flex-wrap items-center gap-3">
          <span class="text-2xl font-bold text-lo-primary">£XX</span>
          <span class="badge bg-lo-success/10 text-lo-success">Available Now</span>
          <span class="badge bg-lo-primary/10 text-lo-primary">Category</span>
        </div>
      </div>
    </div>
  </div>

  <!-- 3. What's Included — grid of feature cards -->
  <div class="section-card mb-6">
    <h2 class="section-card-header">📦 What's Included</h2>
    <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {features.map(f => (
        <div class="content-card">
          <div class="flex items-center gap-2 mb-1">
            <span>{f.icon}</span>
            <h3 class="font-semibold text-lo-text text-sm">{f.title}</h3>
          </div>
          <p class="text-xs text-lo-text-muted">{f.desc}</p>
        </div>
      ))}
    </div>
  </div>

  <!-- 4. Preview / code structure / visual (optional) -->
  <!-- 5. Why / value prop section -->
  <!-- 6. Target audience ("Who This Is For") -->
  <!-- 7. Pricing CTA — centered card with download button -->
  <div class="section-card mb-6 border-lo-primary/30 bg-lo-primary/5">
    <div class="text-center py-4">
      <h2 class="text-lg font-bold text-lo-text mb-1">Get the {Product}</h2>
      <p class="text-sm text-lo-text-muted mb-4">Lifetime updates — buy once, get every future revision.</p>
      <span class="text-3xl font-bold text-lo-primary block mb-1">£XX</span>
      <p class="text-xs text-lo-text-muted mb-4">Brief description of what's included</p>
      <a href="/products/{filename}.zip" class="inline-block px-8 py-3 rounded-lg bg-lo-primary text-white font-semibold hover:opacity-90 transition-opacity text-base no-underline">
        ⬇️ Download Now
      </a>
    </div>
  </div>

  <!-- 8. Footer -->
  <footer class="text-center text-xs text-lo-text-muted/40">
    <p>© 2026 MontyGroup · Built with Astro 5 · Cloudflare Pages</p>
  </footer>
</Layout>
```

## Artefact Generation & Hosting

### Artefact types
Digital products come in these formats — choose based on the product:

- **PDF guide/playbook** — Generate with `fpdf2` (available via `from fpdf import FPDF`). Store generation script in `scripts/generate-{product}.py` for regeneration.
- **Excel scorecard** — Generate with `openpyxl`. Same script approach.
- **ZIP bundle** — Contains all deliverable files. Build with `zipfile` in Python.
- **Starter code templates** — Real TypeScript/Python files with working code, not stubs. Use `delegate_task` for complex multi-file template generation.

### File locations
- Generated files → `public/products/{filename}`
- Generation scripts → `scripts/generate-{product}.py`
- ZIP bundles → `public/products/{product-slug}.zip`

### Artefact regeneration workflow
When artefacts need content fixes (e.g., removing personal info, updating pricing):

1. Find the generation script: `find ~/dev-site -name "generate-*" -type f`
2. Edit the script to fix the content
3. Re-run: `cd ~/dev-site && python3 scripts/generate-{product}.py`
4. Verify: `pdftotext public/products/{file}.pdf - | grep -i "personalname"` (should be empty)
5. Rebuild ZIP: Use `zipfile.ZipDeflated` to bundle updated files
6. If no generation script exists, write one or a one-off Python script

### ZIP bundle command
```python
import zipfile
with zipfile.ZipFile('public/products/bundle.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for filename in ['file1.pdf', 'file2.xlsx']:
        z.write(f'public/products/{filename}', filename)
```

## Hub Page Integration

### 1. Add to tools hub (src/pages/tools/index.astro)

Insert into the `tools` array with the right category and status:

```astro
{
  slug: 'product-slug',
  icon: '🎭',
  title: 'Product Name',
  tagline: 'One-line description',
  price: '£XX',
  category: 'Category',  // Templates | Code | Guides | Spreadsheets
  status: 'available',    // or 'coming-soon'
},
```

### 2. Change status from coming-soon to available

Single `patch` on the status field in `src/pages/tools/index.astro`.

### 3. Update about section links (if they changed)

If you rename or restructure pages, check all cross-references to ensure the about/about page links still work.

## Build & Deploy

```bash
cd ~/dev-site
npm run build           # Verify all pages compile — check route count
git add -A && git status --short
git commit -m "feat: add {Product Name} product + artefacts"
git push                # Triggers Cloudflare Pages auto-deploy via GitHub Actions
```

Verify deployment: `gh run list --workflow deploy-cloudflare.yml --limit 1` then curl live URLs.

## Pitfalls

1. **Artefacts with personal info** — Always check PDFs and ZIPs after generation. The generation script is where personal references live, not the output. Fix the script, regenerate, rebuild ZIPs.
2. **Binary file regeneration** — PDFs and ZIPs can't be patched with `patch` tool. You MUST regenerate from source or run the generation script.
3. **Consistent page structure** — All product pages should follow the same section order: Hero → What's Included → Preview → Why → Audience → Pricing CTA. Inconsistent page layouts confuse buyers.
4. **Artefact download links** — Astro serves everything under `public/` at the site root, so a file at `public/products/bundle.zip` is available at `/products/bundle.zip`.
5. **Product page title tag** — Use format `"{Product Name} — {Category} — {SiteName}"` for the `<Layout title="...">` prop.
6. **URL slug convention** — `tools/{product-slug}` where slug is lowercase with hyphens. No trailing version numbers.
7. **Status consistency** — Mark a product as `available` in the hub ONLY after the product page, artefacts, and ZIP are all created and the build passes.
