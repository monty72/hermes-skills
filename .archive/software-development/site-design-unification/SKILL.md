---
name: site-design-unification
description: Apply a reference page's design language (colours, components, layout patterns) uniformly across all pages of a multi-page Astro static site. Extract CSS classes from a reference page into shared global utilities, then refactor every page to use them.
category: software-development
tags: [astro, css, design-system, tailwind, refactoring, vercel]
---

# Site Design Unification

## When to Use The user says "apply X page's colours and features to the whole site", "make everything look like page Y", "unify the design across all pages", or you detect CSS class duplication / hardcoded colour values across pages that should share the same design tokens.

## Workflow

### 1. Assess Current State
- Navigate to the **reference page** (the one with the desired look): `browser_navigate(url)`
- Navigate to the **homepage** and at least 2-3 other sub-pages to compare
- Read the reference page's source code: `read_file(path)` — identify its CSS classes, colour values, layout components (tabs, cards, badges, banners, pills, stat blocks, headers)
- Read the global CSS: `read_file(path)` — check existing CSS variables and utility classes
- Read all `.astro` page files under `src/pages/` to understand the full scope

### 2. Extract a Shared CSS Class System (global.css)
Create/update utility classes for every component pattern you see reused. Target:
- **Page headers**: `.content-header`, `.content-header-back`, `.content-header-title`, `.content-header-subtitle`
- **Cards**: `.content-card`, `.section-card`, `.section-card-header`, `.product-card`
- **Navigation pills**: `.pill-link`
- **Status/metric blocks**: `.stat-card`, `.stat-card-label`, `.stat-card-value`, `.stat-card-sub`
- **Info banners/callouts**: `.info-banner`, `.info-banner-blue`, `.info-banner-amber`, `.info-banner-green`
- **Badges**: `.badge`
- **Tabs** (if needed): `.cm-tabs`, `.cm-tab`, `.cm-tab-content`, `@keyframes cm-fade-in`, `.scrollbar-none`

Use the site's CSS variable system (e.g. `--color-lo-text`, `--color-lo-primary`) inside these classes for maintainability. Avoid hardcoding colour hex values in utility classes.

### 3. Refactor Each Page
Work through every `.astro` page file (under `src/pages/`). For each page:
- **Back links**: Replace `text-sm text-[#6b7280] hover:text-[#111827] transition-colors no-underline` → `content-header-back`
- **Page titles**: Replace `text-xl font-bold text-[#111827] tracking-tight` → `content-header-title`
- **Page subtitles**: Replace `text-sm text-[#6b7280] font-mono` → `content-header-subtitle`
- **Pill/quick links**: Replace `px-3 py-1.5 rounded border border-[#e5e7eb] text-xs text-[#6b7280] hover:border-[#6b21a8]/30 hover:text-[#111827] transition-all no-underline` → `pill-link`
- **Info banners**: Replace `p-4 rounded bg-blue-50 border border-blue-200/30 mb-8 text-sm text-[#6b7280]` → `info-banner info-banner-blue`
- **Stat blocks**: Replace `rounded border border-[#e5e7eb] bg-white p-3` → `stat-card`
- **Hardcoded colours**: Replace `text-[#111827]` → `text-lo-text`, `text-[#6b7280]` → `text-lo-text-muted`, `bg-[#6b21a8]/10` → `bg-lo-primary/10`, `border-[#e5e7eb]` → `border-lo-border`, `text-[#22c55e]` → `text-lo-success`, etc.

Use `patch(mode='replace')` for each targeted change — one per class migration.

### 4. Build & Verify
```bash
cd ~/dev-site
npm run build
```

Check for build errors. All routes should compile cleanly with no warnings beyond benign `Generated an empty chunk` messages.

### 5. Deploy
- If Vercel auto-deploys from GitHub (most common):
  ```bash
  git add -A
  git commit -m "Site-wide design consistency: shared CSS classes for headers, badges, pills, info banners, and tabbed interface"
  git push origin main
  ```
- Wait ~30 seconds for Vercel deploy, then verify with `curl -s -o /dev/null -w "%{http_code}" https://montygroup.uk`
- Navigate to 2-3 pages in browser to confirm rendering

### 6. Verify Visually
Open the reference page and at least 2 other pages in the browser to confirm:
- Headers are consistently styled
- Colours match the reference page
- No broken layouts or missing CSS
- Tab/accordion interactivity still works (if applicable)

## Pitfalls
- **Don't assume colours differ** — the reference page may already share the same palette. Compare CSS variables before changing anything.
- **Hardcoded hex colours in JSX templates** need separate patches from CSS classes. Check inline `style=` attributes too (e.g. `<div style="color: #6b21a8">`).
- **Edge case: JS-generated HTML** — pages with client-side scripts that create DOM elements (like calculator results, deal feeds) may hardcode colours in template literals. These need separate patches.
- **Edge case: CSS variable names** — if the site uses `@theme inline` in Tailwind v4, CSS variables are accessible as `var(--color-lo-text)` or Tailwind classes like `text-lo-text`. Prefer Tailwind utility classes over raw CSS variables in `.astro` templates.
- **Edge case: Astro components** — check if reusable components exist in `src/components/` that also need updating.
