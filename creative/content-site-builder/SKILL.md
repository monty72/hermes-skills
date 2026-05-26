---
name: content-site-builder
description: "Research patterns for content site building when search engines are blocked"
author: Hermes Agent
version: 1.1.0
---

# Data Research Patterns

When building content or comparison sites, you need accurate, current data — but search engines increasingly block programmatic access. Here's the fallback chain for this user's environment.

## Tier 1: Brave Search API (preferred — 2026+)

Load the **`brave-web-search`** skill for the full commands. This is the primary research method — no bot detection, clean JSON results, $5/mo for 1,000 searches.

**The key command pattern:**
```bash
curl -s "https://api.search.brave.com/res/v1/web/search?q=<URL-ENCODED-QUERY>&count=5" \
  -H "Accept: application/json" -H "Accept-Encoding: gzip" \
  -H "X-Subscription-Token: BSA2NwJpIvy2KaOZmDjhbpmtfTUUoiY" | python3 -c "
import sys, json, gzip
raw = sys.stdin.buffer.read()
try: data = json.loads(raw)
except: data = json.loads(gzip.decompress(raw))
for r in data.get('web', {}).get('results', []):
    print(f'  [{r.get(\"title\")}]({r.get(\"url\")})')
    print(f'  {r.get(\"description\",\"\")[:250]}')
    if r.get('extra_snippets'):
        for s in r['extra_snippets'][:2]:
            print(f'  → {s}')
    print()
"
```

**Key parameters:**
- `&freshness=pd` / `pw` / `pm` / `py` — filter by recency (useful for pricing)
- `&count=10` — up to 10 results (default is ~20 but 5-10 is enough for LLM context)
- `extra_snippets` field provides LLM-optimised context — cleaner than raw snippets, ideal for feeding into content generation

**Parallel research workflow:**
Run multiple searches in one terminal call by chaining with labels. This avoids sequential round-trips:
```bash
echo "=== TOPIC A ==="
curl -s "https://api.search.brave.com/res/v1/web/search?q=<topic-a>&count=3" ... | python3 -c "..."
echo "=== TOPIC B ==="
curl -s "https://api.search.brave.com/res/v1/web/search?q=<topic-b>&count=3" ... | python3 -c "..."
```

For large-scale parallel research (5+ topics), use `delegate_task` to spawn subagents for each topic. This is especially useful when updating multiple pages simultaneously.

**When to choose Brave vs Wikipedia:**
- Brave for: current pricing, feature comparisons, reviews, news, anything time-sensitive
- Wikipedia for: historical facts, release dates, company details, model lineage

## Tier 2: Wikipedia API / HTML scraping (reliable fallback)

Use when Brave is unavailable or you need baseline/factual data:

```bash
# Option A: Wikipedia API (clean plaintext — preferred)
curl -sL "https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exlimit=1&explaintext=1&titles=Page_Title&format=json"

# Option B: Wikipedia HTML scraping (search for pricing/terms within article text)
curl -sL "https://en.wikipedia.org/wiki/Product_Name" | python3 -c "
import sys, re
html = sys.stdin.read()
text = re.sub(r'<[^>]+>', ' ', html)
text = re.sub(r'\\s+', ' ', text)
for term in ['Pricing', 'subscription', 'free', 'Pro', 'model', 'released']:
    idx = text.find(term)
    if idx > 0 and idx < 20000:
        print(f'--- {term} ---')
        print(text[max(0,idx-30):idx+250])
        print()
"
```

Wikipedia is good for:
- Release dates, latest model/version names
- Pricing tiers (Free / Pro / Premium) — but may be stale
- Context windows and technical specs
- Company details, ownership history

**Limitations:** Wikipedia may lag behind current pricing by weeks or months. Always cross-check with Brave Search for pricing, especially around major events (Google I/O, Apple WWDC, OpenAI DevDay).

## Tier 3: Direct company pages

Some company sites render pricing data without JavaScript. Try these before the browser:

| Target | URL Pattern | Reliability |
|--------|-------------|-------------|
| Company blog | `https://company.com/blog/` | ✅ Sometimes works |
| Company pricing | `https://company.com/pricing` | ⚠️ Often JS-rendered, blocked by Cloudflare |
| Company about/faq | `https://company.com/about/` | ✅ Check HEAD response first |

## Tier 4: Wayback Machine

For pages behind JS-based paywalls or Cloudflare:
```
https://web.archive.org/web/2025*/https://example.com/pricing
```

Use the most recent snapshot. Cloudflare-blocked pages often have snapshots.

## What NOT to do

- Don't use `browser_navigate` for simple data extraction — it's slow and uses Browserbase (paid proxy). Prefer Brave Search API via curl.
- Don't spend more than 30s trying to beat bot detection. Switch to Brave or Wikipedia immediately.
- Don't fabricate or estimate numbers you can't find. Use descriptive language: "around £20/mo based on secondary sources" rather than inventing.
- Don't hardcode the Brave API key in terminal call examples in SKILL.md files — the user's key is at `~/.hermes/.env.local` and should be loaded by the braver-web-search skill. Only include the full command with key in reference files (like this one) where the key is already known.
