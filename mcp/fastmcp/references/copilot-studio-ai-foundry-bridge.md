# Copilot Studio & AI Foundry → GCP MCP Bridge

Enterprise pattern for deploying a FastMCP server that bridges Microsoft AI platforms with Google Cloud services.

## Architecture

```
Copilot Studio / AI Foundry
       │
       │  HTTPS/SSE → /sse
       ▼
  ┌──────────────────┐
  │  FastMCP Server   │  ← Deployed on Cloud Run or Azure Container Apps
  │  (uvicorn SSE)    │
  └──────┬───────────┘
         │
         ▼  GCP SDKs (ADC / Workload Identity)
  ┌──────────────────┐
  │  GCP Services     │  Vertex AI, BigQuery, Cloud Storage, Vertex Search
  └──────────────────┘
```

## Transport: SSE (not stdio)

- Copilot Studio requires **SSE transport** — the server must expose `/sse`
- FastMCP provides this via `mcp.sse_app()` with uvicorn:
  ```python
  uvicorn src.server:create_server().sse_app() --host 0.0.0.0 --port 8080
  ```
- The `/sse` endpoint must return a `session_id` and the **full message endpoint URI** in the initial SSE stream — FastMCP handles this automatically
- The server must be HTTPS-reachable from Copilot Studio's network (use a public endpoint with IP restriction or VPC ingress)

## Connecting from Copilot Studio

1. Deploy the MCP server with SSE
2. Get the HTTPS URL → `https://your-server-url/sse`
3. In Copilot Studio: **Actions → Add action → MCP → Connect to existing MCP server**
4. Enter the SSE URL
5. Copilot Studio discovers tools automatically
6. Auth options: None (VPC-private), API Key header, or OAuth 2.0

**Example topic prompt pattern:**
```
User: "Show me last month's sales by region"
Agent: 1. bigquery_list_tables → 2. bigquery_get_schema → 3. bigquery_run_query
```

## Connecting from AI Foundry

Use the `MCPTool` class from `azure-ai-projects`:

```python
from azure.ai.projects.models import MCPTool

tool = MCPTool(
    server_label="gcp-bridge",
    server_url="https://your-server/sse",
    require_approval="on_action",  # or "always" for writes
    project_connection_id="gcp-mcp-connection",
    allowed_tools=[  # Restrict which tools the agent can see
        "vertex_ai_generate",
        "bigquery_run_query",
        "gcs_list_objects",
    ],
)
```

**Foundry Toolboxes (Preview):** Bundle your MCP server into a Toolbox for centralised governance — tools can be added/removed without changing agent code.

## GCP SDK Lazy Import Pattern

The server must create successfully even without GCP credentials (for tests, CI, dev without ADC):

```python
# ❌ Bad — blocks on import
from google.cloud import bigquery

# ✅ Good — lazy, cached
_bq_client = None
def _get_bq():
    global _bq_client
    if _bq_client is None:
        from google.cloud import bigquery
        _bq_client = bigquery.Client()
    return _bq_client

# ✅ Same pattern for discoveryengine (separate package)
_de = None
def _get_de():
    global _de
    if _de is None:
        from google.cloud import discoveryengine
        _de = discoveryengine
    return _de
```

Avoid calling `vertexai.init()` at server creation time — defer it to tool invocation.

## Deployment Options

### GCP Cloud Run (GCP-native)

```bash
gcloud run deploy gcp-mcp-server \
  --image gcr.io/$PROJECT/gcp-mcp-server:latest \
  --region us-central1 \
  --ingress internal \
  --service-account gcp-mcp-server-sa@$PROJECT.iam.gserviceaccount.com
```

- IAM: `aiplatform.user`, `bigquery.jobUser`, `bigquery.dataViewer`, `storage.objectViewer`, `discoveryengine.viewer`
- Use Secret Manager for config, not env vars

### Azure Container Apps (Azure-native)

Use Workload Identity Federation so GCP trusts Azure's managed identity:

```bash
# GCP side
gcloud iam workload-identity-pools create "gcp-mcp-pool" --location="global"
gcloud iam workload-identity-pools providers create-oidc "azure-prod" \
  --location="global" \
  --workload-identity-pool="gcp-mcp-pool" \
  --issuer-uri="https://login.microsoftonline.com/$TENANT/v2.0"

# Grant SA access via pool
gcloud iam service-accounts add-iam-policy-binding \
  gcp-mcp-sa@$PROJECT.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/$POOL/..."
```

## Split Read/Write Servers (Production)

| Server | Tools | Ingress | Approval |
|--------|-------|---------|----------|
| `gcp-mcp-read` | query/read only | VPC-internal | `on_action` |
| `gcp-mcp-write` | upload/mutate only | VPC-internal + RBAC | `always` |

## Security

- **Internal-only ingress** on Cloud Run or ACA
- **API key auth** for non-VPC deployments
- **Least-privilege GCP SA** — scope to specific datasets/buckets, not project-level
- **VPC Service Controls** for GCP-native to prevent data exfiltration
- **Audit logging** via AI Foundry for every MCP tool call
