# Vite + React + TypeScript Scaffolding Recipe

A proven recipe for building full React mockups and portals from scratch when the user says "use react scaffolding" or "build a full app."

## Project Structure

```
<project-name>/
├── index.html              # Add Inter + JetBrains Mono font links in <head>
├── public/
│   └── favicon.svg          # Custom SVG favicon
├── src/
│   ├── main.tsx             # Entry point — unchanged from Vite scaffold
│   ├── App.tsx              # Root layout + page state routing
│   ├── index.css            # Design system CSS variables + all component styles
│   ├── types.ts             # Shared TypeScript types/interfaces
│   ├── data.ts              # Mock data, constants, helper functions
│   └── components/
│       ├── Sidebar.tsx       # Navigation sidebar
│       ├── Dashboard.tsx     # Overview dashboard
│       ├── DeployWizard.tsx  # Multi-step wizard container
│       ├── SkillsMarketplace.tsx
│       ├── DeploymentsList.tsx
│       ├── Settings.tsx
│       └── WizardSteps/      # Step sub-components
│           ├── Step1Agents.tsx
│           ├── Step2Skills.tsx
│           ├── Step3Target.tsx
│           └── Step4Review.tsx
```

## Design System (Dark Cyberpunk Palette)

All tokens in `:root` inside `index.css`. One file governs the entire look.

```css
:root {
  --bg-primary: #07070d;
  --bg-secondary: #0d0d1a;
  --bg-surface: #12121f;
  --bg-surface-hover: #1a1a2e;
  --bg-surface-active: #222238;
  --bg-elevated: #18182b;

  --border-primary: #1e1e35;
  --border-hover: #2e2e4a;
  --border-active: #3e3e5e;

  --text-primary: #e8e8f0;
  --text-secondary: #a0a0b8;
  --text-muted: #6b6b80;

  --accent-purple: #a855f7;
  --accent-purple-glow: rgba(168, 85, 247, 0.2);
  --accent-purple-strong: rgba(168, 85, 247, 0.12);
  --accent-cyan: #22d3ee;
  --accent-green: #22c55e;
  --accent-red: #ef4444;
  --accent-blue: #3b82f6;
  --accent-amber: #f59e0b;

  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;

  --font-sans: 'Inter', -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  --transition-fast: 150ms ease;
  --transition-base: 250ms ease;
}
```

## Component Architecture Rules

| Pattern | Rule |
|---------|------|
| **Page state** | Simple `useState<Page>` in App.tsx, pass `onNavigate` callback. No react-router needed for <6 pages |
| **Wizard steps** | DeployWizard owns all state, passes down to step components via props + callbacks |
| **Interfaces** | All shared types in `types.ts`. Use `import type` everywhere for `verbatimModuleSyntax` |
| **Mock data** | Constants + arrays in `data.ts`. Export helper functions like `getStatusColor()` |
| **Icons** | `lucide-react` — import each icon by name, tree-shaken by Vite |
| **Styling** | Single `index.css` with utility classes (`.btn`, `.card`, `.badge`). No CSS modules |
| **Animations** | CSS `@keyframes fadeIn/slideIn/scaleIn` applied via class. No JS animation libs |

## Build Verification Sequence

```bash
npx tsc --noEmit          # TypeScript check (fast, catches type errors)
npm run build              # Vite production build (catches bundler errors)
npx vite preview --port 5173 --host   # Serve production build locally
```

## Common Pitfalls

1. **verbatimModuleSyntax errors** — Every type-only import needs `import type { ... }` syntax. This is the #1 cause of failed builds on freshly scaffolded Vite projects. Fix with a single sed pattern: `sed -i "s/import { \([A-Z]\)/import type { \1/g"` on files that import types (careful with React hooks — they're values, not types).
2. **Unused React imports** — React 18+ JSX transform doesn't need `import React from 'react'`. The Vite template won't include it, but if you add it, `verbatimModuleSyntax` will flag it as unused.
3. **Missing font files** — Google Fonts CDN links go in `index.html` `<head>`, not CSS. Add preconnect + stylesheet links for Inter and JetBrains Mono.
4. **Port conflicts** — `vite preview` on default 4173 usually works. Use `--port` if needed.
