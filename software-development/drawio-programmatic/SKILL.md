---
name: drawio-programmatic
description: >-
  Read, analyze, and modify drawio (diagrams.net) XML files programmatically
  — parse diagram structure, extract nodes/edges/labels, inject new cells.
  Covers drawio XML format, mxGraphModel structure, stencil decoding, and
  reliable cell injection patterns.
---

# Drawio Programmatic Manipulation

Read, analyze, and inject new elements into drawio XML files without opening diagrams.net.

## Drawio XML Structure

A `.drawio` file is an XML document with this skeleton:

```xml
<mxfile host="..." agent="..." version="..." pages="N">
  <diagram name="Page Name" id="...">
    <mxGraphModel dx="..." dy="..." grid="0" ...>
      <root>
        <mxCell id="0" />                          <!-- root cell -->
        <mxCell id="1" parent="0" value="Canvas" /> <!-- canvas cell -->
        ...cells...
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

### Cell Types

| Type | Tag | Key Attributes |
|------|-----|---------------|
| **Shape / Vertex** | `<mxCell>` | `vertex="1"` — value, style, geometry |
| **Edge / Connector** | `<mxCell>` | `edge="1"` — source, target, style |
| **UserObject** | `<UserObject>` → `<mxCell>` | Wraps a cell with tags/labels; the inner `<mxCell>` has the actual geometry/style |

### Cell IDs

- Root ID must be unique per diagram (e.g. `yvAwWkkrhjme5IgpjQKr-0`, `qyepl6iVJ43P_be80-GU-0`)
- Second cell (canvas) has `parent="<root_id>"` and `value="Some Name"` (usually the architecture name)
- All content cells have `parent="<canvas_id>"` or are nested as children of a container cell

### Key Attributes on Geometry

```xml
<mxGeometry x="100" y="200" width="300" height="50" as="geometry" />
```

- `x`, `y` — position (pixels from top-left)
- `width`, `height` — dimensions
- `relative="1"` — used on edge geometries
- For edges: `<mxPoint x="..." y="..." as="sourcePoint"/>` / `targetPoint`

### Important: Stencils vs Simple Shapes

Drawio files created via **Visio/VSDX import** use `shape=stencil(base64...)` for shapes. These are Visio stencils rendered as inline vector definitions — you CANNOT create them from scratch via injection. You can only inject **simple shapes** (rectangles, rounded rectangles, text labels) and **edges** (arrows, connectors).

**Stencil shapes look like:**
```xml
<mxCell style="fillColor=#0078d4;shape=stencil(nZBLDoAgDERP0z3SIy...);..." vertex="1">
```

**Simple shapes (what you should inject):**
```xml
<mxCell id="my-cell-1" value="Label Text" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#0078d4;fontColor=#FFFFFF;" vertex="1" parent="canvas-id">
  <mxGeometry x="100" y="200" width="280" height="50" as="geometry" />
</mxCell>
```

## Reading a Drawio File

### 1. Load and find diagrams

When the user sends a `.drawio` file (possibly renamed as `.txt`), check its size immediately — drawio files with embedded base64 stencils can be 2-10+ MB.

```python
# Read raw content (truncation possible on large files)
from xml.etree import ElementTree as ET
tree = ET.parse("file.drawio")
root = tree.getroot()
for d in root.findall("diagram"):
    print(d.get("name"), d.get("id"))
```

For files over ~5MB, use `grep` or regex to find diagrams rather than loading the full tree:

```bash
grep -o '<diagram name="[^"]*"' file.drawio
```

### 2. Extract the ALZ hierarchy

Management groups are typically boxes labeled with `<b>Management groups</b>`. Find them by searching for `value` attributes in the XML containing "Management group" or similar text:

```python
import re
with open("file.drawio") as f:
    content = f.read()
# Find text labels
labels = re.findall(r'value="[^"]*Management group[^"]*"', content)
```

### 3. Understand the 2-diagram pattern

Some drawios put the same ALZ layout on **both pages** — Page 1 as the clean reference, Page 2 as the editable overlay where you add your specific flow. Check for this pattern:

```python
parts = content.split('<diagram name="', 3)
for i in range(1, min(3, len(parts))):
    name = parts[i].split('"')[0]
```

### 4. Handle the `</root>` boundary

Each diagram's root section ends with `</root>\n    </mxGraphModel>\n  </diagram>`. This is the injection point for new cells.

```python
root_close = content.rfind('</root>')
# Everything before = existing diagram XML
# Insert new cells here, then append the closing tags
```

## Injecting New Cells Into Drawio XML

### Strategy

1. **Identify the target diagram** — match by name
2. **Find the max numeric cell ID** — scan all `id="*GU-(\d+)"` patterns to avoid collisions
3. **Build new cells** — simple rectangles + edges only (no stencils)
4. **Insert before the target diagram's `</root>`** tag
5. **Write the updated file** with `.drawio` extension

### Step-by-step Script Pattern

```python
import re

with open("input.drawio") as f:
    content = f.read()

# 1. Split at the target diagram
parts = content.split('<diagram name="Target Diagram Name"', 1)
before = parts[0]
rest = '<diagram name="Target Diagram Name"' + parts[1]

# 2. Find max cell ID in that diagram
ids = re.findall(r'id="[^"]*?-(\d+)"', rest[:rest.find('</root>')])
max_id = max(int(n) for n in ids) if ids else 0

# 3. Build new cells
canvas_id = "parent-canvas-id"  # The id=1 cell in the target diagram
new_cells = []

# Nodes (simple rounded rectangles)
nodes = [
    ("Label 1", 100, 200, 280, 50, "rounded=1;whiteSpace=wrap;html=1;fillColor=#0078d4;fontColor=#FFFFFF;"),
    ("Label 2", 100, 300, 280, 50, "rounded=1;whiteSpace=wrap;html=1;fillColor=#D32F2F;fontColor=#FFFFFF;"),
]
for i, (label, x, y, w, h, style) in enumerate(nodes):
    cid = f"flow-injected-{i}"
    new_cells.append(f"""<mxCell id="{cid}" value="{label}" style="{style}" vertex="1" parent="{canvas_id}">
  <mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" />
</mxCell>""")

# Arrows (vertical by default)
for i in range(len(nodes) - 1):
    src = f"flow-injected-{i}"
    tgt = f"flow-injected-{i+1}"
    style = "edgeStyle=orthogonalEdgeStyle;rounded=0;entryX=0.5;entryY=0;exitX=0.5;exitY=1;strokeWidth=2;"
    new_cells.append(f"""<mxCell id="flow-injected-arrow-{i}" style="{style}" edge="1" parent="{canvas_id}" source="{src}" target="{tgt}">
  <mxGeometry relative="1" as="geometry" />
</mxCell>""")

# Boundaries (dashed boxes around service groups)
new_cells.append(f"""<mxCell id="flow-boundary-0" value="Group Name" style="rounded=1;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 8;fillColor=#E8F5E9;strokeColor=#2E7D32;strokeWidth=2;verticalAlign=bottom;align=left;" vertex="1" parent="{canvas_id}">
  <mxGeometry x="80" y="250" width="320" height="150" as="geometry" />
</mxCell>""")

# 4. Inject before </root>
injection = "\n".join(new_cells)
insert_point = rest.rfind('</root>')
updated_rest = rest[:insert_point] + "\n" + injection + "\n" + rest[insert_point:]

# 5. Write
output = before + updated_rest
with open("output.drawio", "w") as f:
    f.write(output)
```

### Caveats

- **Drawio ID collision**: Always compute max ID first. Don't use hardcoded IDs.
- **File encoding**: drawio files are UTF-8. Embedded base64 is safe to read/write as text.
- **Stencil vs simple**: You can ONLY inject simple shapes (`rounded=1`, `rectangle`, `text`). You cannot inject Visio stencil shapes programmatically.
- **Self-closing vs paired tags**: Drawio XML uses BOTH self-closing `<mxCell ... />` AND paired `<mxCell>...</mxCell>`. The injection script should produce whatever matches the file's style (check a few existing cells to detect).
- **Canvas ID discovery**: The second cell (after the root ID=0 cell) is always the canvas with `parent="0"`. Its ID is what all content cells reference in their own `parent` attribute. Extract it: `re.search(r'<mxCell id="([^"]+)" parent="root-id"[^>]*value="', content)`.
- **File renamed as .txt**: User may send file as `.txt`. Detect drawio by checking for `<mxfile` header in first line.

## Edge Cases

### Page 1 is duplicate of Page 2

Some diagrams duplicate the ALZ on both pages. When injecting flow, target the second page ("CoPilot Studio Low Code" or similar) — Page 1 is the reference version.

### Dashed boundary overlap

When placing boundaries behind nodes, insert them EARLIER in the XML (before the nodes they contain), or set a z-order attribute. Drawio renders cells in document order.

### Special characters in labels

Use HTML entities for labels with `<br/>`, bold, etc.:

```
value="&lt;b&gt;Bold Title&lt;/b&gt;&lt;br&gt;Subtitle"
```

## References

- `references/drawio-alz-flow-injection.md` — Session-specific: FLOW_MCP.drawio injection with ALZ Hub & Spoke + Copilot Studio → MCP path
