---
name: architecture-diagram
description: "Dark-themed SVG architecture/cloud/infra diagrams as HTML."
version: 1.0.0
author: Cocoon AI (hello@cocoon-ai.com), ported by Hermes Agent
license: MIT
dependencies: []
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [architecture, diagrams, SVG, HTML, visualization, infrastructure, cloud]
    related_skills: [concept-diagrams, excalidraw, azure-architecture-diagrams]
---

# Architecture Diagram Skill

Generate professional, dark-themed technical architecture diagrams as standalone HTML files with inline SVG graphics. No external tools, no API keys, no rendering libraries — just write the HTML file and open it in a browser.

## Scope

**Best suited for:**
- Software system architecture (frontend / backend / database layers)
- Cloud infrastructure (VPC, regions, subnets, managed services)
- Microservice / service-mesh topology
- Database + API map, deployment diagrams
- Anything with a tech-infra subject that fits a dark, grid-backed aesthetic

**Look elsewhere first for:**
- Physics, chemistry, math, biology, or other scientific subjects
- Physical objects (vehicles, hardware, anatomy, cross-sections)
- Floor plans, narrative journeys, educational / textbook-style visuals
- Hand-drawn whiteboard sketches (consider `excalidraw`)
- Animated explainers (consider an animation skill)

If a more specialized skill is available for the subject, prefer that. If none fits, this skill can also serve as a general SVG diagram fallback — the output will just carry the dark tech aesthetic described below.

Based on [Cocoon AI's architecture-diagram-generator](https://github.com/Cocoon-AI/architecture-diagram-generator) (MIT).

## Workflow

1. User describes their system architecture (components, connections, technologies)
2. Generate the HTML file following the design system below
3. Save with `write_file` to a `.html` file (e.g. `~/architecture-diagram.html`)
4. User opens in any browser — works offline, no dependencies

### Output Location

Save diagrams to a user-specified path, or default to the current working directory:
```
./[project-name]-architecture.html
```

### Preview

After saving, suggest the user open it:
```bash
# macOS
open ./my-architecture.html
# Linux
xdg-open ./my-architecture.html
```

## Design System & Visual Language

### Color Palette (Semantic Mapping)

Use specific `rgba` fills and hex strokes to categorize components:

| Component Type | Fill (rgba) | Stroke (Hex) |
| :--- | :--- | :--- |
| **Frontend** | `rgba(8, 51, 68, 0.4)` | `#22d3ee` (cyan-400) |
| **Backend** | `rgba(6, 78, 59, 0.4)` | `#34d399` (emerald-400) |
| **Database** | `rgba(76, 29, 149, 0.4)` | `#a78bfa` (violet-400) |
| **AWS/Cloud** | `rgba(120, 53, 15, 0.3)` | `#fbbf24` (amber-400) |
| **Security** | `rgba(136, 19, 55, 0.4)` | `#fb7185` (rose-400) |
| **Message Bus** | `rgba(251, 146, 60, 0.3)` | `#fb923c` (orange-400) |
| **External** | `rgba(30, 41, 59, 0.5)` | `#94a3b8` (slate-400) |

### Typography & Background
- **Font:** JetBrains Mono (Monospace), loaded from Google Fonts
- **Sizes:** 12px (Names), 9px (Sublabels), 8px (Annotations), 7px (Tiny labels)
- **Background:** Slate-950 (`#020617`) with a subtle 40px grid pattern

```svg
<!-- Background Grid Pattern -->
<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" stroke-width="0.5"/>
</pattern>
```

## Technical Implementation Details

### Component Rendering
Components are rounded rectangles (`rx="6"`) with 1.5px strokes. To prevent arrows from showing through semi-transparent fills, use a **double-rect masking technique**:
1. Draw an opaque background rect (`#0f172a`)
2. Draw the semi-transparent styled rect on top

### Connection Rules
- **Z-Order:** Draw arrows *early* in the SVG (after the grid) so they render behind component boxes
- **Arrowheads:** Defined via SVG markers
- **Security Flows:** Use dashed lines in rose color (`#fb7185`)
- **Boundaries:**
  - *Security Groups:* Dashed (`4,4`), rose color
  - *Regions:* Large dashed (`8,4`), amber color, `rx="12"`

### Spacing & Layout Logic
- **Standard Height:** 60px (Services); 80-120px (Large components)
- **Vertical Gap:** Minimum 40px between components
- **Message Buses:** Must be placed *in the gap* between services, not overlapping them
- **Legend Placement:** **CRITICAL.** Must be placed outside all boundary boxes. Calculate the lowest Y-coordinate of all boundaries and place the legend at least 20px below it.

## Document Structure

The generated HTML file follows a four-part layout:
1. **Header:** Title with a pulsing dot indicator and subtitle
2. **Main SVG:** The diagram contained within a rounded border card
3. **Summary Cards:** A grid of three cards below the diagram for high-level details
4. **Footer:** Minimal metadata

### Info Card Pattern
```html
<div class="card">
  <div class="card-header">
    <div class="card-dot cyan"></div>
    <h3>Title</h3>
  </div>
  <ul>
    <li>• Item one</li>
    <li>• Item two</li>
  </ul>
</div>
```

## Output Requirements
- **Single File:** One self-contained `.html` file
- **No External Dependencies:** All CSS and SVG must be inline (except Google Fonts)
- **No JavaScript:** Use pure CSS for any animations (like pulsing dots)
- **Compatibility:** Must render correctly in any modern web browser

## Template Reference

Load the full HTML template for the exact structure, CSS, and SVG component examples:

```
skill_view(name="architecture-diagram", file_path="templates/template.html")
```

The template contains working examples of every component type (frontend, backend, database, cloud, security), arrow styles (standard, dashed, curved), security groups, region boundaries, and the legend — use it as your structural reference when generating diagrams.

## Alternative: Python `diagrams` Library (Official Cloud Provider Icons)

For architecture diagrams with **real Azure, AWS, or GCP service icons** (the official stencil kit look), use the Python `diagrams` library instead of the HTML/SVG approach. This generates a PNG file using graphviz with the actual Microsoft/Amazon/Google iconography.

### When to use which

| Approach | Best for |
|----------|----------|
| **HTML/SVG** (this skill's primary) | Custom tech stacks, dark theme, no dependencies, any component type |
| **Python `diagrams` library** | Real cloud provider diagrams, official icons, enterprise presentations, WAF reviews |

### Quick Start

```bash
pip install diagrams
sudo apt-get install -y graphviz
```

Key pattern — write a Python script, run it via `terminal()`:

```python
from diagrams import Diagram, Edge, Cluster
from diagrams.azure.compute import AppServices, AKS
from diagrams.azure.database import SQLDatabases, CosmosDb
from diagrams.azure.network import FrontDoors, ApplicationGateway, Firewall
from diagrams.azure.security import KeyVaults
from diagrams.azure.integration import ServiceBus, APIManagement
from diagrams.onprem.client import Users

with Diagram("Title", show=False, direction="LR", filename="output", outformat="png"):
    users = Users("Users")
    with Cluster("Layer"):
        service = AppServices("App Service")
    users >> service
```

### Import Path Reference (v0.25)

Use `diagrams.azure.X` (singular) tree:

| Module (singular) | Key Classes |
|-------------------|-------------|
| `diagrams.azure.compute` | AppServices, FunctionApps, AKS, ContainerInstances, BatchAccounts |
| `diagrams.azure.database` | SQLDatabases, CosmosDb, CacheForRedis, DataLake |
| `diagrams.azure.network` | FrontDoors, ApplicationGateway, Firewall, ExpressrouteCircuits, LoadBalancers, PrivateEndpoint, VirtualNetworks |
| `diagrams.azure.security` | KeyVaults, MicrosoftDefenderForCloud, Sentinel |
| `diagrams.azure.integration` | APIManagement, ServiceBus, EventGridTopics, LogicApps, AppConfiguration |
| `diagrams.azure.analytics` | EventHubs, StreamAnalyticsJobs, Databricks, SynapseAnalytics |
| `diagrams.azure.storage` | BlobStorage, StorageAccounts, QueueStorage, DataLakeStorage |
| `diagrams.azure.identity` | ActiveDirectory, ADB2C, ConditionalAccess |
| `diagrams.azure.monitor` | Monitor, ApplicationInsights, LogAnalyticsWorkspaces |
| `diagrams.azure.ml` | MachineLearningServiceWorkspaces, CognitiveServices, BotServices |
| `diagrams.onprem.client` | Users |
| `diagrams.generic.blank` | Blank |

### Graph Attributes for Dark Theme

```python
graph_attr={
    "bgcolor": "#0f172a",
    "fontcolor": "#e2e8f0",
    "fontname": "JetBrains Mono",
    "dpi": "200",
    "splines": "ortho",
},
node_attr={"fontcolor": "#e2e8f0", "fontname": "JetBrains Mono", "fontsize": "9"},
edge_attr={"fontcolor": "#94a3b8", "fontname": "JetBrains Mono", "fontsize": "7"},
```

### Edge Styling Convention

```python
users >> Edge(color="#fbbf24", style="dashed") >> front_door   # HTTP/WAF
apim >> Edge(color="#34d399") >> apps                           # internal
apps >> Edge(color="#22d3ee") >> sb                             # async/messaging
apps >> Edge(color="#a78bfa") >> sql                            # data
apps >> Edge(color="#fb7185", style="dashed") >> insights       # monitoring
node >> Edge(color="#e2e8f0", style="dotted") >> entra          # identity
node >> Edge(color="#facc15", style="dotted") >> kv             # secrets
actions >> Edge(color="#22d3ee") >> apps                        # CI/CD
node >> Edge(color="#fb7185", style="dotted") >> log_analytics  # audit
```

### Pitfalls

- The `diagrams` Python sandbox (`execute_code`) does NOT have `diagrams` installed — run via `terminal()` instead, writing the script to a temp file first
- Wrong import path causes `ImportError` — always verify available classes with `dir()` on the module before writing a script. The available names vary between `diagrams` versions
- `diagrams.azure.network` (singular) != `diagrams.azure.networking` (plural) — the singular tree is correct for v0.25. The plural tree has different class names. Use `dir()` to confirm
- Output is a `.png` file — share with the user via `MEDIA:/path/to/file.png` in-line with text in a send_message, not as a bare MEDIA tag (which produces 'No deliverable text or media remained')
- Graphviz (`dot` binary) must be installed at system level: `sudo apt-get install graphviz` — without it, the script produces no output
- Very tall diagrams (>10k px) may exceed Telegram's inline display limits. Prefer `direction="TB"` (top-to-bottom) for landscape-friendly proportions, or `direction="LR"` with a tight `ranksep` to keep width manageable
- Use `outformat="png"` — other formats (svg, pdf) may not render in all delivery channels
- The bgcolor must be set explicitly in graph_attr for dark themes — it does NOT inherit from node/edge attrs

## Reusable Scripts

The following scripts are bundled with this skill for regenerating or modifying reference diagrams:

- `scripts/azure-landing-zone.py` — Full Azure Landing Zone for UK regulated enterprise (hub, prod spoke, non-prod, management, CI/CD)
- `scripts/azure-key-vault.py` — Azure Key Vault enterprise reference architecture (management plane, data plane, workloads, lifecycle)

