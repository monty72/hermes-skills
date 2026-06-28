# FLOW_MCP.drawio — ALZ + Copilot Studio → MCP Injection

Session: 2026-06-26 — Added Copilot Studio → MCP traffic flow to Page 2 of FLOW_MCP.drawio

## File Anatomy

| Property | Value |
|----------|-------|
| File size | 5,653,298 bytes (5.6 MB) |
| Lines | 4,987 |
| Pages | 2 |
| Page 1 | `AI Landing Zone Architecture` (ID: `_voUPaYB4BbW1cI-FXS_`) |
| Page 2 | `CoPilot Studio Low Code` (ID: `e2Ui0CIxrY2rB0QkJAFX`) |
| Root IDs | Page 1: `yvAwWkkrhjme5IgpjQKr-0`, Page 2: `qyepl6iVJ43P_be80-GU-0` |
| Canvas IDs | Page 1: `yvAwWkkrhjme5IgpjQKr-1`, Page 2: `qyepl6iVJ43P_be80-GU-1` |
| Max cell number (P2 before injection) | 730 |

## Injection Target

- **Diagram**: Page 2 ("CoPilot Studio Low Code")
- **Position**: Right side of the ALZ (x ~3060-3420, y ~700-1380)
- **Parent canvas**: `qyepl6iVJ43P_be80-GU-1`

## How the Page 2 Insertion Point Was Found

The second diagram's root block ends with `</root>` followed by:

```
    </mxGraphModel>
  </diagram>
```

Used `re.search(r'(</root>\s*\n\s*</mxGraphModel>\s*\n\s*</diagram>)', rest)` to find the exact insertion boundary in the second diagram's content (not Page 1's).

**Critical technique**: Split the file on the diagram name string, NOT on diagram count or position. This avoids Page 1's identical structure.

```python
parts = content.split('<diagram name="CoPilot Studio Low Code"', 1)
before = parts[0]                                          # Page 1 + everything before
rest = '<diagram name="CoPilot Studio Low Code"' + parts[1]  # Page 2 content
```

## Cell ID Discovery

Page 2 uses IDs like `qyepl6iVJ43P_be80-GU-NNN`. To find the max number:

```python
cell_ids = re.findall(r'id="[^"]+"', rest[:root_close_pos])
max_num = 0
for cid in cell_ids:
    m = re.search(r'GU-(\d+)$', cid)
    if m:
        n = int(m.group(1))
        if n > max_num:
            max_num = n
```

Result: max was 730 (the last stencil cell on Page 2). New flow cells use IDs starting from `qyepl6iVJ43P_be80-flow-0`.

## Injected Elements

| ID | Type | Content | Position |
|----|------|---------|----------|
| `flow-0` | Node (blue) | Copilot Studio (SaaS) | 3100, 700 |
| `flow-1` | Node (dark blue) | Custom Connector | 3100, 800 |
| `flow-2` | Node (purple) | Power Platform Runtime | 3100, 900 |
| `flow-3` | Node (gold/red border) | ⚠ KEY GAP — Injected vNIC in PP Delegated Subnet | 3060, 1000 |
| `flow-4` | Node (red) | Hub Firewall (Connectivity Sub) | 3100, 1120 |
| `flow-5` | Node (blue) | Private Endpoint (AI LZ) | 3100, 1240 |
| `flow-6` | Node (green) | MCP Server (Container App) | 3100, 1360 |
| `flow-arrow-0` to `flow-arrow-5` | Edges | Orthogonal arrows (arrow-3 = red 3px) | — |
| `flow-boundary` | Dashed box | AI Landing Zone (green dashed) | 3040, 1220, 380×220 |
| `flow-boundary-conn` | Dashed box | Connectivity Subscription (orange dashed) | 3040, 1100, 380×100 |
| `flow-label` | Text | Copilot Studio → MCP Traffic Flow (bold) | 3020, 620 |

## Arrow Styling

- Arrows between standard nodes: `strokeWidth=2` (default black)
- Arrow from KEY GAP to Hub Firewall: `strokeWidth=3;strokeColor=#FF0000` (red, thicker)
- All use `entryX=0.5;entryY=0;exitX=0.5;exitY=1` for vertical orthogonal routing

## Verification

After injection:
- 16 flow-related XML cells added
- Validated: `grep -c "flow-"` returned 16
- Validated: `grep "flow-0"` and `"flow-label"` found inside Page 2 split content

## Pushing to GitHub

- Repo: `monty72/alz-copilot-mcp-flow` (private)
- Auth: SSH key (git@github.com) for push; vault GITHUB_TOKEN for API (create repo)
- Process: `gh auth` token was invalid → used `curl -X POST -H "Authorization: token $(hermes-vault get GITHUB_TOKEN)"` to create repo → `git remote add origin git@github.com:monty72/…` → `git push -u origin master`
