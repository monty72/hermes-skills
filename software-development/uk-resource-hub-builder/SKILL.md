---
name: uk-resource-hub-builder
description: "Build comprehensive UK-focused resource hub / directory sites — research methodology, site structure, SVG illustrations, tabbed UI, site-wide design unification (CSS class system extraction), monetization layers (shop, newsletter, affiliate disclosure), and deployment. Full lifecycle from content gathering to live URL."
version: 1.2.0
author: Hermes Agent
related_skills: [brave-web-search, modern-astro-ci-cd-setup]
---

# UK Resource Hub Builder

Use this skill when building a **resource directory / hub site** focused on a UK-specific topic (regulations, services providers, community). This covers the pattern we used for the UK childminding site.

For the site-wide navigation bar pattern (sticky nav with category hover-dropdowns), see `references/site-wide-nav-pattern-astro.md` in the `modern-astro-ci-cd-setup` skill — this is the UI that wraps the resource hub pages.

For the Brave Search API research commands, see `brave-web-search`. For data research methodology (Brave Search, Wikipedia, Wayback Machine, fallback chain), see `references/data-research-patterns.md`.

## The Pattern

1. **Research** — gather authoritative UK sources (GOV.UK, professional bodies, Ofsted, HMRC, PACEY, etc.) using Brave Search API (load `brave-web-search` skill)
2. **Structure** — hero + getting started + key topics + resources + FAQ
3. **Visuals** — hand-coded inline SVG illustrations for every section
4. **Monetize** — affiliate links, printable shop, newsletter, disclosure
5. **Deploy** — copy to nginx on permanent URL (not tunnel)

## Content Research

**Load `brave-web-search` skill for the research commands.** This avoids browser bot detection and returns clean JSON results.

For UK-focused sites, prioritise these sources — search with queries like `"UK childminding regulations 2026 Ofsted"` or `"EYFS framework 2026 statutory guidance"`:

- **GOV.UK** — primary legislation, statutory guidance, registration processes (gov.uk/government/publications/...)
- **Professional bodies** — PACEY, NCMA, CACHE, NDNA, Ofsted
- **HMRC** — tax guidance, simplified expenses, self-employment rules
- **Government schemes** — Tax-Free Childcare, Early Years Funding, 15/30 hours
- **Training providers** — mandatory courses (first aid, safeguarding), CPD providers, free resources (Anna Freud, SEND Gateway)
- **Insurance companies** — Morton Michel, Childcare.co.uk, PACEY

Always include:
- A "Step 1" entry for first-time users (registration, getting started)
- Mandatory requirements tagged clearly (DBS, first aid, insurance)
- Links to official .gov.uk / .org.uk / .ac.uk sources
- Free resources tagged separately from paid ones

## UX Layout Options

Two layout modes are available depending on page length and user preference:

### Option A: Long Scroll (default for moderate-length pages)
For pages with 3-5 sections and light content, use the standard single scroll layout with section headers, grid-2/grid-3 cards, and optional illustration columns. Good for overview pages and landing pages.

### Option B: Tabbed Navigation (preferred for dense content)
For pages with 5+ sections or when the user says the scroll layout feels too long, use a tabbed interface. This is the strongly preferred layout for this user — "a long list isn't the look I want."

Implementation:
1. Add horizontal tab bar below the hero with `<button>` elements
2. Each tab has `data-tab="section-id"` and click handler toggling `active` class
3. Each content section is a `<div class="cm-tab-content" id="tab-section-id">` — only the active one shows
4. Include an inline `<script>` with a plain JS click handler (no dependencies)
5. Use CSS `display: none` / `display: block` on `.cm-tab-content` / `.cm-tab-content.active`
6. Add a gentle fade-in animation (`@keyframes cm-fade` with opacity + translateY)
7. On mobile, the tab bar scrolls horizontally (`overflow-x: auto` with `scrollbar-width: none`)
8. First tab is active by default — class `active` on both the button and the content div

```css
/* Tab bar - horizontal scroll on mobile, no scrollbar */
.cm-tabs {
  display: flex;
  gap: 4px;
  border-bottom: 2px solid #e2e8f0;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

/* Tab buttons */
.cm-tab {
  flex-shrink: 0;
  padding: 10px 18px;
  font-size: 0.85rem;
  font-weight: 600;
  color: #64748b;
  background: none;
  border: none;
  border-bottom: 3px solid transparent;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}
.cm-tab.active {
  color: #2563eb;
  border-bottom-color: #2563eb;
  background: #eff6ff;
}

/* Tab content */
.cm-tab-content { display: none; }
.cm-tab-content.active { display: block; }

/* Fade animation */
@keyframes cm-fade {
  from { opacity: 0.4; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}
.cm-tab-content.active { animation: cm-fade 0.25s ease; }
```

```javascript
// Inline tab switching — no dependencies
const tabs = document.querySelectorAll('.cm-tab');
const contents = document.querySelectorAll('.cm-tab-content');
tabs.forEach(tab => {
  tab.addEventListener('click', () => {
    const target = tab.getAttribute('data-tab');
    tabs.forEach(t => { t.classList.remove('active'); t.setAttribute('aria-selected', 'false'); });
    contents.forEach(c => c.classList.remove('active'));
    tab.classList.add('active');
    tab.setAttribute('aria-selected', 'true');
    document.getElementById('tab-' + target)?.classList.add('active');
  });
});
```

### Organising tabs for a resource hub
- **Getting Started** — registration, legal requirements, first steps (always first tab)
- **Funding** — entitlements, rates, eligibility (if applicable)
- **Inspections** — Ofsted, grading, readiness tips (for regulated topics)
- **Framework** — statutory requirements, learning areas (for UK early years)
- **Policies** — document list / card grid (for template-heavy hubs)
- **Community** — social links, useful external links (always the last tab)

## Page Structure

### CSS Architecture
```css
:root {
  --bg: #0b0b12;
  --bg2: #11111e;
  --card: #16162a;
  --card-hover: #1c1c34;
  --border: #262640;
  --text: #eaeaef;
  --text2: #8a8aa5;
  --text3: #5a5a75;
  --accent: #6c8cff;
  --green: #34d399;
  --amber: #fbbf24;
  --red: #f87171;
  --purple: #a78bfa;
  --cyan: #22d3ee;
  --radius: 12px;
  --font: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}
```

### Grid layouts
- `.grid-2` — 2-column card grid (for main resource sections)
- `.grid-3` — 3-column card grid (for compact items)
- `.grid-visual` / `.grid-visual-rev` — 1fr + 240px grid (cards + illustration side by side)
- `.shop-grid` — auto-fill 220px product cards
- `@media (max-width: 720px)` — collapse to 1 column, hide `.visual-side`

### Section order
1. **Header** — title, description, meta (updated, region, age range)
2. **Quick nav bar** — pill-style section links
3. **Hero** — headline + paragraph + SVG illustration + stat
4. **Getting Started** — registration/steps with checklist illustration
5. **Key Topics 1** (e.g., Training & CPD) — with shield/safeguarding illustration
6. **Key Topics 2** (e.g., Funding & Finance) — with coins/funding illustration
7. **Key Topics 3** (e.g., Resources & Templates) — with bookshelf illustration
8. **Key Topics 4** (e.g., Insurance) — with shield illustration
9. **Key Topics 5** (e.g., Community) — with people illustration
10. **Affiliate Disclosure** — amber-highlighted legal banner
11. **Newsletter** — two-column email signup form
12. **Printable Shop** — 6 product cards with prices and download buttons
13. **FAQ** — accordion with common questions
14. **Footer** — disclaimer + credit

## SVG Illustration Techniques

The best approach for dark themes: **inline SVG elements** directly in the HTML (no external files, no image loading delays, responds to theme colours).

### Rules for inline SVGs
1. Use `<defs>` with unique prefixed gradient IDs to avoid ID collisions across multiple SVGs on the same page
2. Every illustration has a pale translucent `<circle>` background ring (r=120-200, stroke-opacity=0.04)
3. Use `rgba(108,140,255,0.XX)` for accent glows and backgrounds that match the theme
4. Add a `<filter id="...glow">` for heart and star decorations (applied via `filter="url(#id)"`)
5. Use `<g transform="translate(x,y)">` for positioning character elements — this keeps coordinates relative
6. Include floating hearts (♥) and stars (✦) as decorative elements with `filter="url(#glow)"`

### Character construction
| Element | Technique |
|---------|-----------|
| Head | `<circle>` + `<ellipse>` for hair |
| Body | `<ellipse>` with gradient fill |
| Eyes | small `<circle>` elements at y=22 (adult) or y=5-16 (child) |
| Smile | `<path d="M-x y Q0 y+n x y">` for the mouth curve |
| Arms | `<path>` with `stroke-linecap="round"` |
| Legs | `<path>` with `stroke-linecap="round"` |
| Ground | horizontal `<line>` with low-opacity stroke |

### Section-specific SVGs
| Section | Subject | Key elements |
|---------|---------|--------------|
| Hero | Childminder welcoming kids | Adult with open arms, 2 children running, hearts, ground line |
| Getting Started | Registration checklist | Clipboard with checkboxes (DBS, First Aid, EYFS, Ofsted), tick marks |
| Training | Safeguarding shield | Shield path, tick inside, DBS/PFA/OK badge circles |
| Funding | Money | Layered ellipses forming coin pile, £ sign, Funding/Tax-Free tags |
| Resources | Books/EYFS | Bookshelf with coloured rectangles, open book with "EYFS FRAMEWORK" label |
| Insurance | Protection shield | Larger shield, tick, "Public Liability up to £5M" text |
| Community | Connected people | 3 circles+ellipses, connecting dots and lines, hearts |
| Pre-FAQ | Children playing | 3 smaller figures, motion lines, hearts, ground ellipse |

## Monetization Layers

### 1. Affiliate Disclosure (legal requirement)
Place immediately before newsletter/shop sections:
```html
<div class="disclosure">
  <span>⚖️</span>
  <div><strong>Affiliate Disclosure:</strong> Some links on this site are affiliate links...
  <a href="...GOV.UK..." target="_blank">GOV.UK</a> and free resources are never affiliate links.</div>
</div>
```
CSS: amber border, card background, flex layout, 12px font.

### 2. Newsletter Signup
Two-column layout: text left, email form right.
```html
<form class="newsletter-form" onsubmit="event.preventDefault(); ...">
  <input type="email" placeholder="your@email.com" required>
  <button type="submit">Subscribe</button>
</form>
```
Place the demo confirmation message below and hide it initially with `display:none`.

### 3. Printable Shop
6 product cards in a responsive grid. Each card:
- `.preview` — emoji icon (📋 🛡️ 📝 💰 📅 📄)
- `.info` — title, description, price
- `.buy-btn` — download button with `onclick` demo alert

Pricing: £2.99 for simple templates, £3.99 for daily sheets, £4.99 for contracts, £5.99 for multi-part packs.

Product templates that work for any UK resource site:
1. **Daily record template** — diary/log sheet
2. **Risk assessment pack** — Ofsted-ready multi-form
3. **Registration/record form** — data capture form
4. **Expense/summary tracker** — simplified HMRC-style tracker
5. **Weekly planner** — themed, compliant with UK standards
6. **Contract/agreement** — legal-ish parent/provider agreement

### 4. Affiliate Link Opportunities (for UK childcare specifically)
| Provider | Type | Commission (est.) |
|----------|------|-------------------|
| Morton Michel | Insurance | £20-50 per signup |
| PACEY | Membership | Fixed per referral |
| Childcare.co.uk | Gold membership | Fixed per referral |
| St John Ambulance | First Aid courses | Per course |
| Red Cross | First Aid courses | Per course |
| Childcare CPD | Online courses | Per course |

### 5. Octopus Energy Referral (for energy/solar hubs)
See `references/uk-energy-affiliate-landscape.md` for the full supplier-by-supplier affiliate breakdown, cashback routes, and proven placement patterns.

## Site-Wide Design Unification

When you have a multi-page Astro site where pages have drifted in styling, use this pattern to extract a shared CSS class system from a reference page and apply it uniformly. This is a maintenance task for existing sites (not initial build).

### Workflow

1. **Identify the reference page** — the one with the desired look (usually the most polished or recently built page)
2. **Extract CSS classes** from the reference page into a shared `global.css`:
   - Page headers: `.content-header`, `.content-header-back`, `.content-header-title`, `.content-header-subtitle`
   - Cards: `.content-card`, `.section-card`, `.product-card`
   - Navigation pills: `.pill-link`
   - Status/metric blocks: `.stat-card`, `.stat-card-label`, `.stat-card-value`
   - Info banners: `.info-banner`, `.info-banner-blue`, `.info-banner-amber`, `.info-banner-green`
   - Badges: `.badge`
   - Tabs (if needed): `.cm-tabs`, `.cm-tab`, `.cm-tab-content`
3. **Use CSS variables** (e.g. `--color-lo-text`, `--color-lo-primary`) inside utility classes — avoid hardcoded hex values
4. **Refactor each page** — replace inline classes with shared utilities:
   - `text-sm text-[#6b7280] hover:text-[#111827]` → `content-header-back`
   - `px-3 py-1.5 rounded border border-[#e5e7eb]` → `pill-link`
   - Hardcoded `text-[#111827]` → `text-lo-text` or `text-[#111827]` shared variable
5. **Build & verify** — `npm run build` then check all routes render cleanly
6. **Deploy** — commit + push to trigger Vercel auto-deploy

### Pitfalls
- **⚠️ Do NOT use `@apply` with custom classes in Tailwind v4** — it fails at build time. Apply classes directly in HTML.
- **Compare CSS variables before changing** — reference page may already share the same palette
- **Hardcoded hex colours in JSX templates** need separate patches from CSS classes
- **JS-generated HTML** (calculator results, deal feeds) may hardcode colours in template literals
- **JS-generated HTML** (calculator results, deal feeds) may hardcode colours in JS template literals — patch those separately

### Reference: MC v4 → Clean White Color Mapping

| MC v4 Dark/Light Class | Clean White Equivalent |
|------------------------|----------------------|
| `text-lo-text` | `text-[#111827]` |
| `text-lo-text-muted` | `text-[#6b7280]` |
| `bg-lo-bg-alt` | `bg-[#f9fafb]` |
| `border-lo-border` | `border-[#e5e7eb]` |
| `bg-lo-primary` | `bg-[#6b21a8]` |
| `pixel-grid` / `card-lift` | Remove entirely |

## Deployment to LXC Container

Follow the `proxmox-host-creation` skill for the full deployment process.

### Quick deploy steps
1. Copy HTML to container: `pct push <VMID> /tmp/index.html /var/www/<site>/index.html`
2. If SSH is unavailable, use the two-step: curl from Hermes VM's Flask server → stage on Proxmox → pct push
3. Set up nginx with a basic `server { listen 80; root /var/www/<site>; }` block
4. Verify with `curl -s -o /dev/null -w "%{http_code}" http://<container-ip>/`

## Pitfalls

1. **Page size** — a full resource hub with 8 inline SVGs can be 55KB+. This is fine for nginx but worth noting if deploying via API-piped commands (base64 encoding adds 33% overhead).
2. **Telegram output truncation** — HTML files this large (900+ lines) will be TRUNCATED if sent via Telegram's message content. Always deploy to a URL and share the link instead.
3. **SVG gradient ID collisions** — each SVG `<defs>` section uses IDs like `g1`, `g2`. When embedding multiple SVGs per page, prefix each set (e.g., `hg1` for hero, `cg1` for checklist, `sg1` for shield, `fg1` for funding, `eg1` for EYFS, `ig1` for insurance, `cog1` for community, `plg1` for play illustration).
4. **Mobile: hide decorative SVGs** — use `@media (max-width: 720px) { .visual-side { display: none; } }` to keep the page fast on phones.
5. **Disclosure placement** — the affiliate disclosure MUST come before any shop or externally-linked content. In the UK, the ASA enforces this.
6. **Accordion z-index** — accordions use `max-height` transitions, not `height`. Set `max-height: 500px` — high enough for the content, but not so high the transition looks instant.
7. **Brave Search API is the primary research tool** — do not default to manual source listing. Run Brave queries for each UK topic. See `brave-web-search` skill for commands.
8. **UK energy suppliers mostly lack affiliate programs** — Only Octopus Energy has a straightforward referral. See `references/uk-energy-affiliate-landscape.md` for the full breakdown.

## Reference Files

- `references/uk-energy-affiliate-landscape.md` — UK energy supplier affiliate landscape: supplier referral programs, cashback publisher routes (£20-95 per switch), comparison site affiliate networks (£30-80 per switch via CJ/Awin/Impact), solar installer lead-gen model (Gary Does Solar), Axle Energy grid services (compatible brands, Powerwall limitations), and content strategy for an energy comparison site.
