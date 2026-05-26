---
name: brave-web-search
title: Brave Web Search
description: Search the web via the Brave Search API. No browser needed, no bot detection. Use for content research, fact-checking, and finding current information.
related_skills: [content-site-builder]
---

Use this skill when you need to find current information, verify facts, research topics, or discover content that's beyond your training data cutoff.

**Key consumer skills:** `content-site-builder` (research phase for comparison/content pages), `uk-resource-hub-builder` (UK-focused site research).

## Setup

The API key is stored at `~/.hermes/.env.local`:
```
BRAVE_SEARCH_API_KEY=BSA2NwJpIvy2KaOZmDjhbpmtfTUUoiY
```

## Usage

### Web Search
```bash
curl -s "https://api.search.brave.com/res/v1/web/search?q=<URL-ENCODED-QUERY>&count=10" \
  -H "Accept: application/json" \
  -H "Accept-Encoding: gzip" \
  -H "X-Subscription-Token: BSA2NwJpIvy2KaOZmDjhbpmtfTUUoiY" | python3 -c "
import sys, json, gzip
raw = sys.stdin.buffer.read()
try:
    data = json.loads(raw)
except:
    data = json.loads(gzip.decompress(raw))
for r in data.get('web', {}).get('results', []):
    print(f'TITLE: {r.get(\"title\")}')
    print(f'URL: {r.get(\"url\")}')
    print(f'DESC: {r.get(\"description\",\"\")[:200]}')
    if r.get('extra_snippets'):
        for s in r['extra_snippets'][:3]:
            print(f'AI: {s}')
    print()
"
```

### News Search
```bash
curl -s "https://api.search.brave.com/res/v1/news/search?q=<URL-ENCODED-QUERY>&count=5" \
  -H "Accept: application/json" \
  -H "X-Subscription-Token: BSA2NwJpIvy2KaOZmDjhbpmtfTUUoiY"
```

### LLM Context (optimised for AI consumption)
The `extra_snippets` field in web results returns text optimised for LLM context — cleaner than raw snippets, ideal for passing to an AI model for content generation.

## Parallel Research Patterns

For updating multiple pages with fresh data, run parallel searches:

**Single terminal call — multiple topics:**
```bash
echo \"=== TOPIC 1 ===\" && curl ... && echo \"=== TOPIC 2 ===\" && curl ...
```

**Large-scale: delegate_task subagents** — for 5+ topics, spawn subagents that each research one topic and return structured summaries. The parent then combines all research into page updates.

## Pitfalls
- URL-encode query parameters (`curl --data-urlencode` or Python's `urllib.parse.quote`)
- Use gzip decompression (the API returns gzipped responses)
- Rate limit: 50 requests/second — don't need to throttle for normal use
- Free credits: $5/mo = 1,000 searches/month (~33/day)
- The `freshness` parameter can filter by time: `&freshness=pd` (past day), `&freshness=pw` (past week), `&freshness=pm` (past month), `&freshness=py` (past year)
- For Reddit results, results have HTML entities — use Python's `html.unescape()` if needed
- Wikipedia-only pages may return no Brave results — fall back to direct Wikipedia API

## Fallback
If Brave Search fails or returns no results, try:
1. Wikipedia via `curl -sL "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=<QUERY>&format=json"`
2. Direct HTTP to known documentation sites
3. The Hermes browser tool (last resort — has bot detection issues, expensive)
