# SVG Illustration Patterns for Content Sites

## Palette

Use the same CSS custom properties as the dark theme:

| Role | CSS Variable | Practical RGBA |
|------|-------------|----------------|
| Primary accent | `--accent` (6c8cff) | `rgba(108,140,255, X)` |
| Green accent | `--green` (34d399) | `rgba(52,211,153, X)` |
| Amber accent | `--amber` (fbbf24) | `rgba(251,191,36, X)` |
| Red accent | `--red` (f87171) | `rgba(248,113,113, X)` |
| Purple accent | `--purple` (a78bfa) | `rgba(167,139,250, X)` |
| Cyan accent | `--cyan` (22d3ee) | `rgba(34,211,238, X)` |

## ViewBox sizes

- **Landscape (hero)**: `800 500` — wide enough for 2-3 figures side by side
- **Portrait (sections)**: `400 300` — compact, fits in a card or alongside text
- **Square**: `400 400` — use sparingly, when the illustration needs equal dimensions

## Defs to include in every SVG

```svg
<defs>
  <linearGradient id="g1" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#6c8cff"/><stop offset="100%" stop-color="#a78bfa"/>
  </linearGradient>
  <linearGradient id="g2" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#34d399"/><stop offset="100%" stop-color="#22d3ee"/>
  </linearGradient>
  <filter id="glow">
    <feGaussianBlur stdDeviation="2" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>
```

Use `g1` for primary-accent figures, `g2` for secondary/green figures.

## Illustration taxonomies by section type

| Section Subject | Visual Metaphor |
|----------------|-----------------|
| Getting Started / Registration | Clipboard with checklist, progress ticks |
| Training / Education | Bookshelf, open book, graduation cap |
| Funding / Finance | Coin pile, coin stack, pound sign, wallet |
| Safeguarding / Safety | Shield, badge, lock, checkmark |
| Community / People | Connected circles/people, network dots, hearts |
| Health / First Aid | Cross, bandage, heart |
| Children at play | Blocks, toys, running figures, crawling baby |
| Childminder / Carer | Adult with open arms, children running towards |
| Regulations / Framework | Document, official seal, certificate |
| Resources / Tools | Toolbox, folder, documents, links |

## Composition rules

1. **Background circle**: always start with `<circle cx="200" cy="150" r="120" stroke="..." stroke-width="1" fill="none"/>` to frame the illustration
2. **Opacity layers**: background elements 0.04–0.08, mid-ground 0.1–0.3, foreground 0.4–0.9
3. **Text labels**: `font-size="8-10"`, `font-family="sans-serif"`, `text-anchor="middle"`
4. **Figures**: use ellipses for bodies (`rx`, `ry`), circles for heads, paths for limbs
5. **Decorative elements**: stars (✦), hearts (♥), dots, floating shapes — always low opacity (0.15–0.3)
6. **Glow filter**: apply to stars and hearts only, not main figures
7. **No white fills**: everything should inherit from the palette — no `#ffffff` or pure white
8. **Unique gradient IDs**: When inlining multiple SVGs on one page, scope gradient IDs per SVG (e.g. `hg1`, `cg1`, `sg1`, `fg1`, `eg1`, `ig1`, `cog1`, `plg1`). Never reuse bare `g1`, `g2` across multiple inline SVGs — the second instance overrides the first in SVG rendering.

## Example: shield + badges (safeguarding)

```svg
<circle cx="200" cy="150" r="120" stroke="rgba(108,140,255,0.04)" stroke-width="1" fill="none"/>
<path d="M200 70 L260 95 L260 155 C260 210 200 240 200 240 C200 240 140 210 140 155 L140 95 Z"
  fill="rgba(108,140,255,0.06)" stroke="rgba(108,140,255,0.15)" stroke-width="1.5"/>
<path d="M180 160 L195 175 L225 145" stroke="#34d399" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="160" cy="110" r="16" fill="rgba(52,211,153,0.1)" stroke="rgba(52,211,153,0.2)" stroke-width="1"/>
<text x="160" y="114" text-anchor="middle" font-size="8" fill="#34d399" font-family="sans-serif" font-weight="600">DBS</text>
```

## Example: clipboard + checklist (registration)

```svg
<rect x="140" y="80" width="120" height="160" rx="8" fill="rgba(108,140,255,0.08)" stroke="rgba(108,140,255,0.15)" stroke-width="1.5"/>
<rect x="170" y="70" width="60" height="20" rx="4" fill="rgba(108,140,255,0.12)" stroke="rgba(108,140,255,0.2)" stroke-width="1"/>
<!-- Checkbox items: rect + text -->
<rect x="160" y="110" width="14" height="14" rx="2" .../>
<text x="182" y="123" font-size="10" fill="#8a8aa5">Item</text>
<!-- Tick -->
<path d="M163 117 L167 121 L173 114" stroke="#34d399" stroke-width="1.5" fill="none" stroke-linecap="round"/>
```

## Example: people figures

- **Adult**: ellipse(rx=35, ry=40), circle(r=25), arms as wide-open paths
- **Child standing**: ellipse(rx=25, ry=30), circle(r=20)
- **Child sitting**: ellipse(rx=28, ry=32), circle(r=22), legs as paths reaching down, arms reaching to toys
- **Child crawling**: small ellipse(rx=15, ry=18), circle(r=12), arms reaching forward
- **Motion lines** for running figures: short diagonal lines ahead of the figure
- **Hearts** floating between figures: `fill="rgba(248,113,113, 0.2-0.3)"`

## File naming

- `topic-illustration.svg` — e.g. `childminder-illustration.svg`, `funding-illustration.svg`
- `topic-descriptive.svg` — e.g. `registration-checklist.svg`, `safeguarding-shield.svg`
- All lowercase, hyphens, placed in `images/` subdirectory next to the HTML

## Image embedding in HTML

Three patterns — prefer **inline embedding** for single-file pages.

### Pattern A: Inline embedding (PREFERRED for single-file pages)

Inline SVGs load immediately (no extra HTTP request) and never 404. Keep the page fully self-contained.

**Hero section:**
```html
<div class="hero-image">
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500" fill="none" style="max-height:220px">
    <!-- SVG defs and content here -->
  </svg>
</div>
```

**Content section (side-by-side with cards):**
```html
<div class="visual-side">
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" fill="none">
    <!-- content -->
  </svg>
</div>
```

**Full-width section divider illustration** (between sections, e.g. before FAQ):
```html
<div style="text-align:center;margin-bottom:32px;opacity:0.6">
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 300" fill="none" style="max-height:180px" preserveAspectRatio="xMidYMid meet">
    <!-- children playing, decorative scene - subtle, low opacity figures -->
    <ellipse cx="400" cy="250" rx="350" ry="20" fill="rgba(108,140,255,0.03)"/>
    <!-- 2-3 small figure groups at x=200, x=400, x=580, all opacity 0.25-0.35 -->
    <text x="300" y="100" font-size="10" fill="rgba(248,113,113,0.15)">♥</text>
  </svg>
</div>
```
Use this for a soft visual break between major content sections. Keep figures at 60-70% scale compared to hero illustrations, and opacity at 0.25-0.35 so it doesn't compete with section content. Mobile-safe (just subtle centering, no layout impact).

**IMPORTANT:** When inlining multiple SVGs in one page, give each `<defs>` section **unique IDs** to avoid collision (e.g. `g1` → `hg1`, `cg1`, `sg1`, `fg1`, `eg1`, `ig1`, `cog1`, `plg1`). Gradient IDs must be unique per SVG instance.

### Pattern B: `<img>` tag (multi-file deployments only)

```html
<img src="images/hero-illustration.svg" alt="Children playing with toys" style="max-width:100%; border-radius:var(--radius);">
```
