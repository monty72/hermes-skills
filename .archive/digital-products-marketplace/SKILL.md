---
name: digital-products-marketplace
description: Build, price, and sell digital products — templates, tools, guides, starters — using an agent-driven workflow. Covers market research, platform selection, product creation (Excel/PDF/ZIP), pricing strategy, payment setup, product page design, and ongoing idea generation.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [digital-products, marketplace, gumroad, lemonsqueezy, payhip, monetization, templates]
    related_skills: [modern-astro-ci-cd-setup, cloud-architecture-authoring, static-site-deployment, watchers]
---

# Digital Products Marketplace

## Overview

A repeatable process for creating and selling digital products (templates, tools, guides, code starters) using an AI agent for most of the work. The user provides domain expertise and a small seed budget (~£1k); the agent handles research, creation, deployment, and monitoring.

The stack: Astro 5 site → Vercel (product pages + marketing) → LemonSqueezy or similar (payment + delivery) → cron-based idea pipeline.

## When to Use

- User wants to create a side income stream from digital products
- User has domain expertise they can package (cloud architecture, energy, property, dev tools)
- User asks "what digital products should I build" or "how to monetize my skills"
- Building a product line around a specific expertise area (cloud architecture, energy, property)

## Step-by-Step

### 1. Market Research

Use `delegate_task` with `web_search` to research three axes in parallel:

**Axis A — Platform comparison:**
Compare Gumroad (10%+$0.50, built-in discovery), LemonSqueezy (5%+$0.50, global tax compliance), Payhip (5%, best value at scale), Whop (~5.7%, community products). Key factors: fee structure, tax handling, payout schedule, email ownership, API availability.

**Axis B — Category analysis:**
Top categories by real revenue (Gumroad 146K product dataset):
- Software/Dev Tools: $65.8M (32% of all revenue), $60K/product
- Business templates: $15.4M, $10K/product
- 3D assets: $13.9M, $6.7K/product
- Design templates: $8.8M, $7.4K/product
- Self-improvement: $8.7M, $8.5K/product
- Fitness/Health: $4.2M, $11K/product

**Axis C — Case studies:**
Look for solo creators who started with £0-100. Patterns: build in public, niche down, ship fast, zero paid ads, Product Hunt launch, charge real money early.

### 2. Platform Selection

| Scenario | Platform |
|----------|----------|
| First product, zero audience | Payhip Free → list on Etsy |
| Quick launch, simplicity | Gumroad |
| Software/global tax compliance | LemonSqueezy or Polar.sh |
| UK/EU creator, value at scale | Payhip Pro (at £1.5K+/mo) |
| Community/Discord products | Whop |
| Design assets/graphics | Creative Market or Etsy |

LemonSqueezy is the best general recommendation for UK creators: 5%+$0.50, handles global VAT automatically, no merchant-of-record registration needed.

### 3. Product Creation

**For each product, create these artifacts:**

a) **Product page** — An Astro page on the user's existing site (e.g., `montygroup.uk/tools/<product-slug>`). Structure:
   - Hero section (icon, title, price, buy button, status badge)
   - "What's Included" grid (feature cards with icons)
   - Detailed breakdown (pillars, screenshots, tabs)
   - "Who Is This For" section
   - FAQ
   - Bottom CTA

b) **Downloadable files** — Generate product files using Python:
   - **Excel (.xlsx)** — Use `openpyxl` for scorecards, calculators, templates with styling and charts
   - **PDF guide** — Use `fpdf2` (not `reportlab`) for lightweight guides
   - **ZIP bundle** — Use Python's `zipfile` module to package multiple files
   
   Store files in `public/products/` on the Astro site. Create a `scripts/generate-<product>.py` so the files can be regenerated.

c) **Product files location convention:**
   ```
   public/products/
     <product>-toolkit.zip     ← Downloadable bundle
     <product>-scorecard.xlsx  ← Individual file
     <product>-guide.pdf       ← Individual file
   scripts/
     generate-<product>.py     ← Regeneration script
   ```

### 4. Pricing Strategy

From the research data:
- Single product: avg 269 sales lifetime (~$13K)
- 4-5 products: avg 1,681 sales (~$82K)
- 11+ products: avg 5,201 sales ($255K+)

Pricing bands by category:
- Templates/spreadsheets: £15-29
- Developer tools/starters: £29-49
- Courses/playbooks: £39-99
- Software/SaaS: subscription £5-15/mo or one-time £49-199

Always charge real money from day one. Offer lifetime updates as a value-add.

### 5. Product Page Template

Use the existing Astro site's design system (MontyGroup: purple primary, white cards, pixel-grid background). See `modern-astro-ci-cd-setup` for the full design tokens. Key components:

- `content-header` — Breadcrumb + title + subtitle
- `section-card` — Content sections
- `product-card` — Product grid cards with hover lift
- `stat-card` — Metric display
- `badge` — Status badges (Available Now, Coming Soon)
- `pill-link` — Quick links

### 6. Payment Integration

- Sign the user up for LemonSqueezy (free, no monthly fee)
- Create a product with the ZIP file as the download
- Add a "Buy Now" link on the product page pointing to the LemonSqueezy checkout
- LemonSqueezy handles: payment processing, VAT/GST collection, file delivery, customer emails

### 7. Ongoing Idea Pipeline

Set up a weekly cron job to monitor for new product opportunities:

```bash
cronjob action=create \
  name="<topic>-idea-scout" \
  schedule="0 8 * * 1" \
  skills='["brave-web-search"]' \
  prompt="Monitor Product Hunt, HN, Reddit, GitHub Trending for... (see reference file)"
```

Sources to scan:
- **Product Hunt** — developer-tools, productivity, design-tools categories
- **Hacker News** — cloud/infra/devops frontpage posts
- **Reddit** — r/azure, r/devops, r/cloudcomputing, r/kubernetes, r/backstage
- **GitHub Trending** — cloud/devops repos
- **Gumroad/Product trends** — What templates and tools are selling

The cron delivers a scored list (🔥 HOT, 👍 WARM, 💤 COLD) to the user's chat every Monday.

### 8. Product Pipeline Management

- Keep "Coming Soon" placeholders on the tools hub page for visibility
- Maintain a product backlog with priority scores from the cron
- Build one product at a time, starting with the highest-scored 🔥 HOT item
- Update the site, generate files, push to deploy → all in one session

## Reference Files

- `references/platform-comparison.md` — Full fee comparison across Gumroad, LemonSqueezy, Payhip, Polar, Dodo, Whop, Etsy, Ko-fi, Paddle, ThriveCart at various revenue levels.
- `references/case-studies.md` — Detailed case studies of solo creators who succeeded with under £1k investment (Marc Lou, Andy Cloke, Gil Hildebrand, Pieter Levels, Tim Bennetto, Nic Polale).
- `references/category-data.md` — Revenue breakdown by category from 146K Gumroad product dataset, hidden gem niches, and pricing band data.

## Common Pitfalls

1. **Overthinking the first product** — Don't try to build a perfect product. Ship a minimal viable toolkit at 70% completeness and iterate based on real feedback. The case studies show that all successful solo creators shipped fast.

2. **Pricing too low** — Products under £15 get eaten by platform fees (Gumroad takes ~21% on a $10 sale). Price at £25+ for decent margins. Premium pricing also signals quality.

3. **No buy link on the product page** — The CTA must be immediately visible. Place it in the hero section, not buried at the bottom. Use the accent color for the button.

4. **Building features nobody asked for** — Watch for this in the cron output. Prioritise ideas that solve real, expressed pain points (Reddit complaints, HN discussions) rather than hypothetical needs.

5. **Vercel CI not deploying after adding pages** — See `modern-astro-ci-cd-setup` pitfalls #1 (wrong project) and #13 (.vercel gitignore).

6. **Platform lock-in** — Own your customer list. Use platforms that let you export emails (Gumroad, Payhip, LemonSqueezy all allow this). Avoid Etsy as the primary sales channel—use it for discovery only.

7. **PDF generation failures** — fpdf2's `multi_cell(0, h, text)` can fail with "Not enough horizontal space" when the cursor position hasn't been reset. Always call `pdf.set_x(pdf.l_margin)` before each `multi_cell` call.

## Verification Checklist

- [ ] Product page renders correctly (build with `npm run build`, check `dist/`)
- [ ] Product files are generated and stored in `public/products/`
- [ ] ZIP bundle is created and downloadable
- [ ] Navigation updated (if adding a new section)
- [ ] Landing page updated with new card
- [ ] Payment link configured (LemonSqueezy product created)
- [ ] Build succeeds (`npm run build`)
- [ ] Deployed to production (verify with curl)
- [ ] Cron job for idea pipeline is active
