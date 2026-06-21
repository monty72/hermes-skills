---
name: market-research
title: Multi-Source Market & Product Research
description: Systematic scanning of Product Hunt, Hacker News, Reddit, GitHub Trending, and Gumroad for product opportunities, competitive intelligence, and market signals. Includes report synthesis and prioritization.
related_skills: [brave-web-search, content-site-builder, uk-property-investment]
---

Use this skill when you need to research market opportunities, analyze competitive landscapes, find product gaps, or monitor for emerging trends across multiple sources.

**When to load:** Before any "monitor the market" or "find product opportunities" request that spans multiple sources.

## Research Sources

| Source | What to Look For | Search Pattern |
|--------|-----------------|----------------|
| **Product Hunt** | Trending tools in developer-tools, productivity, AI infrastructure categories | `web_search("Product Hunt trending developer tools cloud infrastructure 2026")` |
| **Hacker News** | Front-page discussions about cloud/infra/devops pain points | `web_search("site:news.ycombinator.com cloud infrastructure devops 2026")` |
| **Reddit** | "I wish there was", complaints, common questions | `web_search("site:reddit.com r/azure OR r/devops OR r/kubernetes pain points 2026")` |
| **GitHub Trending** | What repos are hot in cloud/devops/developer-tools | `web_extract("https://github.com/trending?since=weekly")` |
| **Gumroad/CC** | What cloud/dev templates are selling | `web_search("Gumroad cloud architecture terraform kubernetes devops toolkit")` |

## Methodology

### Phase 1: Parallel Source Scan
Run searches across ALL sources before analyzing any single result. Use `delegate_task` for 5+ topics, or chain `web_search` calls for 3-5 sources.

```python
from hermes_tools import web_search, web_extract

# Run parallel searches (chain via one execute_code block)
results = {}
results['ph'] = web_search("Product Hunt cloud architecture platform engineering")
results['hn'] = web_search("site:news.ycombinator.com cloud devops 2026")
results['reddit'] = web_search("site:reddit.com r/azure \"wish there was\" cloud")
results['gh'] = web_extract("https://github.com/trending?since=weekly")
```

### Phase 2: Deep Dive on Signal
For results with high engagement (200+ upvotes, multiple comments, repeated across sources):
- Use `web_extract(url)` to get full thread/article content
- Look for specific pain points: exact quotes, price points mentioned, "if only X existed"
- Note sentiment (frustration/desire vs. satisfaction)

### Phase 3: Idea Generation
For each pain point found, structure as:

- **Idea name** — Short, memorable title
- **Problem it solves** — The exact pain point (quote if from community)
- **Target audience** — Job title, company size, persona
- **Estimated price point** — $9-$19 impulse, $29-$79 professional, $99+ premium
- **Monetization model** — One-time, subscription, or both
- **My ability to build it** — Can Hermes produce this? (templates/PDFs/spreadsheets = yes; SaaS backend = maybe; hardware/app store = no)
- **First-mover advantage** — Crowded, open, or first-mover?
- **Priority score** — 🔥 HOT (this week), 👍 WARM (this month), 💤 COLD (backlog)

### Phase 4: Prioritization
Filter ideas that:
- Can be built by an AI agent (templates, guides, spreadsheets, code starters, calculators)
- Leverage Matt's cloud architecture expertise
- Have clear target audience willing to pay
- Minimal to zero ongoing cost to maintain

## Report Format
Start with a **Summary Verdict** calling out the single most promising idea at top. Then list each idea with its priority label. Close with a recommended action plan (week-by-week build schedule).

## Pitfalls
- **curl | python3 may be blocked** by Hermes security (tirith). Use `web_search` tool or `execute_code` with `from hermes_tools import web_search` instead of raw curl pipes.
- **GitHub Trending pages are huge** and may truncate via `web_extract`. Use `?since=weekly` for better signal, and be selective about which repo details to capture.
- **Reddit threads may fail to fetch** via `web_extract` (blocked parsing). Use `web_search("site:reddit.com ...")` with descriptive queries to get thread titles and excerpts instead.
- **Gumroad has poor search indexing**; use broader searches ("cloud architecture template, terraform module") and look at DEV/LinkedIn articles referencing Gumroad bestsellers instead.
- **Don't trust subagent self-reports** about external operations. If a subagent claims "found a product," verify the URL yourself.

## Related Skills
- `brave-web-search` — Lower-level Brave Search API usage (raw curl, this skill builds on it)
- `content-site-builder` — For using research output to build comparison/content sites
- `uk-property-investment` — Similar multi-source research pattern but for UK property
