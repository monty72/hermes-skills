---
name: skills-marketplace
title: Skills Marketplace
description: "Full AI agent skill marketplace — Flask API + Astro 5 frontend + Vercel deployment. Build from scratch: schema design, seed data, REST endpoints, React islands for browse/detail/landing, dynamic route fallbacks."
---

# Skill Marketplace Builder

## Overview

Builds a full AI agent skill marketplace combining best-in-class design patterns from LobeHub, SkillsMP, SkillsLLM, Agensi, ClawHub, and AI Agents Directory. Two-tier architecture: Flask API backend (SQLite + FTS5) and Astro 5 frontend (React islands) deployed on Vercel.

## Structure

```
~/skill-marketplace/
  api.py            # Flask API server (port 5010)
  data/
    schema.sql       # SQLite schema with FTS5 full-text search
    skills.db        # SQLite database
  scripts/
    seed.py          # Seed data script (13 skills, 8 authors, 4 collections)
    init_db.py       # Initialize database + rebuild FTS index

~/dev-site/
  src/pages/
    skills.astro               # Marketplace landing page
    skills/browse.astro        # Browse with filters + pagination
    skills/[slug].astro        # Dynamic detail page (getStaticPaths fallback)
  src/components/
    SkillsMarketplace.tsx      # Landing page React island
    SkillsBrowse.tsx           # Browse page React island
    SkillDetail.tsx            # Detail page React island
  vercel.json                  # Rewrite: /skills/(.*) -> /skills/__fallback__
```

## API Endpoints (port 5010)

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/health | GET | Status check + skills count |
| /api/stats | GET | Marketplace stats + category breakdown |
| /api/skills | GET | Paginated list with filters |
| /api/skills/{slug} | GET | Full detail with author, similar, versions |
| /api/skills/search?q= | GET | FTS5 full-text search |
| /api/authors | GET | All authors with top skills |
| /api/authors/{slug} | GET | Author detail + their skills |
| /api/collections | GET | Curated bundles with skill names |
| /api/rankings | GET | Pre-computed lists (quality, stars, fresh, trending) |
| /api/use-cases | GET | All use cases with top 3 skills |
| /api/activity | GET | Recent activity feed |
| /api/skills/submit | POST | Submit new skill from GitHub URL |
| /api/feedback | POST | Agent usage telemetry |

## Key Technical Patterns

### FTS5 full-text search
- Create schema with `CREATE VIRTUAL TABLE skills_fts USING fts5(name, description, tags, author, content='skills', content_rowid='rowid')`
- After inserting skills, rebuild the index: `INSERT INTO skills_fts(skills_fts) VALUES('rebuild')`
- Rebuild must happen after EVERY data insertion, not just at creation
- On API startup, always run the rebuild command to catch offline DB manipulation
- Search query must use double-quoted phrases: `'"' + safe + '"'`

### Dynamic routes on Vercel static
- Astro 5 static output can't pre-generate unknown slug pages
- Solution: getStaticPaths returning `[{params: {slug: '__fallback__'}}]` generates one page shell
- vercel.json rewrites `/skills/(.*)` to `/skills/__fallback__` so any slug URL serves that shell
- The React component reads `window.location.pathname` in a useEffect to extract the slug
- Fetch API data client-side: fetch(`http://localhost:5010/api/skills/${slug}`)

### API port conflict handling
- Flask's debug mode with `use_reloader=True` spawns a child process that holds the port
- Fix: add a startup socket check that frees the port with `fuser -k {port}/tcp` before binding
- Set `use_reloader=False` to prevent duplicate reloader processes

### React island approach for API-dependent pages
- Astro `client:load` for components that need client-side API data
- The Astro page shell is static; the React component hydrates and fetches
- This avoids SSR complexity on Vercel static output
- Pattern: create `.tsx` component in `src/components/`, import in `.astro` with `<Component client:load />`

## Design Patterns (best-in-class features)

| Feature | Source | Implementation |
|---------|--------|---------------|
| Dual-audience toggle | LobeHub | "I'm an Agent" / "I'm a Human" pill switch |
| Use-case browsing | SkillsMP | Categories from /api/use-cases |
| Security score | SkillsLLM | Color-coded badge (green 90+, amber 70+, red <70) |
| @author/skill naming | ClawHub | Card title format |
| Premium/Free | Agensi | Purple premium badge, gray free, bundle discounts |
| Tabbed install | Agensi | Hermes CLI / OpenClaw / npx tabs with copy buttons |
| URL-synced filters | built | history.replaceState on every filter change |

## Page Components

### 1. Landing Page (SkillsMarketplace.tsx)
- Hero with title + tagline + animated stat counters
- Audience toggle (Agent/Human) that swaps search placeholder
- Search bar with enter-key navigation to `/skills/browse?q=...`
- Trending Now section from `/api/rankings` trending endpoint
- Highest Quality section from rankings
- Featured Collections with premium/free badges and discount labels
- Use Cases grid from `/api/use-cases`
- Loading: skeleton pulse animation; Error: banner with retry button

### 2. Browse Page (SkillsBrowse.tsx)
- Left sidebar filters: Category dropdown, Platform multi-select, Quality tier, Min stars
- Top bar: search input, results count badge, sort dropdown
- Sort options: Recommended, Most Starred, Trending, Recently Updated, Newest, Name A-Z
- Skill card: @author/name, description, category pill, platform color pills, quality badge, stars, premium/free
- Pagination: page numbers with ellipsis, prev/next, "Page X of Y"
- All state synced to URL query params
- States: skeleton grid (9 cards), error banner, empty state with reset CTA

### 3. Detail Page (SkillDetail.tsx)
- Header: name, @author, category badge, quality tier, premium/free, verified check, GitHub link
- Stats row (6-column): Stars, Forks, Installs, Rating, Downloads, Security score
- Description + long_description sections
- Platforms and compatibility badges with colors
- Tabbed install: Hermes CLI (`hermes skill add <slug>`), OpenClaw, npx
- Tags as clickable pills linking to browse
- Version history cards
- File listing with type badges
- Similar skills section (6 cards)
- Reviews section with star ratings
- Loading skeleton, 404 error page with retry

## Commands

```bash
# Start API server
cd ~/skill-marketplace && python3 api.py

# Re-seed database (clears and re-inserts)
cd ~/skill-marketplace && python3 scripts/seed.py

# Re-init DB (recreates tables from schema)
cd ~/skill-marketplace && python3 scripts/init_db.py

# Build and deploy frontend
cd ~/dev-site
npm run build
npx vercel build --prod --token <TOKEN>
npx vercel deploy --prebuilt --prod --token <TOKEN> --yes
```

## Vercel token
<REDACTED - stored in vault>

## Pitfalls

1. **FTS5 returns zero results after seeding** - the FTS index needs a manual rebuild after data is inserted. Always run the rebuild command after seeding.
2. **Port 5010 already in use** - Flask's reloader spawns a child process that holds the port. The socket-check + fuser cleanup pattern in api.py handles this.
3. **Dynamic routes on Vercel static** - without vercel.json rewrite, /skills/{slug} returns 404. The rewrite is essential.
4. **Static path page props don't render React islands** - the [slug].astro just renders Layout + island. No frontmatter data fetching since all data comes from the API client-side.
5. **Empty slug in URL** - when rewrite sends /skills to __fallback__, the component extracts the last path segment. Handle the empty case by showing a redirect or landing content.
6. **Template literals inside JSX expression blocks in .astro files** - esbuild can choke on backtick strings inside `{ }` in .astro, especially in .map() + JSX callbacks. Use string concatenation instead. In .tsx files template literals work fine.
