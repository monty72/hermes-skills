---
name: fastmcp
description: "Build, test, inspect, install, and deploy MCP servers with FastMCP in Python."
version: 1.0.0
---

# FastMCP

## Overview

Build MCP servers with FastMCP in Python. Use when creating a new MCP server, wrapping an API or database as MCP tools, exposing resources or prompts, or preparing a FastMCP server for Claude Code, Cursor, or HTTP deployment.

## Pitfalls & Known Quirks

### `FastMCP()` constructor only accepts `name`, `version`, `instructions`

The `description` keyword argument is **rejected** (FastMCP ≥1.6.x). Use `instructions` for the server-level description instead:

```python
# ✅ Correct
mcp = FastMCP(
    name="My Server",
    version="1.0.0",
    instructions="Optional description of what this server does.",
)

# ❌ TypeError: unexpected keyword argument 'description'
mcp = FastMCP(
    name="My Server",
    description="This will crash on import.",
)
```

### `list_tools()` is async

You cannot call `mcp.list_tools()` synchronously — it returns a coroutine. Use `asyncio.run()` to inspect tools in a sync context:

```python
import asyncio

tools = asyncio.run(mcp.list_tools())
print([t.name for t in tools])
```

The old private attribute `mcp._tool_manager.list_tools()` no longer exists in FastMCP 1.6.x.

### SSE endpoint lives at `/sse`

When running with SSE transport (uvicorn), FastMCP serves the SSE endpoint at the `/sse` path. Clients connecting must hit `http://host:port/sse` to initiate the stream. FastMCP handles the `/sse` → message endpoint flow correctly, but Copilot Studio requires the initial SSE response to include the full message endpoint URI (FastMCP does this automatically).

### Tool names must be stable with explicit `name` kwarg

When passing `name=` to `@mcp.tool()`, the tool name is fixed. Omitting it derives the name from the function name. For tools consumed by Copilot Studio or AI Foundry, prefer explicit names for stability across code refactors.

```python
# ✅ Explicit stable name — survives function renames
@mcp.tool(name="bigquery_run_query")
def _run_query_impl(query: str) -> str:
    return "results"

# ❌ Implicit name — breaks if function is renamed
@mcp.tool()
def bigquery_run_query(query: str) -> str:
    return "results"
```

### GCP SDK imports block server startup — use lazy import

When building MCP servers that talk to GCP services (BigQuery, Vertex AI, Storage), do NOT import GCP SDKs at module level — they block server creation when no credentials exist (tests, CI, dev environments without ADC). Use a lazy-init function instead:

```python
# Instead of:
from google.cloud import bigquery          # ❌ blocks on import

# Do this:
_bq_client = None

def _get_bq():
    global _bq_client
    if _bq_client is None:
        from google.cloud import bigquery
        _bq_client = bigquery.Client()
    return _bq_client

# Also avoid calling vertexai.init() in server creation —
# let each tool init on first call.
```

### Separate read-only and write-capable servers for enterprise approval

When serving Copilot Studio or AI Foundry with `require_approval="always"` for writes, run two MCP server instances:
- **Read server** — query tools only, approval not required
- **Write server** — mutation tools, always requires approval

This avoids approval fatigue on common read operations while still gating destructive actions.

## Architectural Patterns

### Multi-connector architecture (one server, many services)

Structure enterprise MCP servers with a **connector-per-service** pattern. Each connector lives in its own module and exports a `register_tools(mcp, ...)` function:

```
src/
├── server.py              # create_server() — registers all connectors
├── config.py              # typed config from environment
├── auth.py                # shared auth helpers
├── connectors/
│   ├── vertex_ai.py       # register_tools(mcp, project_id, location, model_name)
│   ├── bigquery.py        # register_tools(mcp, project_id, default_dataset)
│   ├── storage.py         # register_tools(mcp, project_id, default_bucket)
│   └── ...
└── utils/
    └── error_handler.py   # decorator-based SDK error wrapping
```

Each connector module is self-documenting — register all its tools in one call:

```python
# server.py
def create_server(cfg: AppConfig) -> FastMCP:
    mcp = FastMCP(name="My Server", version="1.0.0")

    vertex_ai.register_tools(mcp, project_id=cfg.gcp.project_id, ...)
    bigquery.register_tools(mcp, project_id=cfg.gcp.project_id, ...)

    return mcp
```

### Meta tools pattern (health + info)

Every enterprise MCP server should expose informational tools so consumers can diagnose connectivity without reading config files:

```python
@mcp.tool(name="gcp_health_check")
def health_check() -> str:
    """Check GCP authentication and all configured services."""
    authed, msg = check_gcp_auth()
    lines = [f"{'✅' if authed else '❌'} Auth: {msg}"]
    lines.append(f"   • Project: `{cfg.gcp.project_id}`")
    lines.append(f"   • Model: `{cfg.gcp.vertex_ai_model}`")
    return "\n".join(lines)

@mcp.tool(name="gcp_server_info")
def server_info() -> str:
    """Metadata about this server's capabilities."""
    return f"**My Server** v1.0.0\nServices: Vertex AI, BigQuery, Cloud Storage\n"
```

### Error handling decorator

Wrap GCP (or any SDK) tool handlers with a consistent error decorator that catches SDK errors and returns clean MCP tool errors:

```python
from fastmcp.exceptions import ToolError

class ServiceToolError(ToolError):
    def __init__(self, message: str, service: str = "", detail: str = ""):
        parts = [message]
        if service:
            parts.insert(0, f"[{service}]")
        if detail:
            parts.append(f"({detail})")
        super().__init__(" ".join(parts))

def handle_service_errors(service_name: str = ""):
    """Decorator for SDK-wrapped tool handlers."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ServiceToolError:
                raise
            except Exception as e:
                raise ServiceToolError(
                    message=f"Failed in {func.__name__}",
                    service=service_name,
                    detail=str(e),
                ) from e
        return wrapper
    return decorator

# Usage in a connector:
@mcp.tool(name="bigquery_run_query")
@handle_service_errors(service_name="BigQuery")
def run_query(query: str) -> str:
    return _get_bq().query(query).result().to_dataframe().to_markdown()
```

### Full project scaffolding template

For a production-ready MCP server with multiple GCP connectors, SSE deployment, Docker, and Azure/GCP deployment configs, copy the project at `~/projects/gcp-mcp-server/`:

```
gcp-mcp-server/
├── src/
│   ├── server.py                # FastMCP setup + tool registration
│   ├── config.py                # Dataclass config from env vars
│   ├── auth.py                  # GCP ADC + workload identity
│   ├── connectors/
│   │   ├── vertex_ai.py         # Gemini generate, chat, web search
│   │   ├── bigquery.py          # SQL, schema, datasets, cost estimate
│   │   ├── storage.py           # Buckets, list, read, upload
│   │   └── vertex_search.py     # Search, converse, data stores
│   └── utils/
│       └── error_handler.py     # Decorator SDK error wrapping
├── docs/
│   ├── copilot-studio-connection.md
│   ├── ai-foundry-connection.md
│   ├── azure-power-platform-connectivity.md
│   └── gcp-setup.md
├── infra/
│   ├── cloud-run.yaml           # VPC-internal Cloud Run deployment
│   └── azure-container-apps.bicep  # Private ACA + workload identity
├── Dockerfile                   # uvicorn SSE entry point
├── docker-compose.yml           # Local dev with ADC mount
└── Makefile                     # install/test/run/deploy
```

## Enterprise Bridge Deployment: Copilot Studio & AI Foundry → GCP

Copilot Studio and Azure AI Foundry connect to MCP servers via SSE (Server-Sent Events) at the `/sse` path. See `references/copilot-studio-ai-foundry-bridge.md` for full connection guides covering:

- Connecting from Copilot Studio (SSE endpoint, onboarding wizard, auth)
- Connecting from AI Foundry (MCPTool, Project Connections, Toolboxes, approval patterns)
- GCP ↔ Azure workload identity federation for container deployments
- Full project scaffolding for a GCP MCP bridge server

## Multi-Cloud MCP Architecture (Azure + GCP)

See `references/multi-cloud-mcp-patterns.md` for 5 deployment patterns when AI agents live in both Azure (AI Foundry / Copilot Studio) and GCP (Vertex AI). Covers auth (Managed Identity vs Workload Identity Federation), latency trade-offs, and evolution from single-server to dual-server to sidecar mesh.

**Key recommendation:** Deploy the MCP server in whatever cloud is your primary AI runtime. Single server in Azure is the default. Split to dual (one per cloud) when both are equally primary and isolation matters.

## Private On-Prem → Copilot Studio Connectivity

See `references/on-prem-copilot-connectivity.md` for 4 patterns connecting Copilot Studio agents to on-prem data/services without public internet exposure. The key insight: Copilot Studio is multi-tenant SaaS, so the MCP server must run in Azure (in your VNet) and be reached via Power Platform VNet Integration. The on-prem hop goes over ExpressRoute.

**MCP protocol limitation:** Only the VNet + ACA pattern supports native MCP SSE end-to-end. The on-prem data gateway cannot pass MCP protocol — only REST custom connectors.

## Azure → Power Platform Connectivity

See `references/azure-power-platform-connectivity.md` for the 5 canonical connectivity patterns between Azure services and Power Platform (Power Apps, Power Automate, Copilot Studio, AI Foundry):

1. **APIM → Custom Connector** — enterprise standard: export Azure APIs as Power Platform connectors
2. **VNet Direct** — native Power Platform VNet integration for private Azure PaaS access
3. **On-Prem Data Gateway** — legacy/hybrid bridge
4. **Event Grid → Power Automate** — push-based event reactions
5. **Logic Apps Hub** — multi-step cross-cloud orchestration

Includes the topology for the full stack: Power Platform → Azure → GCP MCP Server.

## Quick Start

```python
from fastmcp import FastMCP

# Create server
mcp = FastMCP("My Server")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.resource("config://app")
def get_config() -> str:
    """Static config resource"""
    return "App configuration here"

# Run (stdio transport)
if __name__ == "__main__":
    mcp.run()
```

## Tools

```python
@mcp.tool()
def get_weather(city: str) -> str:
    """Get weather for a city"""
    return f"Weather for {city}: sunny, 22°C"
```

## Resources

```python
# Static resource
@mcp.resource("file:///path/to/data")
def get_data() -> str:
    return "data"

# Dynamic resource with URI params
@mcp.resource("users://{user_id}/profile")
def get_profile(user_id: str) -> str:
    return f"Profile for {user_id}"
```

## Prompts

```python
@mcp.prompt()
def review_code(code: str) -> str:
    return f"Review this code:\n{code}"
```

## Running

```bash
# Stdio (default)
python server.py

# HTTP (SSE)
mcp run server.py --transport sse

# With uvicorn for production
uvicorn my_server:mcp.sse_app()
```

## Delivery workflow

After building any MCP server project, always **init git and push to the user's GitHub** (`monty72/<project-name>`). Never leave artifacts as local-only directories.

```bash
cd <project-dir>
git init && git branch -m main
git add -A && git commit -m "Initial: <description>"
# Create repo via GitHub API if it doesn't exist
curl -s -H "Authorization: token $GH_TOKEN" \
  -d "{\"name\":\"<project>\",\"private\":true}" \
  https://api.github.com/user/repos
git remote add origin git@github.com:monty72/<project>.git
git push -u origin main
```

## Connecting

```yaml
# In hermes config.yaml:
mcp:
  servers:
    my-server:
      command: python
      args: ["path/to/server.py"]
```
