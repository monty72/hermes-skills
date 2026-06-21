# PDF Playbook Pattern

Full fpdf2 Python script structure for generating multi-chapter PDF guides.

## Script Structure

```python
#!/usr/bin/env python3
from fpdf import FPDF
import os

class PlaybookPDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font('DejaVu', 'I', 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 8, 'Guide Title', align='L')
            self.cell(0, 8, f'Page {self.page_no()}', align='R',
                       new_x='LMARGIN', new_y='NEXT')
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font('DejaVu', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, '(c) 2026 MontyGroup - montygroup.uk', align='C')

    def chapter_title(self, title):
        self.set_font('DejaVu', 'B', 16)
        self.set_text_color(30, 30, 30)
        self.ln(4)
        self.multi_cell(0, 8, title)
        self.ln(2)
        self.set_draw_color(100, 30, 180)  # Purple accent
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 100, self.get_y())
        self.ln(4)

    def section_title(self, title):
        self.set_font('DejaVu', 'B', 12)
        self.set_text_color(60, 60, 60)
        self.ln(2)
        self.set_x(10)
        self.multi_cell(190, 7, title)
        self.ln(1)

    def body_text(self, text):
        self.set_font('DejaVu', '', 10)
        self.set_text_color(60, 60, 60)
        self.set_x(10)  # CRITICAL: reset x before multi_cell
        self.multi_cell(190, 5.5, text)
        self.ln(2)

    def bullet(self, text):
        self.set_font('DejaVu', '', 10)
        self.set_text_color(60, 60, 60)
        self.set_x(10)  # CRITICAL: reset x before multi_cell
        self.multi_cell(190, 5.5, "-  " + text)

# Instantiate
pdf = PlaybookPDF()
pdf.add_font('DejaVu', '', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', uni=True)
pdf.add_font('DejaVu', 'B', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', uni=True)
pdf.add_font('DejaVu', 'I', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf', uni=True)
pdf.set_auto_page_break(auto=True, margin=20)

# Title page
pdf.add_page()
pdf.ln(40)  # Vertical centering
pdf.set_font('DejaVu', 'B', 28)
pdf.set_text_color(100, 30, 180)
pdf.cell(0, 15, 'Main Title', align='C', new_x='LMARGIN', new_y='NEXT')
pdf.cell(0, 15, 'Subtitle', align='C', new_x='LMARGIN', new_y='NEXT')
pdf.ln(10)
pdf.set_font('DejaVu', '', 14)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 10, 'Tagline line 1', align='C', new_x='LMARGIN', new_y='NEXT')
pdf.cell(0, 10, 'Tagline line 2', align='C', new_x='LMARGIN', new_y='NEXT')
pdf.ln(20)
pdf.set_font('DejaVu', '', 11)
pdf.set_text_color(150, 150, 150)
pdf.cell(0, 8, 'Author Name', align='C', new_x='LMARGIN', new_y='NEXT')
pdf.cell(0, 8, 'URL or reference', align='C', new_x='LMARGIN', new_y='NEXT')
pdf.cell(0, 8, 'Version - Date', align='C', new_x='LMARGIN', new_y='NEXT')

# Chapters (use data-driven approach)
chapters = [
    ('1. Chapter Title', 'Context paragraph', ['Bullet 1', 'Bullet 2'], 'Extra paragraph'),
    # ...
]
for title, ctx, bullets, extra in chapters:
    pdf.add_page()
    pdf.chapter_title(title)
    if ctx:
        pdf.body_text(ctx)
    for b in bullets:
        pdf.bullet(b)
    if extra:
        pdf.ln(2)
        pdf.body_text(extra)

# Output
out_path = os.path.expanduser('~/dev-site/public/products/{slug}.pdf')
pdf.output(out_path)
print(f"Created: {out_path} ({pdf.page_no()} pages)")
```

## Key Rules

1. **Always `set_x(10)` before `multi_cell`** — fpdf2's x tracking can leave the cursor mid-page, causing "Not enough horizontal space" errors
2. **Use explicit width `190`** (A4 = 210mm width, 10mm margins each side = 190mm usable)
3. **Use DejaVu Sans** for Unicode support (em dashes, smart quotes, copyright symbols)
4. **Replace special characters** — use `-` not `\u2014`, `(c)` not `\u00a9`
5. **Data-driven chapters** — use a list of tuples rather than repeating code
6. **Title page uses `new_x='LMARGIN', new_y='NEXT'`** — essential for fpdf2 cursor positioning
7. **Vertical centering on title page** — `pdf.ln(40)` before title, not after
