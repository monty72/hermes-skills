# Flask: RSS-scraping API Endpoint

Pattern for adding a live-deals or feed-based endpoint to an existing Flask/BaseHTTPRequestHandler server.

## Use Case

You have a Flask (or stdlib `BaseHTTPRequestHandler`) server running on localhost, exposed via Cloudflare Tunnel. You want to add an endpoint that scrapes an RSS feed, filters by keyword, and returns JSON — for a frontend page that shows live deals.

## Architecture

```
Browser JS → fetch('/api/homelab-deals') → Cloudflare → Tunnel → Flask → RSS fetch → JSON response
```

The endpoint runs **server-side** (avoiding CORS and bot-detection issues that plague browser-side RSS fetching).

## BaseHTTPRequestHandler Pattern

```python
from xml.etree import ElementTree
import urllib.request, html as html_mod

def fetch_homelab_deals():
    keywords = ["server", "mini pc", "nuc", "nas", "ssd", "hdd", "raspberry pi"]
    try:
        req = urllib.request.Request("https://www.hotukdeals.com/rss/hot",
            headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                     "Accept": "application/rss+xml"})
        rss = urllib.request.urlopen(req, timeout=15).read()
        root = ElementTree.fromstring(rss)
        ns = {"pepper": "http://www.pepper.com/rss"}
        deals = []
        for item in root.findall(".//item"):
            title = (item.findtext("title", "") or "").lower()
            desc = (item.findtext("description", "") or "").lower()
            if any(kw in (title + " " + desc) for kw in keywords):
                merch = item.find(".//pepper:merchant", ns)
                deals.append({
                    "title": html_mod.unescape(item.findtext("title", "") or "")[:120],
                    "price": merch.get("price", "") if merch is not None else "",
                    "merchant": merch.get("name", "") if merch is not None else "",
                    "link": item.findtext("link", ""),
                })
        return {"deals": deals, "count": len(deals)}
    except Exception as e:
        return {"deals": [], "error": str(e), "count": 0}
```

Then in the handler:

```python
elif path == "/api/homelab-deals":
    self.send_response(200)
    self.send_header("Content-Type", "application/json")
    self.send_header("Access-Control-Allow-Origin", "*")
    self.send_header("Cache-Control", "max-age=600")  # 10 min cache
    self.end_headers()
    deals = fetch_homelab_deals()
    self.wfile.write(json.dumps(deals).encode())
```

## Key Details

- **User-Agent is critical** — HotUKDeals blocks Python's default `urllib` UA. Use a realistic browser UA string.
- **Namespace prefix** — HotUKDeals RSS uses `pepper:` namespace for merchant info: `{http://www.pepper.com/rss}merchant`. Access via `item.find('.//pepper:merchant', ns_dict)`.
- **Cache-Control: max-age=600** — sets a 10-minute browser cache. The feed is poll-only (no write), so caching is safe.
- **Keyword filter** — the filter runs on lowercased title + description. Keep keywords lowercase and broad enough to catch different product names.
- **Error handling** — always wrap in `try/except` and return `{"deals": [], "error": str(e)}`. The RSS feed can 403 if the UA is blocked, or timeout.

## HotUKDeals RSS Feed Details

| Property | Value |
|----------|-------|
| Feed URL | `https://www.hotukdeals.com/rss/hot` |
| Max items | ~40 in hot feed |
| Update frequency | Every few minutes |
| Auth | None (public) |
| Rate limit | Unspoken but ~1 req/sec is safe |
| CORS | Blocks browser-side fetch — **must proxy through backend** |

## Frontend (Astro <script>)

```javascript
async function loadDeals() {
    const el = document.getElementById('deals-feed');
    try {
        const r = await fetch('/api/homelab-deals');
        const data = await r.json();
        if (data.deals?.length) {
            el.innerHTML = data.deals.map(d => `
                <a href="${d.link}" target="_blank" class="deal-card">
                    <div class="deal-title">${d.title}</div>
                    <div class="deal-price">${d.price ? '£' + d.price : ''}</div>
                    <div class="deal-merchant">${d.merchant}</div>
                </a>
            `).join('');
        }
    } catch {
        el.innerHTML = '<div>Feed unavailable. Try direct links.</div>';
    }
}
loadDeals();
```

## Pitfalls

1. **RSS feed 403** — if the UA gets blocked, update the User-Agent string to a current browser version. The `Accept` header for `application/rss+xml` also helps.
2. **Empty merchant name** — not every RSS item has a `<pepper:merchant>` element. Handle `None` gracefully.
3. **No price** — some deals have no `price` attribute on the merchant element. Default to empty string.
4. **Flask server restart** — after adding the endpoint, kill the old process and restart with `PORT=8000` env var (the server may use env var, not CLI args).
5. **`html.unescape()` needed** — RSS titles contain HTML entities (`&amp;`, `&pound;`). Decode before returning.
