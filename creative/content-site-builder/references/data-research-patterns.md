# Data Research Patterns

When building content or comparison sites, you need accurate, current data — but search engines increasingly block programmatic access. Here's the fallback chain.

## Tier 1: API-based (preferred)

When available, use documented APIs over scraping:

| Source | URL Pattern | Notes |
|--------|-------------|-------|
| Wikipedia API | `https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exlimit=1&explaintext=1&titles=Page_Title&format=json` | Returns clean plaintext, no HTML stripping needed. Use `explaintext=1`. |
| OpenLibrary | `https://openlibrary.org/search.json?q=...` | Public API, no auth. |

## Tier 2: Wikipedia HTML scraping (reliable fallback)

When search engines are blocked but Wikipedia is accessible:

```bash
# Fetch a Wikipedia article and extract text by searching for key terms
curl -sL "https://en.wikipedia.org/wiki/Product_Name" | python3 -c "
import sys, re
html = sys.stdin.read()
text = re.sub(r'<[^>]+>', ' ', html)
text = re.sub(r'\s+', ' ', text)
for term in ['Pricing', 'subscription', 'free', 'Pro', 'model', 'released', 'Plus']:
    idx = text.find(term)
    if idx > 0 and idx < 20000:
        print(f'--- {term} ---')
        print(text[max(0,idx-30):idx+250])
        print()
"
```

For multiple products, run parallel calls in one terminal command or use `execute_code` with `from hermes_tools import terminal`.

Wikipedia is particularly good for:
- Release dates
- Latest model/version names
- Pricing tiers (Free / Pro / Premium)
- Context windows and technical specs
- Ownership/company details

## Tier 3: Direct company pages

Some company sites render pricing data without JavaScript:

| Target | URL | Works? |
|--------|-----|--------|
| Wikipedia | `https://en.wikipedia.org/wiki/*` | ✅ Always |
| Company about/FAQ | Check HEAD response first | ✅ Sometimes |
| Company blog/release notes | `https://company.com/blog/` | ✅ Sometimes |

## Tier 4: Wayback Machine

For pages that are behind JS-based paywalls:

```
https://web.archive.org/web/2025*/https://example.com/pricing
```

Use the most recent snapshot.

## What NOT to do

- Don't use `browser_navigate` for simple data extraction — it's slow and uses a paid proxy. Prefer `curl`.
- Don't spend more than 30s trying to beat bot detection. Switch to Wikipedia or Wayback Machine.
- Don't fabricate or estimate numbers you can't find. Use qualifiers: "around £20/mo" based on secondary sources rather than inventing.
