---
name: concept-diagrams
description: "Generate flat, minimal light/dark-aware SVG diagrams as standalone HTML files."
version: 1.0.0
---

# Concept Diagrams

## Overview

Generate flat, minimal SVG diagrams as standalone HTML files — light/dark aware, educational visuals, non-software concepts.

## Features

- Light/dark mode auto-switch via `prefers-color-scheme`
- 9 semantic color ramps
- Sentence-case typography
- Clean, minimal aesthetic

## Template HTML

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  :root {
    --bg: #ffffff;
    --text: #1a1a2e;
    --line: #c0c0d0;
    --fill: #e8e8f0;
    --accent: #4361ee;
    --accent-light: #e0e7ff;
  }
  @media (prefers-color-scheme: dark) {
    :root { --bg: #1a1a2e; --text: #e0e0f0; --line: #4a4a6a; --fill: #2a2a4a; --accent: #6c8cff; --accent-light: #2a2a5a; }
  }
  body { margin: 0; background: var(--bg); display: flex; justify-content: center; align-items: center; min-height: 100vh; font-family: system-ui, sans-serif; }
  svg { width: 800px; max-width: 100%; height: auto; }
</style>
</head>
<body>
<svg viewBox="0 0 800 500" xmlns="http://www.w3.org/2000/svg">
  <rect width="800" height="500" fill="var(--bg)" rx="8"/>

  <!-- Title -->
  <text x="400" y="40" text-anchor="middle" fill="var(--text)" font-size="22" font-weight="600" font-family="system-ui">Diagram Title</text>

  <!-- Box 1 -->
  <rect x="100" y="100" width="200" height="80" rx="8" fill="var(--accent-light)" stroke="var(--accent)" stroke-width="2"/>
  <text x="200" y="145" text-anchor="middle" fill="var(--accent)" font-size="16" font-weight="500" font-family="system-ui">Step 1</text>

  <!-- Arrow -->
  <line x1="300" y1="140" x2="380" y2="140" stroke="var(--line)" stroke-width="2" marker-end="url(#arrow)"/>
  <defs><marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="var(--line)"/></marker></defs>

  <!-- Box 2 -->
  <rect x="380" y="100" width="200" height="80" rx="8" fill="var(--fill)" stroke="var(--line)" stroke-width="2"/>
  <text x="480" y="145" text-anchor="middle" fill="var(--text)" font-size="16" font-weight="500" font-family="system-ui">Step 2</text>
</svg>
</body>
</html>
```

## Color Usage

| Role | Light | Dark |
|------|-------|------|
| Background | `#ffffff` | `#1a1a2e` |
| Text | `#1a1a2e` | `#e0e0f0` |
| Lines | `#c0c0d0` | `#4a4a6a` |
| Fill | `#e8e8f0` | `#2a2a4a` |
| Accent | `#4361ee` | `#6c8cff` |
| Accent light | `#e0e7ff` | `#2a2a5a` |
| Success | `#2ec4b6` | `#5edbd0` |
| Warning | `#f7934b` | `#f7b77b` |
| Danger | `#e63946` | `#ef6b75` |

## Dashboard Mode (Mission Control Aesthetic)

For live dashboard / mission-control pages (multi-panel status views), use this extended template. It adds:

- **Pulsing status dots** (`@keyframes pulse-dot`)
- **Metric cards** with large monospaced values, labels, and trend indicators (▲/▼)
- **Agent/Service cards** with status badges (Running/Idle/Error/Queued)
- **Activity timeline** with dot markers and timestamped entries
- **Quick action buttons** that copy to clipboard or open external links
- **Background grid** with subtle radial gradient glows

Color scheme:
```css
--bg-primary: #0a0a0f;
--bg-secondary: #111118;
--bg-card: #161622;
--bg-card-hover: #1c1c2e;
--border: #2a2a3e;
--text-primary: #f0f0f5;
--text-secondary: #8888a0;
--text-muted: #55556a;
--accent: #6c8cff;
--green: #4ade80;
--red: #f87171;
--amber: #fbbf24;
--blue: #60a5fa;
--purple: #a78bfa;
--cyan: #22d3ee;
--pink: #f472b6;
```

Layout: fixed header → 6-column metrics row → 4-column services grid → 2-column (activity timeline + agent list) → quick actions → footer.

Deploy as a single `index.html` using the `static-site-deployment` skill.

## Common Elements

- **Flow**: boxes + arrows left to right
- **Timeline**: horizontal line with nodes
- **Compare**: two columns side by side
- **Cycle**: circular arrow path
- **Layers**: stacked rectangles
- **Tree**: root + branches going down

## Templates

- **`templates/mission-control.html`** — Full dark-theme dashboard HTML template with metric cards, agent list, activity timeline, status grid, and quick actions. All data is configurable via the `CONFIG` JS object at the top of the script. Deploy with `static-site-deployment` skill.
