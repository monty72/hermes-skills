# Astro Dashboards with Server-Side Data Fetching

This reference documents the pattern for building data-rich Astro pages that fetch from external APIs at build time (SSR/static generation). Used for: Octopus Agile tariff tracker, energy dashboard, mission control.

## Architecture

```
Astro build time (server-side fetch)
  ├── Octopus Energy API (public, no auth)
  ├── Local Flask API (localhost:8000 - Tesla/System data)
  └── node:os (system metrics)

output: static HTML with live data embedded

Client side (optional):
  └── fetch('/api/...') for live updates via <script>
```

## Pattern: Server-Side Data in Frontmatter

```astro
---
import Layout from '../layouts/Layout.astro';

// 1. Fetch in frontmatter — runs at build time
const OCTOPUS_PRODUCT = 'AGILE-24-10-01';
const TARIFF_CODE = 'E-1R-AGILE-24-10-01-E';

let rates = [];
try {
  const now = new Date().toISOString().slice(0,16) + 'Z';
  const url = `https://api.octopus.energy/v1/products/${OCTOPUS_PRODUCT}/electricity-tariffs/${TARIFF_CODE}/standard-unit-rates/?period_from=${now}`;
  const res = await fetch(url);
  const data = await res.json();
  rates = (data.results || []).slice(0, 48);
} catch (e) {
  // Graceful fallback — page renders with placeholder data
}
---

<Layout title="Title">
  <main>
    {rates.length > 0 ? (
      rates.map(r => (
        <div>{/* render with data */}</div>
      ))
    ) : (
      <div>Data unavailable</div>
    )}
  </main>
</Layout>
```

## Pattern: Local API Fetch (Flask backend)

For data exposed on a local server (e.g. Tesla API proxy, system status):

```astro
---
let energyData = { battery: '—', solar: '—', home: '—' };
try {
  const res = await fetch('http://localhost:8000/api/energy');
  if (res.ok) energyData = await res.json();
} catch {}
---
```

## Pattern: Client-Side Refresh

For dashboards that need live-updating data, add an inline `<script>`:

```astro
<script>
  async function refresh() {
    try {
      const r = await fetch('/api/energy');
      const d = await r.json();
      document.getElementById('battery').textContent = d.battery;
    } catch {}
  }
  refresh();
  setInterval(refresh, 30000);
</script>
```

## Octopus Agile API Details

| Aspect | Detail |
|--------|--------|
| API base | `https://api.octopus.energy/v1/products/` |
| Current product | `AGILE-24-10-01` |
| Tariff format | `E-1R-{product}-{region}` |
| Region codes | `_A` through `_P` (East Midlands = `E`) |
| Full tariff | `E-1R-AGILE-24-10-01-E` |
| Rate param | `?period_from={ISO timestamp}` |
| Response | `{results: [{valid_from, valid_to, value_inc_vat}]}` — returns 100 entries by default |
| Auth | None — public API |
| Rate limit | Unknown, but generous (returns 100 rates per call) |

### Finding the right product code

```bash
# List all products
curl -s "https://api.octopus.energy/v1/products/" | jq '.results[].code'

# Get product details (includes tariff codes)
curl -s "https://api.octopus.energy/v1/products/AGILE-24-10-01/"

# The tariff suffixes (_E, _F, etc.) are in:
# product.single_register_electricity_tariffs
```

### Rendering half-hourly rates

A common pattern is rendering colour-coded rate bars. The rate range is typically 5p–50p (can spike to 70p+ in winter):

```astro
<div class="flex items-center gap-3 p-2 rounded-lg bg-white/5 border border-white/10">
  <span class="w-20 text-sm text-slate-400 font-mono">{timeFrom} – {timeTo}</span>
  <div class="flex-1 h-5 rounded-full bg-slate-800 overflow-hidden">
    <div class="h-full rounded-full opacity-70"
      style={`width: ${Math.min(((rate - 5) / 50) * 100, 100)}%`}
      class={rate < 10 ? 'bg-green-500' : rate < 20 ? 'bg-cyan-500' : rate < 30 ? 'bg-yellow-500' : rate < 50 ? 'bg-orange-500' : 'bg-red-500'}>
    </div>
  </div>
  <span class="w-16 text-right font-mono text-sm font-bold">{rate.toFixed(1)}p</span>
</div>
```

### Finding cheapest charging windows

Common use case: find the cheapest 3 consecutive half-hour slots for EV charging:

```astro
---
let bestIdx = 0;
let bestAvg = Infinity;
for (let i = 0; i < rates.length - 2; i++) {
  const avg = (rates[i].value_inc_vat + rates[i+1].value_inc_vat + rates[i+2].value_inc_vat) / 3;
  if (avg < bestAvg) { bestAvg = avg; bestIdx = i; }
}
const best = rates.slice(bestIdx, bestIdx + 3);
---
<p>Best: {best[0].valid_from.slice(11,16)} – {best[2].valid_to.slice(11,16)} · avg {bestAvg.toFixed(1)}p</p>
```
