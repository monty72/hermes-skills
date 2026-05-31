# Mission Control V4.0 — Design Brief & Build Log

Delivered as an image by the user on 2026-05-26. This document captures both the original design spec AND the actual build decisions made during implementation.

**Status: BUILT** (2026-05-26). The V4 frontend is live at `~/mission-control-v4/` and running on port 3000 alongside the Python API backend on port 8081.

## Tech Stack

- **Framework:** Next.js (hosted on localhost, dev server always running)
- **Styling:** Tailwind CSS
- **Dev workflow:** Start the dev server and keep it running (hot reload)

## Visual Style

**Clean, minimal layout inspired by Linear** (the project management tool):
- White/light base backgrounds with light gray borders
- Clean typography with generous whitespace
- Linear-like structure and information density

**Retro game accents layered on top** — the distinctive twist:
- Pixel art icons for navigation elements
- 8-bit style decorative elements (borders, dividers, section headers)
- Subtle pixel grid backgrounds in section headers
- Monospace fonts for data/numbers (retro terminal feel)
- Pixel art character avatars for each tracked agent (Hermes, OpenCrawl, OpenClaw workers)
- 8-bit style navigation icons
- Retro game UI details like pixel progress bars

**Think:** Linear's structure and whitespace, but with pixel art character avatars for agents, 8-bit icons for navigation, and retro game UI details like pixel progress bars.

## Colour Palette — Lonely Octopus Brand

| Role | Hex | Notes |
|------|-----|-------|
| Base background | `#FFFFFF` | White |
| Secondary background | `#F5F5F5` | Light gray |
| Primary | `#6B21A8` | Deep purple |
| Accent | `#A855F7` | Bright purple |
| Highlight | `#E905FF` | Soft lavender — hover states, tags |
| Text | `#1A1A2E` | Near-black |

## Migration Path

### Phase 1 — Scaffold (Next.js + Tailwind)
1. `npx create-next-app@latest mission-control-v4 --typescript --tailwind`
2. Set up project structure, routing, layout components
3. Port the 4-tab structure (Overview, Hermes Self, OpenClaw, Proxmox) to React components

### Phase 2 — API Layer
1. Create API route handlers (`/api/route.ts`, `/api/cron/route.ts`, etc.)
2. Either proxy to the existing Python server or build new data-fetching logic
3. Keep the Python collector as-is (data source)

### Phase 3 — Theming
1. Apply Lonely Octopus colour palette to Tailwind config
2. Build pixel art components (PixelProgressBar, PixelIcon, PixelAvatar)
3. Create Linear-inspired card/list components
4. Add retro decorative elements

### Phase 4 — Polish
1. Responsive layout
2. Loading skeletons
3. Real-time updates (polling or SSE from collector)
4. Auth middleware (preserve Basic Auth)

## Notes

- The V3.x Python server (`server.py` + inline HTML) remains the current production version
- V4.0 is the target architecture but not yet implemented
- The Python server's `/api` endpoints remain the canonical data source regardless of frontend framework

---

## Actual Build (2026-05-26)

### Architecture

```
Next.js (port 3000)                Python API (port 8081)
┌─────────────────────┐     ┌───────────────────────────┐
│  [[...slug]]/route.ts│────▶│  server.py (with auth)    │
│  (proxies + adds     │     │  reads observability.json │
│   Basic Auth header) │     │  (written by cron every   │
│                      │◀────│  5 min)                   │
├─────────────────────┤     └───────────────────────────┘
│  page.tsx (Overview) │     
│  hermes/page.tsx     │     ┌───────────────────────────┐
│  openclaw/page.tsx   │     │  ~/mission-control-v4/     │
│  proxmox/page.tsx    │     │  Next.js + Tailwind       │
└─────────────────────┘     └───────────────────────────┘
```

### Key Design Decisions

**API Proxy via Route Handler, Not `rewrites()`**
The initial approach used `next.config.ts` `async rewrites()` but this doesn't forward custom HTTP headers. Since the Python backend has Basic Auth, the rewrite returned 401. The fix: a catch-all route handler at `src/app/api/[[...slug]]/route.ts` that:
1. Receives the incoming request path (e.g., `/api/cron`)
2. Strips `/api` prefix
3. Forwards to `http://127.0.0.1:8081/api/...` with `Authorization: Basic <base64>` header
4. Returns the response

This means **the Python server stays fully protected** by Basic Auth, and the Next.js frontend never exposes credentials to the browser.

**Key code** (`src/app/api/[[...slug]]/route.ts`):
```typescript
const BACKEND = "http://127.0.0.1:8081";
const AUTH = Buffer.from("mc:MissionCtrl2026!").toString("base64");

export async function GET(request: NextRequest, { params }) {
  const { slug } = await params;
  const path = slug ? "/" + slug.join("/") : "";
  const url = `${BACKEND}/api${path}${request.nextUrl.search}`;
  const res = await fetch(url, {
    headers: { Authorization: `Basic ${AUTH}` },
    cache: "no-store",
  });
  const body = await res.text();
  return new NextResponse(body, { status: res.status, headers: { ... } });
}
```

**Data Source Separation**
- The Python collector (cron, every 5 min) writes `observability.json` to the Hermes host
- The Python server (`server.py` on port 8081) reads that file and serves the API
- The Next.js frontend (port 3000) proxies through the Python server
- This means all three layers (collector → API → frontend) are independently deployable

### Project Structure

```
~/mission-control-v4/
├── src/
│   ├── app/
│   │   ├── globals.css           # Tailwind v4 + Lonely Octopus palette + pixel/retro utilities
│   │   ├── layout.tsx            # Sidebar + main content area
│   │   ├── page.tsx              # Overview tab
│   │   ├── api/[[...slug]]/
│   │   │   └── route.ts          # API proxy (adds Basic Auth)
│   │   ├── hermes/page.tsx       # Hermes Self tab
│   │   ├── openclaw/page.tsx     # OpenClaw tab
│   │   └── proxmox/page.tsx      # Proxmox tab
│   ├── components/
│   │   ├── Sidebar.tsx           # Left nav with pixel art icons
│   │   ├── StatusCard.tsx        # Clickable metric card
│   │   ├── Modal.tsx             # Drill-down modal (Escape to close)
│   │   ├── PixelProgressBar.tsx  # Retro pixel-style progress bar
│   │   └── AgentAvatar.tsx       # Pixel art agent avatar
│   └── lib/
│       └── api.ts                # TypeScript types + fetch helpers
├── next.config.ts
├── package.json
└── tsconfig.json
```

### Running

```bash
# Ensure the Python API server is running (port 8081)
cd ~/mission-control/src && python3 server.py &

# Start the Next.js dev server (port 3000)
cd ~/mission-control-v4 && npx next dev -p 3000

# Access at http://localhost:3000
```

Production build:
```bash
cd ~/mission-control-v4 && npx next build && npx next start -p 3000
```

### Components Used

All components in `src/components/`:

| Component | Purpose | State |
|-----------|---------|-------|
| `Sidebar` | Left nav with 4 tabs, pixel icon navigation, active state highlighting | Link-based, uses `usePathname()` |
| `StatusCard` | Clickable metric card with value, label, icon, status dot, hover lift | `onClick` drill-down, `card-lift` hover animation |
| `Modal` | Drill-down overlay with title, close button, Escape-to-close, backdrop click-to-close | `open`/`onClose` props |
| `PixelProgressBar` | Retro pixel-art progress bar with label and percentage | CSS `box-shadow` pixel borders |
| `AgentAvatar` | Pixel grid-character avatar per agent with status indicator dot | Maps initials to unicode pixel shapes (⬟⬢⏣⬡◈⚔▣⛁) |

### Colour Palette Implementation

Defined in `globals.css` via Tailwind v4 `@theme inline`:

```css
@theme inline {
  --color-lo-base: #ffffff;
  --color-lo-bg-alt: #f5f5f5;
  --color-lo-primary: #6b21a8;
  --color-lo-primary-light: #7c3aed;
  --color-lo-accent: #a855f7;
  --color-lo-highlight: #e905ff;
  --color-lo-text: #1a1a2e;
  --color-lo-text-muted: #6b7280;
  --color-lo-border: #e5e7eb;
  --color-lo-success: #22c55e;
  --color-lo-warning: #f59e0b;
  --color-lo-error: #ef4444;
  --color-lo-info: #3b82f6;
}
```

Usage: `bg-lo-base`, `text-lo-primary`, `border-lo-border`, `text-lo-accent`, etc.

### Tailwind v4 Note

This project uses Tailwind CSS v4 (CSS-based configuration, no `tailwind.config.js`). Custom values are defined in `globals.css` via `@theme inline { --color-*: ... }`. The `@import "tailwindcss"` directive replaces the old `@tailwind base/components/utilities` directives.

### Retro/Pixel Utility Classes (globals.css)

| Class | Effect |
|-------|--------|
| `.pixel-grid` | 16px dot-grid background pattern (radial-gradient) |
| `.pixel-grid-dark` | Same but with purple-tinted dots |
| `.pixel-border` | 2px four-sided `box-shadow` border (gray) |
| `.pixel-border-primary` | Same but in `#6b21a8` purple |
| `.pixel-progress` | 8px tall retro progress bar track |
| `.pixel-progress-fill` | Animated fill with pixel shadow |
| `.card-lift` | -2px Y translate + purple shadow on hover |
| `.scanlines::after` | Pseudo-element scanline overlay effect |
