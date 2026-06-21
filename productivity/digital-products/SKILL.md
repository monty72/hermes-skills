---
name: digital-products
description: "Build, price, sell digital products — templates, guides, toolkits, code starters. Covers market research, platform selection (LemonSqueezy, Gumroad, Payhip), product creation (PDF/ZIP/Excel), pricing strategy, Astro product pages, and the creator economy playbook."
tags: [digital-products, marketplace, gumroad, lemonsqueezy, payhip, monetization, templates, creator-economy]
related_skills: [static-site-deployment, modern-astro-ci-cd-setup, cloud-architecture-authoring]
---

# Digital Products — Create, Publish, Monetize

Build a digital products business by leveraging AI for creation and deployment. Core insight: digital products have 70-95% margins, "create once sell forever" scalability.

## When to Use

- User wants a side income stream from digital products
- User has domain expertise to package (cloud, energy, property, dev tools)
- User asks about Gumroad, LemonSqueezy, Etsy, or digital downloads
- Building a product page on an existing site

## 1. Platform Comparison

| Feature | **Gumroad** | **LemonSqueezy** | **Payhip** |
|---------|-------------|------------------|------------|
| Fee | 10% + $0.50 | 5% + $0.50 | 5% (Free), 2% ($29/mo) |
| MoR (tax) | ✅ Global | ✅ Global (100+ countries) | ⚠️ EU/UK only |
| Marketplace | ✅ Discover (30% fee) | ❌ | ❌ |
| Best for | Quick launches, beginners | SaaS/software, global tax | Budget-conscious, EU |

**Other platforms:** Polar.sh (5%, open-source dev tools), Whop (~5.7%, community products), Etsy (~16% effective, **zero-audience discovery**), Ko-fi (0% tips), ThriveCart ($495 one-time, 0% transaction fees).

**Winner for UK creators:** LemonSqueezy — handles global VAT, no merchant-of-record registration needed.

## 2. Market Research

Top selling categories (146K Gumroad products):
- **Software/Dev Tools**: $65.8M (32%), $60K/product
- **Business templates**: $15.4M, $10K/product
- Self-improvement: $8.7M, $8.5K/product
- Fitness/Health: $4.2M, **$11K/product** (hidden gem, low competition)
- Writing & Publishing: **$15,750/product** (only 226 products)

## 3. Pricing Strategy

| Product Type | Entry | Mid | Premium |
|-------------|-------|-----|---------|
| Templates | $5-15 | $19-49 | $49-97 |
| Ebooks/Guides | $5-10 | $15-30 | $30-49 |
| Code Starters | $19-39 | $39-79 | $79-199 |
| AI Prompt Packs | $9-19 | $19-47 | $47-97 |
| Courses | $19-49 | $49-199 | $199-499 |

**Products under £15 get eaten by fees.** Price £25+ for decent margins.

## 4. Product Creation Pipeline

See `references/product-authoring.md` for full detail. Summary:

1. **Create content** — markdown, YAML, Excel templates in `public/products/`
2. **Package assets** — Python zipfile for Zips, fpdf2 for PDFs, openpyxl for Excel
3. **Build product page** — Astro page at `src/pages/tools/<slug>/index.astro`
4. **Register in tools hub** — add entry to `src/pages/tools/index.astro`
5. **Set up payment** — LemonSqueezy product with download file
6. **Deploy**

## 5. Launch Workflow

1. Pick narrow niche with genuine expertise
2. Build MVP (70% completeness, ship fast)
3. List on Etsy (for discovery) + own site
4. Post on X/Twitter with build-in-public thread
5. Submit to Product Hunt
6. Cross-post to relevant subreddits/LinkedIn
7. Iterate based on real feedback

## 6. The Creator Playbook

Pattern from successful $0→$95k/mo case studies:
- Self-build the product (no outsourcing) — 6/6
- Build in public on X/Twitter — 5/6
- Launch on Product Hunt — 5/6
- Zero paid ads at start — 6/6
- Niched down hard — 6/6
- Shipped fast/imperfect MVP — 6/6
- Charged real money early — 6/6

**Starting costs:** $0-$100 across all case studies (domain + hosting only).

## 7. Ongoing Pipeline

Set up a weekly cron job to monitor Product Hunt, HN, Reddit for new product opportunities:

```bash
cronjob action=create name="<topic>-idea-scout" schedule="0 8 * * 1"
```

## References

- `references/product-authoring.md` — Full product creation: PDF generation (fpdf2), ZIP packaging, Astro page templates, product page patterns
- `references/platform-comparison.md` — Detailed fee comparison at various revenue levels across all platforms
- `references/case-studies.md` — Solo creator case studies (Marc Lou $95k/mo, Pieter Levels $3M/yr, etc.)
- `references/category-data.md` — Revenue breakdown by category, hidden gem niches, pricing bands
- `references/digital-product-business.md` — Full business strategy: platform comparison, pricing, the creator economy playbook

## Common Pitfalls

1. **Overthinking the first product** — Ship at 70% completeness, iterate on feedback
2. **Pricing too low** — Products under £15 get eaten by fees
3. **No buy link on product page** — CTA must be immediately visible in hero
4. **Building features nobody asked for** — Prioritise real pain points from Reddit/HN
5. **Platform lock-in** — Own your customer list, use platforms that let you export emails
6. **PDF generation failures** — Always `pdf.set_x(pdf.l_margin)` before `multi_cell`
7. **Single product isn't enough** — 4-5 products = $82K avg vs 1 product = $13K
