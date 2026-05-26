# Childminding Hub — Full Tabbed Implementation Example

This reference contains the complete tabbed page used for the UK Childminding Hub at montygroup.uk/childminding. It is a real deployed example of the "Option B: Tabbed Navigation" layout pattern from the uk-resource-hub-builder skill.

## Architecture

- **6 tabs**: Getting Started, Funding, Ofsted, EYFS, Policies, Community
- **Light theme** (`background: #f0f4f8`) — flipped from original dark gradient after user feedback
- **Colour-coded cards per section**: yellow (started), green (funding), blue (Ofsted), purple (EYFS), white (policies), indigo (Facebook)
- **Tab switching**: plain JS IIFE, no dependencies, inlined in the `<script>` tag
- **Responsive**: grids collapse to 1 column on mobile, tab bar scrolls horizontally
- **First tab active by default**: "Getting Started" visible on page load

## Key Implementation Details

### Tab bar scrolls without a visible scrollbar
```css
.cm-tabs {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}
.cm-tabs::-webkit-scrollbar { display: none; }
```

### Tab content visibility
```css
.cm-tab-content { display: none; animation: cm-fade 0.25s ease; }
.cm-tab-content.active { display: block; }
```

### Card colour variants
|css class | bg | border | heading colour | section |
|----------|-------|--------|----------------|---------|
| cm-card-yellow | #fff9e6 | #fde68a | #92400e | Getting Started |
| cm-card-green | #ecfdf5 | #a7f3d0 | #065f46 | Funding |
| cm-card-blue | #eff6ff | #bfdbfe | #1e40af | Ofsted |
| cm-card-purple | #f5f3ff | #ddd6fe | #5b21b6 | EYFS |
| cm-card-slate | #ffffff | #e2e8f0 | #0f172a | Policies |
| cm-card-facebook | #eef2ff | #a5b4fc | #4338ca | Community |

### Tab JavaScript
```javascript
(function() {
  const tabs = document.querySelectorAll('.cm-tab');
  const contents = document.querySelectorAll('.cm-tab-content');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const target = tab.getAttribute('data-tab');
      tabs.forEach(t => { t.classList.remove('active'); t.setAttribute('aria-selected', 'false'); });
      contents.forEach(c => c.classList.remove('active'));
      tab.classList.add('active');
      tab.setAttribute('aria-selected', 'true');
      document.getElementById('tab-' + target)?.classList.add('active');
    });
  });
})();
```

### Alert boxes for key information
Two colour variants for emphasis callouts:
- `cm-alert-amber` — amber bg (#fffbeb + #fcd34d border) for funding rate notes
- `cm-alert-blue` — blue bg (#eff6ff + #93c5fd border) for inspection readiness tips

## Deployment History for This Page
1. Original: dark gradient (slate-900/orange-950/yellow-950), full scroll layout
2. User: "update the colours... can't see the tabs or structured layout"
3. Fix 1: light theme with colour-coded card sections, still full scroll
4. User: "a long list isn't the look I want"
5. Fix 2: tabbed interface — 6 tabs replacing scroll sections

## Source File
`src/pages/childminding.astro` in the montygroup-astro GitHub repo.
