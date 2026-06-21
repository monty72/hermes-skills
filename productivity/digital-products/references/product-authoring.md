# Digital Product Authoring — Creation Guide

Full pipeline for creating digital products.

## Product Types

| Type | Example | Content Format | Pricing |
|------|---------|----------------|---------|
| Template Pack | ADR Template Pack | Markdown + YAML + ZIP | £19 |
| PDF Guide | Platform Engineering Playbook | fpdf2-generated PDF | £39 |
| Toolkit Bundle | WAF Review Toolkit | PDF + XLSX + ZIP | £29 |

## Content Creation

Files go in `public/products/`:
```
public/products/adr-template-markdown.md
public/products/adr-template-yaml.yaml
public/products/adr-example-aks.md
public/products/adr-template-pack-readme.md
```

## ZIP Packaging

```python
import zipfile, os
with zipfile.ZipFile('adr-template-pack.zip', 'w') as z:
    for f in files:
        z.write(f, os.path.basename(f))
```

## PDF Generation (fpdf2)

Use DejaVu Unicode fonts for proper character support:

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_font('DejaVu', '', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', uni=True)
pdf.add_font('DejaVu', 'B', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', uni=True)
pdf.set_auto_page_break(auto=True, margin=20)
```

**Pitfalls:**
- Always `pdf.set_x(pdf.l_margin)` before `multi_cell()` — prevents "Not enough horizontal space" errors
- Place ALL styling (header, footer, body_text, bullet) in one FPDF subclass

## Product Page Pattern

Each product gets an Astro page at `src/pages/tools/{slug}/index.astro`:

```
Back link → Back to Tools
Hero section (icon, title, tagline, price, availability badge)
What's Included (feature cards grid — 3 per row)
Pricing CTA section (download button)
```

## Verification

```bash
cd ~/dev-site && npm run build
for path in "/tools/" "/tools/{slug}/" "/products/{slug}.zip"; do
  curl -so /dev/null -w '%{http_code}' "https://montygroup.uk$path"
done
```
