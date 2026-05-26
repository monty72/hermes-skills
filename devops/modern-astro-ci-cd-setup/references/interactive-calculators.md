# Interactive Calculators in Astro

Reference pattern for building client-side calculators/ROI tools as Astro pages. Used for: Solar & Battery ROI Calculator.

## Architecture

```
Astro frontmatter (build time)
  ├── Static lookup tables (region data, monthly distribution, costs)
  └── Static HTML form markup

Client-side <script> (browser)
  ├── User fills form → hits "Calculate"
  ├── JS reads form values, computes results
  └── Renders results into a hidden <div id="results">
```

No API calls needed — all computation is client-side JS. The server renders the form and static data tables; the browser runs the calculation.

## Pattern: Form + Results

```astro
---
// Build-time data as JS literals
const DATA_MAP = {
  'region-a': { name: 'Region A', value: 1000 },
  'region-b': { name: 'Region B', value: 2000 },
};
const COST_PER_UNIT = 1600;
const NATIONAL_AVG_RATE = 24.5;
---

<Layout title="Calculator">
  <main class="dark-theme">
    <form id="calc-form" onsubmit="event.preventDefault(); calculate();">
      <select id="region">
        {Object.entries(DATA_MAP).map(([key, r]) => (
          <option value={key}>{r.name} — {r.value}</option>
        ))}
      </select>
      <input type="range" id="system-size" min="1" max="10" value="4" />
      <button type="submit">Calculate</button>
    </form>

    <div id="results" class="hidden">
      <div id="results-content"></div>
    </div>
  </main>
</Layout>

<script>
  // Client-side computation
  function calculate() {
    const region = document.getElementById('region').value;
    const size = parseInt(document.getElementById('system-size').value);
    // ... compute
    document.getElementById('results').classList.remove('hidden');
    document.getElementById('results-content').innerHTML = `
      <div>Result: £${savings}</div>
    `;
  }
</script>
```

## Key Patterns

### 1. Pre-compute server data in frontmatter, use in client `<script>`

```astro
---
const monthlyPct = [3.5, 5, 8, 11, 13, 14, 14, 12, 9, 6, 3.5, 2];
const monthNames = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
---

<script>
  // These values are available as globals because they were rendered
  // into the page HTML during build
  function calculate() {
    // Use data from frontmatter scope (above)
  }
</script>
```

NOTE: Server-side `const` values in frontmatter are NOT automatically available in the `<script>` block. You must either:
- **Duplicate** the data as a `<script>`-scoped `const` (the Solar page approach — cleaner, since the data is inlined)
- **Render** data into the page HTML via hidden elements or `data-` attributes
- **Use Astro's `define:vars`** directive

### 2. Client-side only rendering (hidden results div)

The results div starts hidden (`class="hidden"` / `display: none`) and is revealed when the user clicks Calculate. The results content is set via `innerHTML`:

```js
document.getElementById('results').classList.remove('hidden');
document.getElementById('results-content').innerHTML = `
  <div class="grid grid-cols-2 gap-3">
    <div>Stat 1: ${value1}</div>
    <div>Stat 2: ${value2}</div>
  </div>
`;
```

### 3. Colour-coded results

Use ternary expressions on the value to assign classes or inline styles:

```js
const color = paybackYears < 8 ? '#4ade80' : paybackYears < 12 ? '#facc15' : '#f87171';
html += `<div style="color: ${color}">${paybackYears} years</div>`;
```

### 4. Bar chart with flexbox

For simple bar charts (monthly generation, rate comparison), use flex children with percentage heights:

```html
<div class="flex items-end gap-1.5 h-32">
  ${values.map(v => `
    <div class="flex-1 flex flex-col items-center">
      <div class="bg-yellow-400 rounded-t w-full" style="height:${(v / maxVal) * 100}%"></div>
      <span class="text-[10px]">Label</span>
    </div>
  `).join('')}
</div>
```

No charting library needed — pure CSS flexbox bars for pages with < 12 data points.

### 5. Form defaults from real-world data

Pre-select the option that matches your actual setup (e.g., Powerwall 3 × 2, East Midlands) so the calculator shows realistic defaults on first load:

```html
<select id="battery">
  <option value="27" selected>Powerwall 3 × 2 (27 kWh) — our setup</option>
</select>
```

## Common Pitfalls

1. **`innerHTML` vs DOM manipulation** — `innerHTML` is fine for result pages where the content is entirely replaced on each Calculate. Don't use it for interactive widgets that need incremental updates.
2. **`hidden` class visibility** — make sure `.hidden { display: none !important; }` or use Tailwind's `hidden` utility. The results div must not take layout space before the calculation.
3. **Server data duplication** — data defined in frontmatter (`---` block) is NOT accessible in the `<script>` tag. Define data BOTH in frontmatter (for server rendering) AND in the `<script>` (for client computation), or use `data-` attributes on the form.
4. **Form values are strings** — always `parseInt()` or `parseFloat()` before arithmetic.
5. **Number formatting** — use `.toLocaleString()` for readability: `(12000).toLocaleString()` → "12,000".
6. **No API calls on submit** — the calculator should work entirely client-side. If you need live rates, fetch them on page load from a `<script>` that runs `fetch()`, not from a submit handler.
