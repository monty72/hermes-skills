---
name: uk-retail-research
description: "Research product pricing, availability, and stock levels at UK retailers — Amazon, John Lewis, Currys, Argos, AO.com. Covers browser automation workarounds, Cloudflare detection patterns, and when to hand off to the user."
version: 1.0.0
---

# UK Retail Research

## Overview

Researching product prices and availability at UK retailers from within an agent session. Most major UK retailers aggressively block automated browser access with Cloudflare, Akamai, and similar bot detection.

## Known Blocked Retailers

These retailers consistently block browser automation:

| Retailer | Block Pattern | Workaround |
|----------|--------------|------------|
| **John Lewis** | ERR_HTTP2_PROTOCOL_ERROR or 403 | Cannot scrape. Tell user to visit site directly. |
| **Currys** | Cloudflare "Just a moment..." | Cannot bypass. Tell user to visit site directly. |
| **AO.com** | Cloudflare challenge | Cannot bypass. Tell user to visit site directly. |
| **Argos** | "Access Denied" | Cannot bypass. Tell user to visit site directly. |
| **Google Shopping** | CAPTCHA page | Cannot bypass. Try Bing/DuckDuckGo or Amazon only. |

## Amazon UK (Partially Works)

Amazon.co.uk **does work** with the browser tool, but with caveats:

1. **Cookie banner** — must click "Accept" (ref=e19 on first load) before results render
2. **Results are in the DOM** — use `browser_console` with JS queries to extract structured data, not `browser_snapshot` (too verbose)
3. **Amazon's own search bar** — start with a clean URL like `https://www.amazon.co.uk/s?k=PRODUCT+NAME&s=price-asc-rank` and sort by price ascending so the first result is the cheapest
4. **Use the product category param** — `&i=kitchen` for kitchen, `&i=electronics` for electronics, etc.

### Amazon Extraction Pattern

```javascript
// After accepting cookies and waiting for results:
Array.from(document.querySelectorAll('[data-component-type="s-search-result"]'))
  .map(el => {
    const title = el.querySelector('h2 a')?.textContent?.trim() || 'n/a';
    const price = el.querySelector('.a-price')?.textContent?.trim().replace(/\s+/g,' ') || 'n/a';
    const link = el.querySelector('h2 a')?.href || '';
    return `${title} | ${price} | ${link}`;
  })
  .join('\n')
```

Some results will show "no title" if the product card is for accessories, not the main product. Look for the full product name in results — it's usually the first or second listing when sorted by price ascending.

### Amazon Results Are Noisy

Search results include:
- The actual product (usually marked by "Sponsored" or full brand name)
- Accessories, replacement parts, and third-party accessories for the product
- Completely unrelated items that matched loosely

Manually filter by looking for the **exact brand + model** in the title string.

## When to Hand Off to the User

**Do NOT keep trying blocked sites.** Two failed attempts at a retailer means:
1. Tell the user the site blocks automation
2. Provide the direct search URL they can open manually: `https://www.johnlewis.com/search?q=PRODUCT+NAME`
3. Include known RRP info so they know whether the online price is fair

Example:
> "John Lewis blocks my browser. Search **John Lewis 'GE Profile Opal 2.0'** on your phone — it's usually £449."

## Pitfalls

- **Multiple tunnel processes** — if you kill and restart localhost.run tunnels, old SSH processes for the same port may linger and interfere. Kill them all first: `kill $(pgrep -f 'ssh.*localhost.run')`.
- **Cookie banners on every Amazon session** — each new browser_navigate to Amazon requires accepting cookies. Always click "Accept" (@e19) before extracting results.
- **Safari on iPhone blocks Amazon product links** for certain categories. If the user reports "link doesn't open", it's a Safari content blocker issue — tell them to copy and paste the URL.
