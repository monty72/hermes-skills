# Curated Product Guide / Hardware Guide

Pattern for building an Astro content page with curated product recommendations, price estimates, section-based category breakdown, UK retailer shopping tips, and a live deals feed.

## Structure

```
Header → Title + subtitle
[Info box] → Disclaimer / approach note
[Category sections] → Each with:
  - Section title + emoji
  - Grid of product cards (3 columns)
  - Each card: title, spec lines, price, retailer tag
[Shopping Tips] → UK-specific advice grid
[Live Deals Feed] → Fetches from Flask backend API
[Footer] → Disclaimer
```

## Astro Page Pattern

```astro
---
import Layout from '../layouts/Layout.astro';
---
<Layout title="Guide Title — Site">
  <main class="dark-gradient-bg">
    <header>← Back · title · subtitle</header>

    <div class="info-box">🔧 Context / disclaimer</div>

    <!-- Each category as a <section> -->
    <section class="mb-10">
      <h2>📦 Category Name</h2>
      <p class="intro">One-line description of category.</p>
      <div class="grid md:grid-cols-3 gap-4">
        {items.map(item => (
          <div class="product-card">
            <div class="card-header">
              <h3 class="product-name accent-color">{item.name}</h3>
              <span class="badge">{item.tag}</span>
            </div>
            <div class="specs">{item.specs}</div>
            <div class="power">🔌 {item.power}</div>
            <div class="card-footer">
              <span class="price">~£{item.price}</span>
              <span class="retailer">{item.retailer}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  </main>
</Layout>
```

## Card CSS Pattern

```css
/* Product cards — dark theme, hover glow */
.product-card {
  padding: 1.25rem;
  border-radius: var(--radius);
  background: var(--card, rgba(255,255,255,0.05));
  border: 1px solid var(--border, rgba(255,255,255,0.1));
  transition: all 0.2s;
}
.product-card:hover {
  border-color: color-mix(in srgb, var(--accent) 30%, transparent);
  background: var(--card-hover, rgba(255,255,255,0.1));
}

/* Responsive grid: auto-fill with min 260px */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}
```

Use Tailwind classes in Astro:
- Card: `p-5 rounded-xl bg-white/5 border border-white/10 hover:border-green-400/30 transition-all`
- Price: `text-lg font-bold text-white`
- Retailer tag: `text-xs text-slate-500`
- Badge: `px-2 py-0.5 rounded text-xs bg-green-500/20 text-green-400`

## Pricing Presentation

Show prices with the tilde prefix for estimated prices:
```
~£120
```

For price ranges (or to indicate "from"):
```
~£280-£350
```

Always include a **retailer source tag** underneath the price so users know where to look.

## Shopping Tips Section

A two-column grid of tips, each a small card with a title + short paragraph. Use a gradient banner background to distinguish from product cards:

```html
<section class="p-6 rounded-xl bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border border-blue-500/20 mb-10">
  <h2 class="text-lg font-semibold mb-4 text-cyan-300">💡 UK Shopping Tips</h2>
  <div class="grid md:grid-cols-2 gap-4">
    <div class="p-3 rounded-lg bg-white/5">
      <h3 class="font-semibold text-cyan-400">eBay Refurb</h3>
      <p class="text-xs text-slate-400">Best source for Mini PCs...</p>
    </div>
    <div class="p-3 rounded-lg bg-white/5">
      <h3 class="font-semibold text-cyan-400">Scan Computers</h3>
      <p class="text-xs text-slate-400">UK-based, great for new components...</p>
    </div>
  </div>
</section>
```

## Live Deals Feed

Add a section at the bottom that fetches from a Flask backend API endpoint (see `watchers` skill → `references/flask-rss-endpoint.md`):

```astro
<section class="p-6 rounded-xl bg-white/5 border border-white/10 mb-6">
  <h2 class="text-lg font-semibold mb-4">📡 Live Deals Feed</h2>
  <div id="deals-feed">
    <div class="animate-pulse text-slate-500 text-sm">Loading deals...</div>
  </div>
</section>

<script>
  async function loadDeals() {
    const el = document.getElementById('deals-feed');
    try {
      const r = await fetch('/api/homelab-deals');
      const data = await r.json();
      if (data.deals?.length) {
        el.innerHTML = data.deals.map(d => `
          <a href="${d.link}" target="_blank" class="block p-3 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-all mb-2">
            <div class="text-sm font-medium">${d.title}</div>
            <div class="flex justify-between text-xs text-slate-500">
              <span>${d.merchant}</span>
              <span class="text-green-400 font-bold">${d.price}</span>
            </div>
          </a>
        `).join('');
      }
    } catch {
      el.innerHTML = '<div class="text-slate-500 text-sm p-4 text-center">Feed unavailable. Check back later.</div>';
    }
  }
  loadDeals();
</script>
```

## UK Retailer Reference

| Retailer | Best For | URL Pattern |
|----------|----------|-------------|
| eBay UK | Used/refurb Mini PCs, servers | `ebay.co.uk/sch/i.html?_nkw=SEARCH&_sop=10` |
| Scan | New components, NAS, networking | `scan.co.uk` |
| Amazon | Everything, fast delivery | `amazon.co.uk` |
| Broadband Buyer | MikroTik, Ubiquiti networking | `broadbandbuyer.com` |
| PiHut | Raspberry Pi, SBC accessories | `thepihut.com` |
| AliExpress | Orange Pi, cheap SBCs, cables | `aliexpress.com` |

## Software/Service Comparison Pages (Template)

For comparison pages comparing software products, SaaS tools, or AI services (not hardware), use this template pattern:

```astro
---
import Layout from '../layouts/Layout.astro';

// Define comparison data as a JS array of product objects
const products = [
  {
    id: 'product-a',
    name: 'Product A',
    company: 'Company Name',
    logo: '🟢',
    color: 'emerald',
    latest: 'Model v2.0',
    released: 'Jan 2023',
    pricing: {
      free: '✅ Limited access',
      plus: '$20/mo — Full access',
      pro: '$200/mo — Unlimited',
    },
    context: '128K tokens',
    strengths: ['Strength 1', 'Strength 2', 'Strength 3'],
    weaknesses: ['Weakness 1', 'Weakness 2'],
    verdict: 9.2, // /10
    bestFor: 'Primary use case description',
    description: '2-3 paragraph honest writeup...',
  },
  // ... more products
];

// Utility functions
function getScoreBar(score: number) {
  const full = Math.floor(score);
  const half = score % 1 >= 0.5 ? 1 : 0;
  const empty = 10 - full - half;
  return '★'.repeat(full) + (half ? '½' : '') + '☆'.repeat(empty);
}
---
```

### Page structure (in order)

1. **Header** — title, subtitle (e.g. "Honest, hands-on comparison of 6 major chatbots — pricing, strengths, weaknesses, verdicts")
2. **Top Picks Grid** — a 3-column grid of quick-pick cards (best all-round, best for research, best free tier, etc.). Each card: emoji, title, product name, one-line reason.
3. **Feature Comparison Table** — scrollable `<table>` with sticky header. Columns: Feature | ProductA | ProductB | ProductC | ... Rows should cover: models, pricing, context window, voice/image/code/search features, file upload, open source, mobile app, API availability.
4. **Pricing Quick View** — 3-column grid showing Free Tier / Standard Paid / Power User row across all products.
5. **In-Depth Reviews** — one card per product, each containing:
   - Logo + name + company + latest model
   - Score badge (★9.2/10)
   - 2-3 paragraph honest description
   - Strengths list (green) + Weaknesses list (red) side by side
   - "Best For" highlight box
   - Collapsible pricing details `<details>` element
6. **Final Verdict Section** — gradient banner with decision guide: "Pick this one if..."

### CSS colour per product

Define a `colorClasses` function mapping color names to Tailwind classes:

```ts
function getColorClasses(color: string) {
  const map: Record<string, string> = {
    emerald: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
    violet: 'bg-violet-500/20 text-violet-300 border-violet-500/30',
    blue: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    red: 'bg-red-500/20 text-red-300 border-red-500/30',
    slate: 'bg-slate-500/20 text-slate-300 border-slate-500/30',
    amber: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  };
  return map[color] || map.blue;
}
```

### Data research pattern (when search engines are blocked)

When Google/DuckDuckGo/Brave block requests, use Wikipedia as the primary data source:

```bash
# Fetch Wikipedia article, strip HTML, search for key terms
curl -sL "https://en.wikipedia.org/wiki/Product_Name" | python3 -c "
import sys, re
html = sys.stdin.read()
text = re.sub(r'<[^>]+>', ' ', html)
text = re.sub(r'\s+', ' ', text)
for term in ['Pricing', 'subscription', 'free', 'Pro', 'model', 'released']:
    idx = text.find(term)
    if idx > 0:
        print(f'--- {term} ---')
        print(text[max(0,idx-30):idx+250])
        print()
"
```

For a group of products, parallelise with multiple `curl` calls in a single terminal call or an `execute_code` block.

Pricing info on Wikipedia is usually up to date for major products. Supplement with:
- The product's own FAQ/pricing page (if it renders without JS)
- Archived review articles (Wayback Machine)
- Community wikis and subreddits

### Pitfalls

1. **Static prices go stale** — mark all non-live prices with "~" prefix and note the date in the footer. The page is static until a cron job updates it.
2. **Live feed fails gracefully** — the deals feed tries the API endpoint first, then falls back to a "Feed unavailable" message with direct search links.
3. **Category balance** — aim for 3 items per category. 2 looks thin, 4+ overwhelms. Use a sub-grid if you need more.
4. **Mobile responsive** — 3-column grid collapses to 1 column on mobile. Test with `@media (max-width: 640px)` or Tailwind's responsive classes.
5. **No opinions = no trust** — guides without opinions (just specs and prices) feel like an Amazon listing. Add a "Why this" one-liner per card.
