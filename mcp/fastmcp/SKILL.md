---
name: fastmcp
description: "Build, test, inspect, install, and deploy MCP servers with FastMCP in Python."
version: 1.0.0
---

# FastMCP

## Overview

Build MCP servers with FastMCP in Python. Use when creating a new MCP server, wrapping an API or database as MCP tools, exposing resources or prompts, or preparing a FastMCP server for Claude Code, Cursor, or HTTP deployment.

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

## Connecting

```yaml
# In hermes config.yaml:
mcp:
  servers:
    my-server:
      command: python
      args: ["path/to/server.py"]
```
