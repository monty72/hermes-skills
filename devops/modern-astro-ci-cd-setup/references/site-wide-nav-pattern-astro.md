# Astro Site-Wide Nav Pattern

A sticky navigation bar with hover-dropdown category sections, mobile hamburger, current-page highlighting, and a shared footer. Built into the shared Layout component and reused across all pages.

## Architecture

### Layout (`src/layouts/Layout.astro`)

The nav is part of the shared Layout component. It accepts a `currentPath` prop from each page for highlighting.

```astro
---
export interface Props {
  title?: string;
  currentPath?: string;
}
const { title, currentPath = '/' } = Astro.props;
---
```

### Per-page usage

Every page passes its route:

```astro
<Layout title="Energy Monitor — MontyGroup" currentPath="/energy">
```

For nested routes:
```astro
<Layout title="Tariff Calculator" currentPath="/energy/calculator">
```

For dynamic routes (`[slug]`):
```astro
<Layout title="Skill Detail" currentPath="/skills/[slug]">
```

This is critical — the dynamic route literal string is passed, not resolved, because `currentPath` is compared against `Astro.url` patterns statically.

### Nav data structure

```astro
const navSections = [
  {
    label: 'Energy',
    icon: '⚡',
    links: [
      { href: '/energy', label: 'Energy Monitor', icon: '🔋' },
      { href: '/agile', label: 'Agile Tracker', icon: '⚡' },
    ],
  },
  {
    label: 'Tech',
    icon: '💻',
    links: [
      { href: '/mission-control', label: 'Mission Control', icon: '🚀' },
    ],
  },
];
```

### Active state logic

```astro
function normalizePath(p: string): string {
  return p.replace(/\/$/, '') || '/';
}
function isActive(href: string): boolean {
  const normCurrent = normalizePath(currentPath);
  const normHref = normalizePath(href);
  if (normHref === '/') return normCurrent === '/';
  return normCurrent.startsWith(normHref);  // /energy/calculator matches /energy
}
function sectionHasActive(section): boolean {
  return section.links.some(l => isActive(l.href));
}
```

## HTML Structure

```html
<nav class="site-nav">
  <div class="nav-inner">
    <a href="/" class="nav-logo">MontyGroup</a>

    <!-- Hamburger toggle -->
    <input type="checkbox" id="nav-toggle" class="nav-toggle" />
    <label for="nav-toggle" class="nav-hamburger">
      <span></span><span></span><span></span>
    </label>

    <!-- Dropdown sections -->
    <div class="nav-sections">
      {navSections.map(section => (
        <div class={`nav-section${sectionHasActive(section) ? ' active' : ''}`}>
          <span class="nav-section-label">{section.icon} {section.label}</span>
          <div class="nav-links">
            {section.links.map(link => (
              <a href={link.href} class={`nav-link${isActive(link.href) ? ' current' : ''}`}>
                {link.icon} {link.label}
              </a>
            ))}
          </div>
        </div>
      ))}
    </div>
  </div>
</nav>

<slot />

<footer class="site-footer">...</footer>
```

## CSS

### Desktop (hover dropdowns)
```css
.nav-links {
  display: none;
  position: absolute;
  top: 100%;
  left: 0;
  min-width: 200px;
  background: #1e293b;
  border: 1px solid var(--nav-border);
  border-radius: 8px;
  padding: 6px;
  z-index: 200;
  box-shadow: 0 8px 24px rgba(0,0,0,0.4);
}
.nav-section:hover .nav-links,
.nav-section:focus-within .nav-links {
  display: block;
}
.nav-link.current {
  color: var(--nav-active);
  background: rgba(34, 211, 238, 0.08);
}
```

### Mobile (hamburger toggle)
```css
@media (max-width: 768px) {
  .nav-hamburger { display: flex; }
  .nav-sections {
    display: none;
    position: absolute;
    top: 56px;
    left: 0;
    right: 0;
    background: var(--nav-bg);
    border-bottom: 1px solid var(--nav-border);
    flex-direction: column;
    padding: 8px;
  }
  .nav-toggle:checked ~ .nav-sections {
    display: flex;
  }
  .nav-links {
    display: none;
    position: static;
    box-shadow: none;
    border: none;
    background: transparent;
    padding: 0 0 8px 0;
  }
  .nav-section:hover .nav-links,
  .nav-section:focus-within .nav-links {
    display: block;
  }
}
```

## Footer

Simple two-row footer:
- Top row: quick links (Home · Energy · Tech · Services · About)
- Bottom row: small copyright text

```css
.site-footer {
  background: var(--nav-bg);
  border-top: 1px solid var(--nav-border);
}
.footer-inner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}
.footer-links { display: flex; gap: 16px; flex-wrap: wrap; }
```

## Pitfalls

1. **Missing `currentPath` on a page** — the nav renders but the `current` class is never applied (it defaults to `/`). Always add `currentPath` to every `<Layout>` invocation or the current page won't highlight.

2. **Backtick template literals in Astro JSX blocks** — esbuild chokes on `${...}` syntax inside backtick template strings that are themselves inside `{ }` Astro expression blocks. This manifests as `Unexpected \"const\"` errors at odd columns. Use string concatenation instead.

3. **Dynamic route pages (`[slug].astro`)** — pass the literal route pattern `currentPath="/skills/[slug]"`, not the resolved URL. The Lit component compares against the `currentPath` prop, not `Astro.url`.

4. **Deeply nested routes** — `/energy/calculator` starts with `/energy`, so `isActive()` with `startsWith` will match it under the Energy section's `href="/energy"`. This is correct — the sub-page highlights the parent section. But `startsWith` means `/energy` would also match `/energy-anything`. Avoid routing `/energy` and `/energy-anything` as different sections for this reason.

5. **Sticky nav + page content** — `position: sticky` on `.site-nav` with `top: 0` works but can overlap page content if the page `<main>` doesn't have `padding-top`. Add `padding-top: 56px` (the nav height) to page content, or account for it in page layouts.

6. **Adding `currentPath` via automated patch** — when migrating from a bare `<Layout>` to one with `currentPath`, the per-page import is easy to miss for pages with multiline `<Layout` openings (`<Layout title="..."` on one line, `>` on the next). Use `grep -L 'currentPath'` to find missing ones after bulk-patching.
