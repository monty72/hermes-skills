---
name: digital-product-authoring
description: "Create and package digital products for sale — PDF generation (fpdf2), ZIP packaging (Python zipfile), Astro product page layouts, and managing product availability in the tools hub. Used for architecture templates, guides, playbooks, and toolkits."
version: 1.0.0
author: Hermes Agent
---

# Digital Product Authoring

## Overview

Build digital products (templates, guides, toolkits, playbooks) and publish them on montygroup.uk. Each product follows the same pipeline:
1. Create content files (Markdown, YAML, etc.)
2. Package assets (ZIP, PDF)
3. Build the product page
4. Register in the tools hub
5. Deploy

## Product Types

| Type | Example | Content Format | Pricing |
|------|---------|----------------|---------|
| **Template Pack** | ADR Template Pack | Markdown + YAML + ZIP | £19 |
| **PDF Guide** | Platform Engineering Playbook | fpdf2-generated PDF | £39 |
| **Toolkit Bundle** | WAF Review Toolkit | PDF + XLSX + ZIP | £29 |

## Content Creation

### Template Packs (ADR, Scorecards, etc.)

Create a set of files in `public/products/`:

```
public/products/adr-template-markdown.md    # Human-readable template
public/products/adr-template-yaml.yaml      # Machine-readable template  
public/products/adr-example-aks.md          # Worked example
public/products/adr-template-pack-readme.md # Usage instructions
```

File naming: `{product-slug}-{descriptor}.{ext}`

### ZIP Packaging

Use Python's `zipfile` module (avoid system `zip` command which may not be installed):

```python
import zipfile, os
files = ['adr-template-markdown.md', 'adr-template-yaml.yaml', ...]
with zipfile.ZipFile('adr-template-pack.zip', 'w') as z:
    for f in files:
        z.write(f, os.path.basename(f))  # strip dirs
```

### PDF Generation (fpdf2)

Use `fpdf2` via the Hermes venv (`source ~/.hermes/hermes-agent/venv/bin/activate`).

**IMPORTANT:** Use DejaVu Unicode fonts (available on most Linux systems) — the built-in Helvetica font cannot handle Unicode characters (em dashes, smart quotes, etc.).

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_font('DejaVu', '', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', uni=True)
pdf.add_font('DejaVu', 'B', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', uni=True)
pdf.add_font('DejaVu', 'I', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf', uni=True)
pdf.set_auto_page_break(auto=True, margin=20)
```

**Page layout methods:**

```python
def header(self):
    if self.page_no() > 1:
        self.set_font('DejaVu', 'I', 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, 'Product Name', align='L')
        self.cell(0, 8, f'Page {self.page_no()}', align='R')

def footer(self):
    self.set_y(-15)
    self.set_font('DejaVu', 'I', 8)
    self.set_text_color(150, 150, 150)
    self.cell(0, 10, '(c) 2026 MontyGroup', align='C')

def chapter_title(self, title):
    self.set_font('DejaVu', 'B', 16)
    self.set_text_color(30, 30, 30)
    self.multi_cell(0, 8, title)
    self.set_draw_color(100, 30, 180)  # Purple accent line
    self.set_line_width(0.5)
    self.line(10, self.get_y(), 100, self.get_y())
    self.ln(4)

def body_text(self, text):
    self.set_font('DejaVu', '', 10)
    self.set_text_color(60, 60, 60)
    self.set_x(10)  # Reset x to margin before each body_text call
    self.multi_cell(190, 5.5, text)  # Explicit width = 190 (A4 - 2*10mm margins)

def bullet(self, text):
    self.set_font('DejaVu', '', 10)
    self.set_text_color(60, 60, 60)
    self.set_x(10)  # CRITICAL: reset x position before multi_cell
    self.multi_cell(190, 5.5, "-  " + text)  # Prefix with bullet marker
```

**Pitfalls:**
- Always `self.set_x(10)` before `multi_cell()` or `bullet()` — fpdf2's internal x-position tracking can leave the cursor at a non-zero position after previous cells, causing "Not enough horizontal space" errors
- Replace em dashes (`—`), smart quotes, and other Unicode characters that the built-in Helvetica font can't handle. The DejaVu font handles all common Unicode
- `uni=True` is deprecated in fpdf2 v2.5.1+ — just omit it (DejaVu is auto-detected as Unicode)
- Title page: use `pdf.add_page()` then `pdf.ln(40)` for vertical centering, then set text with `align='C'` and `new_x='LMARGIN', new_y='NEXT'`
- `FPDF()` subclasses work best as a single class rather than multiple classes — place ALL styling (header, footer, chapter_title, body_text, bullet) in one class
- Title page uses larger fonts: `B, 28` for main title, `'', 14` for subtitle, `'', 11` for metadata

## Product Page Pattern

Each product gets an Astro page at `src/pages/tools/{slug}/index.astro`.

### Page Structure

```
Back link → Back to Tools
Hero section (icon, title, tagline, price, availability badge)
What's Included (feature cards grid — 3 per row)
Preview / code block if applicable
Why / value proposition section
Pricing CTA section (download button)
Footer
```

### Key components

```astro
<!-- Hero -->
<div class="section-card mb-6">
  <div class="flex items-start gap-4">
    <span class="text-4xl shrink-0">{icon}</span>
    <div>
      <h1 class="text-2xl font-bold text-lo-text mb-1">{title}</h1>
      <p class="text-lo-text-muted text-sm mb-3">{tagline}</p>
      <div class="flex flex-wrap items-center gap-3">
        <span class="text-2xl font-bold text-lo-primary">£{price}</span>
        <span class="badge bg-lo-success/10 text-lo-success">Available Now</span>
        <span class="badge bg-lo-primary/10 text-lo-primary">{category}</span>
      </div>
    </div>
  </div>
</div>

<!-- Feature cards (use content-card inside section-card) -->
<div class="section-card mb-6">
  <h2 class="section-card-header">📦 What's Included</h2>
  <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
    {features.map(f => (
      <div class="content-card">
        <div class="flex items-center gap-2 mb-1">
          <span>{f.icon}</span>
          <h3 class="font-semibold text-lo-text text-sm">{f.title}</h3>
        </div>
        <p class="text-xs text-lo-text-muted">{f.desc}</p>
      </div>
    ))}
  </div>
</div>

<!-- Pricing CTA -->
<div class="section-card mb-6 border-lo-primary/30 bg-lo-primary/5">
  <div class="text-center py-4">
    <h2 class="text-lg font-bold text-lo-text mb-1">Get the {title}</h2>
    <p class="text-sm text-lo-text-muted mb-4">Lifetime updates — buy once, get every future revision.</p>
    <span class="text-3xl font-bold text-lo-primary block mb-1">£{price}</span>
    <p class="text-xs text-lo-text-muted mb-4">{file description}</p>
    <a href="/products/{slug}.zip" class="inline-block px-8 py-3 rounded-lg bg-lo-primary text-white font-semibold hover:opacity-90 transition-opacity text-base no-underline">
      ⬇️ Download Now
    </a>
  </div>
</div>
```

## Registering in the Tools Hub

Edit `src/pages/tools/index.astro` — add/update entry in the `tools` array:

```javascript
{
  slug: 'product-slug',
  icon: '🎯',
  title: 'Product Name',
  tagline: 'Short value proposition',
  price: '£Price',
  category: 'Templates|Code|Guides|Spreadsheets',
  status: 'available',        // 'available' or 'coming-soon'
}
```

And create the product page at `src/pages/tools/{slug}/index.astro`.

**Status transitions:**
- `coming-soon` → styled as dimmed (`opacity-60`) with "Coming Soon" badge
- `available` → styled as full card with price, clickable, "Available Now" badge

## Verification

```bash
# Build
cd ~/dev-site && npm run build

# Check all prod pages in tools
for path in "/tools/" "/tools/{slug}/" "/products/{slug}.zip"; do
  curl -so /dev/null -w '%{http_code}' "https://montygroup.uk$path" && echo " $path"
done
```

## References

| File | Content |
|------|---------|
| `references/template-pack-pattern.md` | Standard file structure for template packs (Markdown + YAML + example + readme + ZIP) |
| `references/pdf-playbook-pattern.md` | Full fpdf2 Python script structure for generating multi-chapter PDF guides |
