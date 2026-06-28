---
name: drawio-file-manipulation
description: Programmatically read, parse, and modify diagrams.net (.drawio) files by working with the XML format directly. Covers file structure, cell injection, edge creation, and validation.
---

# Drawio File Manipulation

Programmatic modification of diagrams.net (formerly draw.io) files via XML injection. Use when a user needs to add nodes/edges to an existing diagram without opening the GUI, or when automated diagram generation from templates is required.

## File Format

A `.drawio` file is XML in one of two formats:

| Format | Characteristics | How to Detect |
|--------|----------------|---------------|
| **Uncompressed** | Plain XML — `<mxGraphModel><root>` with `<mxCell>` elements | Contains `<diagram>` with literal `<mxGraphModel>` inside |
| **Compressed** | Diagram content is base64-encoded, deflate-compressed XML | `<diagram>` content starts with base64 chars, not XML |

### Uncompressed Structure

```xml
<mxfile host="..." agent="..." version="...">
  <diagram name="Page 1" id="...">
    <mxGraphModel dx="..." dy="..." grid="0" gridSize="10" ...>
      <root>
        <mxCell id="0" />                          <!-- Root cell -->
        <mxCell id="1" value="ALZ Hub &amp; Spoke" parent="0" />  <!-- Diagram root -->
        
        <!-- Node (vertex) -->
        <mxCell id="cell-3" value="My Service" style="rounded=1;whiteSpace=wrap;html=1;"
                vertex="1" parent="1">
          <mxGeometry x="100" y="200" width="280" height="50" as="geometry" />
        </mxCell>
        
        <!-- Edge (connector) -->
        <mxCell id="cell-4" style="edgeStyle=orthogonalEdgeStyle;rounded=0;"
                edge="1" parent="1" source="cell-3" target="cell-5">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

### Multi-Page Files

Multiple `<diagram>` elements inside the same `<mxfile>`:
- `pages="2"` attribute on `<mxfile>` indicates multiple pages
- Each page is a separate `<diagram>` with its own `<mxGraphModel><root>` and independent cells
- Cell IDs DO NOT need to be unique across pages (each page has its own namespace), but using globally unique IDs is safer

## Core Cell Types

### Vertex (Node Box)

```xml
<mxCell id="unique-id" value="Label Text" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#0078d4;fontColor=#FFFFFF;"
        vertex="1" parent="diagram-root-id">
  <mxGeometry x="100" y="200" width="280" height="50" as="geometry" />
</mxCell>
```

| Attribute | Purpose | Notes |
|-----------|---------|-------|
| `id` | Unique cell identifier | Must be unique within diagram |
| `value` | Display label | HTML entities: `&lt;` `<`, `&gt;` `>`, `&amp;` `&` |
| `style` | Visual properties | Semicolon-delimited key=value pairs |
| `vertex="1"` | Marks as a node | Required for shapes |
| `parent` | Parent cell | Usually the diagram root cell ID |
| `edge="1"` | Marks as an edge/connector | Required for arrows |

### Style Properties (Common)

| Property | Values | Example |
|----------|--------|---------|
| `rounded` | `0` or `1` | `rounded=1` |
| `whiteSpace` | `wrap` | `whiteSpace=wrap` |
| `html` | `1` | `html=1` |
| `fillColor` | Hex color | `fillColor=#0078d4` |
| `fontColor` | Hex color | `fontColor=#FFFFFF` |
| `strokeColor` | Hex color | `strokeColor=#FF0000` |
| `strokeWidth` | Number | `strokeWidth=2` |
| `fontSize` | Number | `fontSize=14` |
| `fontStyle` | `1` (bold) | `fontStyle=1` |
| `dashed` | `1` | `dashed=1` |
| `dashPattern` | `8 8` | `dashPattern=8 8` |
| `verticalAlign` | `middle`, `top`, `bottom` | `verticalAlign=middle` |
| `align` | `center`, `left`, `right` | `align=center` |

### Edge (Connector Arrow)

```xml
<mxCell id="arrow-1" style="edgeStyle=orthogonalEdgeStyle;rounded=0;strokeWidth=2;entryX=0.5;entryY=0;exitX=0.5;exitY=1;"
        edge="1" parent="diagram-root-id" source="source-cell-id" target="target-cell-id">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
```

| Attribute | Purpose |
|-----------|---------|
| `source` | Cell ID of the source node |
| `target` | Cell ID of the target node |
| `entryX/entryY` | Entry point on target (0-1, 0.5=center) |
| `exitX/exitY` | Exit point on source (0-1, 0.5=center) |
| `edgeStyle` | Routing style: `orthogonalEdgeStyle` (default), `curved`, `elbow` |

## Injection Technique

### Strategy

1. **Read file** — load the XML into a string
2. **Locate the target diagram** — split on `<diagram name="..."` and find the one to modify
3. **Find the `</root>` tag** within that diagram section — this is the insertion point
4. **Generate new cells** — nodes (vertex), edges, labels, boundary boxes
5. **Inject** — insert new cell XML before `</root>`
6. **Verify** — check count of flow- elements, validate XML structure

### ID Generation

Cells must have unique IDs within the same diagram. Pattern: scan existing IDs for a numeric suffix prefix, then increment:

```python
import re

# Find max numeric suffix from existing cell IDs
max_num = 0
for cid in all_cell_ids:
    m = re.search(r'GU-(\d+)$', cid)  # or any prefix pattern
    if m:
        n = int(m.group(1))
        max_num = max(max_num, n)

# Generate new IDs starting from max_num + 1
NEXT = max_num + 1
```

**Common ID prefixes in drawio files:**
- `yvAwWkkrhjme5IgpjQKr-{N}` — randomly generated base64-ish
- `qyepl6iVJ43P_be80-GU-{N}` — randomly generated
- Custom: `flow-{N}` (self-injected cells)

### Complete Injection Script Pattern

```python
#!/usr/bin/env python3
"""Inject new cells into a drawio diagram."""

import re
from pathlib import Path

SRC = Path("/path/to/input.drawio")
DST = Path("/path/to/output.drawio")

raw = SRC.read_text()

# Split on target diagram
parts = raw.split('<diagram name="Target Page Name"', 1)
before = parts[0]
rest = '<diagram name="Target Page Name"' + parts[1]

# Find the closing </root> in this diagram's section
root_end = re.search(r'(</root>\s*\n\s*</mxGraphModel>\s*\n\s*</diagram>)', rest)
root_close_pos = root_end.start(1)

# Find max existing cell ID numeric suffix
cell_ids = re.findall(r'id="([^"]+)"', rest[:root_close_pos])
max_num = 0
for cid in cell_ids:
    m = re.search(r'GU-(\d+)$', cid)  # adjust prefix to match your file
    if m:
        max_num = max(max_num, int(m.group(1)))

N = max_num + 1

# Define nodes as (label, x, y, width, height, style)
nodes = [
    ("Service A", 100, 200, 280, 50,
     "rounded=1;whiteSpace=wrap;html=1;fillColor=#0078d4;fontColor=#FFFFFF;fontSize=14;"),
    ("Service B", 100, 300, 280, 50,
     "rounded=1;whiteSpace=wrap;html=1;fillColor=#D32F2F;fontColor=#FFFFFF;fontSize=14;"),
]

parent_id = "qyepl6iVJ43P_be80-GU-1"  # diagram root cell ID in this file

# Build node cells
new_cells = []
for i, (label, x, y, w, h, style) in enumerate(nodes):
    cid = f"qyepl6iVJ43P_be80-flow-{i}"
    new_cells.append(f"""        <mxCell id="{cid}" value="{label}" style="{style}" vertex="1" parent="{parent_id}">
          <mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" />
        </mxCell>""")

# Build arrow edges
for i in range(len(nodes) - 1):
    src = f"qyepl6iVJ43P_be80-flow-{i}"
    tgt = f"qyepl6iVJ43P_be80-flow-{i+1}"
    arrow_style = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;entryX=0.5;entryY=0;exitX=0.5;exitY=1;strokeWidth=2;"
    new_cells.append(f"""        <mxCell id="qyepl6iVJ43P_be80-flow-arrow-{i}" style="{arrow_style}" edge="1" parent="{parent_id}" source="{src}" target="{tgt}">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>""")

# Add section labels and boundary boxes
new_cells.append(f"""        <mxCell id="qyepl6iVJ43P_be80-flow-boundary" value="Boundary Label" style="rounded=1;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 8;fillColor=#E8F5E9;strokeColor=#2E7D32;strokeWidth=2;fontSize=14;fontColor=#2E7D32;verticalAlign=bottom;align=left;" vertex="1" parent="{parent_id}">
          <mxGeometry x="80" y="180" width="320" height="200" as="geometry" />
        </mxCell>""")

# Inject: insert before the closing </root>
injection = "\n".join(new_cells) + "\n"
updated_rest = rest[:root_close_pos] + "\n" + injection + rest[root_close_pos:]
output = before + updated_rest
DST.write_text(output)
print(f"Written to {DST}")
```

## Validation

### Basic Check

```bash
grep -c "flow-" output.drawio        # Count injected elements
grep "flow-0" output.drawio           # Verify specific cell exists
```

### XML Validity

```python
import xml.etree.ElementTree as ET
tree = ET.parse("output.drawio")
root = tree.getroot()
diagrams = root.findall("diagram")
print(f"Diagrams: {len(diagrams)}")
print(f"Ends with </mxfile>: {open('output.drawio').read().strip().endswith('</mxfile>')}")
```

> ⚠️ `xml.etree.ElementTree` parses the outer `<mxfile>` structure correctly but diagram content is raw XML text within `<diagram>` tags — `.text` may not expose injected elements from parse trees. Always also do raw string checks.

## Edge Cases

### 1. Second Diagram Modification

When modifying a multi-page file, split on the `<diagram name="Page Name"` tag of the target page. The first page is everything before the match, the second page is the match + everything after:

```python
parts = raw.split('<diagram name="Page 2">', 1)
```

### 2. Compressed Diagrams

If the `<diagram>` content starts with base64 characters (not `<mxGraphModel>`), the diagram is compressed:

```python
import base64, zlib

# Inside the diagram tag
compressed = b64_content.encode('ascii')
# Strip whitespace/newlines from base64
compressed = base64.b64decode(compressed)
xml_text = zlib.decompress(compressed, -zlib.MAX_WBITS).decode('utf-8')

# Modify xml_text
# Recompress
compressed_back = base64.b64encode(zlib.compress(xml_text.encode('utf-8'))).decode('ascii')
```

Detect compressed vs uncompressed:
```python
is_compressed = not diagram_content.strip().startswith('<')
```

### 3. HTML in Labels (Critical — Must Use HTML Encoding)

Drawio's XML uses HTML entities within the `value` attribute for ALL text rendering. **Literal `\n` (newlines) inside the `value` attribute do NOT render as line breaks** — you must use `&lt;br&gt;` tags inside a wrapping `&lt;div&gt;`.

**DON'T** (plain newlines — will NOT render correctly):
```xml
<!-- ❌ Broken: newline chars in attribute are ignored by drawio -->
<mxCell id="cell-1" value="Line 1
Line 2" vertex="1" ...>
```

**DO** (HTML-encoded div + br):
```xml
<!-- ✅ Correct: HTML-encoded line breaks -->
<mxCell id="cell-1" value="&lt;div&gt;Line 1&lt;br&gt;Line 2&lt;/div&gt;" vertex="1" ...>
```

**Python helper:**
```python
import html

def drawio_label(text):
    """Convert plain text (with \\n) to drawio HTML-encoded value."""
    text_br = text.replace('\n', '<br>')
    escaped = html.escape(text_br)
    return f'&lt;div&gt;{escaped}&lt;/div&gt;'

# Usage
label = drawio_label("Hub Firewall\n(Connectivity Sub)")
# Returns: &lt;div&gt;Hub Firewall&lt;br&gt;(Connectivity Sub)&lt;/div&gt;
```

HTML markup cheat sheet:

| Render result | Value attribute |
|--------------|----------------|
| Bold text | `&lt;b&gt;Text&lt;/b&gt;` |
| Line break | `&lt;br&gt;` |
| Colored span | `&lt;font style=&quot;color:#FF0000;&quot;&gt;red&lt;/font&gt;` |
| Nested layout | `&lt;div&gt;...&lt;/div&gt;` wrapping everything |
| Non-breaking space | `&amp;nbsp;` |

> ⚠️ **Why `\n` fails:** XML attribute values can contain literal newlines (they're valid XML), but drawio's layout engine strips or ignores them. The HTML rendering engine (`html=1`) only interprets HTML tags, not whitespace. Always wrap multiline labels in `&lt;div&gt;...&lt;br&gt;...&lt;/div&gt;`.

### 4. Text-Only Elements (Standalone Labels)

For labels, titles, and boundary-names that float **over** or **inside** boundary boxes (not inside a shape), use `style="text;html=1;..."` with `vertex="1"`:

```xml
<mxCell id="label-1" value="&lt;b&gt;Section Title&lt;/b&gt;"
        style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=top;whiteSpace=wrap;rounded=0;fontSize=12;fontColor=#333333;fontStyle=1"
        vertex="1" parent="diagram-root-id">
  <mxGeometry x="100" y="100" width="200" height="20" as="geometry" />
</mxCell>
```

| Style property | Purpose |
|----------------|---------|
| `text` | Marks as text-only (no shape background) |
| `strokeColor=none` | No border |
| `fillColor=none` | Transparent background |
| `align` | Horizontal: `left`, `center`, `right` |
| `verticalAlign` | Vertical: `top`, `middle`, `bottom` |

Use text elements for:
- Section headers above a flow
- Boundary zone labels (e.g. "Connectivity Subscription" overlaid on a dashed box)
- Direction annotations
- Legend items

### 5. Coordinate Range & Visibility

When placing new elements into an existing diagram, **check the existing element coordinates first** to ensure your new elements will be visible:

```python
# Scan existing element positions
import re
positions = re.findall(r'<mxGeometry x="(\d+)" y="(\d+)"', diag2_content)
xs = [int(p[0]) for p in positions]
ys = [int(p[1]) for p in positions]
print(f"Existing X range: {min(xs)}-{max(xs)}, Y range: {min(ys)}-{max(ys)}")
```

Place new elements within or just beyond these ranges. Avoid placing elements at extreme coordinates far from existing content — drawio will render them but they'll be off-screen when the file first opens (stuck at default zoom/pan).

### 6. Clean Re-Injection (Removing Previous Blocks)

When re-injecting into the same diagram (e.g. fixing positions/labels), you must remove **entire blocks** — not just the `<mxCell>` lines — because each block spans 3+ lines:

```xml
<mxCell id="flow-0" value="..." ...>           <!-- has target string -->
  <mxGeometry x="100" y="200" ... />           <!-- no target string -->
</mxCell>                                       <!-- no target string -->
```

**Wrong approach:** filtering lines by the target string will remove the `<mxCell>` line but leave orphaned `<mxGeometry>` and `</mxCell>` tags — breaking XML parsing.

**Correct approach:** track state through each block:

```python
lines = content.split('\n')
new_lines = []
skip = False
for line in lines:
    if 'flow-' in line:
        skip = True                  # start skipping
        continue
    if skip and '</mxCell>' in line:
        skip = False                 # end of block
        continue
    if not skip:
        new_lines.append(line)
```

Or, even simpler: **regenerate from the original source file** if you have it. Keep the source file intact and always inject fresh on a clean copy.

### 7. Boundary Boxes (Dashed Zones)

Use dashed rounded rectangles to draw subscription/resource-group/region boundaries:

```xml
<mxCell id="boundary-1" value="Zone Label" style="rounded=1;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 8;fillColor=#E8F5E9;strokeColor=#2E7D32;strokeWidth=2;fontSize=14;fontColor=#2E7D32;verticalAlign=bottom;align=left;" vertex="1" parent="diagram-root-id">
  <mxGeometry x="x" y="y" width="w" height="h" as="geometry" />
</mxCell>
```

For boundary boxes that shouldn't clip their label, set the label in the box's `value` with `verticalAlign=bottom;align=left` — the label sits at the top-left inside the box stroke. Alternatively, use a separate text element (section 4) overlaid on the box for independent positioning.

### 8. Large Files (5MB+)

Files with embedded base64 PNG stencils (from Visio imports) can be very large. The actual diagram structure is a small fraction of the total size. When editing:
- Read the full file into memory
- Work with string operations, not DOM parsers
- Inject new cells in the target diagram's root section only
- Don't try to parse/modify stencil definitions

### 9. Parent Group Coordinate Offsets

When cells are nested inside a group container (e.g. `parent="GU-443"`), their `mxGeometry` x/y coordinates are **relative to that group's position**, not absolute to the diagram canvas:

```python
# Group container GU-443 is at (3651, 722) in the diagram
# A cell inside it with x=612, y=585 renders at:
#   absolute_x = 3651 + 612 = 4263
#   absolute_y = 722 + 585 = 1307
```

To find a cell's absolute position, trace its parent chain:
1. Find the cell's geometry: `mxGeometry x="612" y="585"`
2. Find its parent's geometry and add offsets
3. Repeat up to the diagram root (usually `GU-1` or ID `1`)

**When placing new cells inside a group**, ensure the parent attribute points to the group ID, not the diagram root:

```python
# ❌ Wrong — placed at absolute coords, parent is diagram root
parent="qyepl6iVJ43P_be80-GU-1", x="3651+612"

# ✅ Correct — placed relative to group container
parent="qyepl6iVJ43P_be80-GU-443", x="612"
```

### 9b. Visio-Imported Groups: `connectable="0"` Restriction

Many drawio files imported from Visio use **group containers** with `connectable="0"` (e.g. `style="group" parent="..." connectable="0" vertex="1"`). This prevents edges outside the group from connecting to cells inside it — standard `source`/`target` edge references **will not render**.

**Detection:** Check the parent group's attributes:
```python
import re
m = re.search(r'connectable="0"', diagram_section)
if m:
    print("⚠ connectable=0 groups present — edges via source/target may be blocked")
```

**Workaround — Explicit Coordinate Paths (Polylines):** Instead of using `source` and `target` attributes, use an `Array as="points"` with explicit `mxPoint` entries to define the edge's path:

```xml
<mxCell id="arrow-1" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeWidth=2;strokeColor=#0078d4;"
        edge="1" parent="diagram-root-id">
  <mxGeometry relative="1" as="geometry">
    <Array as="points">
      <mxPoint x="3473" y="418" />
      <mxPoint x="3473" y="600" />
      <mxPoint x="4850" y="600" />
      <mxPoint x="4850" y="1510" />
    </Array>
  </mxGeometry>
</mxCell>
```

**Coordinate calculation:** When connecting to cells inside a locked group, calculate the **absolute coordinates** by adding parent group offsets (see section 9). Point the polyline to those absolute positions.

**Entry/Exit behavior:** Without `source`/`target`, entry/exit points (`entryX`/`exitX` and `entryY`/`exitY`) are ignored. The polyline's last point is the arrow tip. Ensure the final segment aligns with where you want the arrowhead.

**Fallback order:**
1. ✅ `source`/`target` — works when cells are GU-1 children or groups WITHOUT `connectable="0"`
2. ❌ `source`/`target` — FAILS when cells are inside `connectable="0"` groups
3. ✅ Explicit `Array as="points"` polyline — always works

### 9c. Self-Closing Tags & Balance Checking

**Don't use naive tag counting to validate drawio XML.** Self-closing tags (e.g. `<mxCell id="x" ... />`) close themselves — they don't produce `</mxCell>` closings. A file with many self-closing tags will show `N opens ≠ N closes` and that's expected.

**Use XML parser validation instead:**
```python
import xml.etree.ElementTree as ET
try:
    ET.fromstring(content)
    print("✓ XML valid")
except ET.ParseError as e:
    print(f"✗ XML error: {e}")
```

### 10. Connecting Existing Objects (Preference)

**When the user asks to add a flow path to an existing diagram, prefer connecting existing objects with arrows over creating new boxes.** This keeps the diagram clean and maintains its original design language.

**Workflow:**

1. **Inventory existing objects** — Scan the diagram's `value` attributes to find relevant labels. Match each step of the requested flow to an existing diagram element.

2. **Get cell IDs** — Find the `id` attribute of each matching `mxCell`:

```python
# Search for cell by label
for m in re.finditer(r'<mxCell[^>]*value="[^"]*My Label[^"]*"[^>]*>', content):
    cid = re.search(r'id="([^"]+)"', m.group(0)).group(1)
```

3. **Create edge cells** — Use `source` and `target` attributes pointing to existing cell IDs. No new vertex cells needed:

```python
edge = f'''<mxCell id="new-arrow-1"
    style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;entryX=0.5;entryY=0;exitX=0.5;exitY=1;strokeWidth=2;"
    edge="1" parent="diagram-root-id"
    source="existing-cell-A"
    target="existing-cell-B">
  <mxGeometry relative="1" as="geometry" />
</mxCell>'''
```

4. **Add minimal annotation only** — Use text labels for section headers and small callout boxes for gaps/issues. Do NOT create new service/subnet/component boxes that duplicate existing content.

5. **Check positions with geometry** — Before connecting, verify coordinates make sense for a clean arrow path. If existing objects are in different parent groups, the arrow may cross the diagram awkwardly. In that case, consider the arrow's visual path or ask the user.

**Example — adding a flow path to an existing architecture diagram:**

```
Request: "Add Copilot Studio → MCP flow to the diagram"

✅ Correct approach:
  - Find existing "Internet" object → add arrow → existing "HTTPS" object
  - Find existing "Azure Firewall" → add arrow → existing "PE" → existing "MCP"
  - Add a KEY GAP annotation note where the flow is incomplete
  - Add boundary boxes (dashed) for subscription scope
  - Zero new service boxes created

❌ Wrong approach:
  - Create "Copilot Studio (SaaS)" box
  - Create "Custom Connector" box  
  - Create "Hub Firewall" box ← duplicates existing Azure Firewall
  - Create "MCP Server" box ← duplicates existing MCP icon
  - The diagram ends up with duplicate representations of the same services
```

### 11. Iteration Strategy for Drawio Edits

When the user says "I can't see the update" or requests changes:

1. **Regenerate from original source** — Keep a copy of the original file. Instead of patching an already-injected file, always inject fresh into the clean original. This avoids orphaned tags, duplicate IDs, and cascading format errors.

2. **Validate XML after every change** — Use `xml.etree.ElementTree` to parse the output:
   ```python
   import xml.etree.ElementTree as ET
   ET.fromstring(output)  # raises ParseError on malformed XML
   ```

3. **Check element counts** — Count injected elements in the target diagram:
   ```bash
   grep -c "my-prefix-" output.drawio
   ```

4. **Verify with the user** — Push to GitHub and ask them to open in diagrams.net. Positions and visual rendering are hard to verify from XML alone.

## Known Pitfalls

1. **ID collision** — New cell IDs must not match existing ones. Always scan existing IDs first and use an increment pattern.
2. **Wrong parent ID** — Every cell needs the correct `parent` attribute pointing to the diagram's root cell. The diagram root cell is usually ID `1` or `qyepl6iVJ43P_be80-GU-1` (child of cell `0`).
3. **Edge source/target** — Both source and target cell IDs must exist in the diagram or the edge won't render.
4. **XML escaping** — Label values containing `<`, `>`, `&` must use HTML entities. Drawio uses `&lt;`/`&gt;`/`&amp;` even in the XML attribute `value="..."`.
5. **`execute_code` sandbox** — Cannot run scripts that write files. Use `write_file` + `terminal()` instead.
