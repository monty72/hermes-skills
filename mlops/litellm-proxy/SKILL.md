---
name: litellm-proxy
description: Deploy, configure, and manage a LiteLLM proxy server — multi-model OpenAI-compatible endpoint with systemd service, auto-restart, health monitoring, and model routing configuration.
tags: [litellm, proxy, llm, openai-compatible, systemd, model-routing, deepseek, multi-model]
---

# LiteLLM Proxy

LiteLLM is a lightweight proxy that exposes a single OpenAI-compatible API endpoint
(`/v1/chat/completions`, `/v1/models`, `/health`) routing to multiple LLM backends.
Swap models by changing the `model` parameter in your client — no config changes needed.

## Installation

LiteLLM is installed system-wide via pip, not in a virtual environment:

```bash
pip install litellm
```

Binary goes to `~/.local/bin/litellm`. Verify:

```bash
litellm --help
```

## Configuration

Config file at `~/.litellm/config.yaml`. Structure:

```yaml
general_settings:
  enable_request_id: true

litellm_settings:
  drop_params: true
  set_verbose: false

model_list:
  - model_name: deepseek-chat
    litellm_params:
      model: openai/deepseek-chat
      api_key: sk-...
      api_base: https://api.deepseek.com/v1
      max_tokens: 65536
  - model_name: gpt-4o
    litellm_params:
      model: openai/gpt-4o
      api_key: sk-...
```

Each entry maps a friendly `model_name` (what your clients use) to a `litellm_params.model`
identifier (provider/model format).

### Model Name Mapping Convention

| Model Name | Backend | Notes |
|---|---|---|
| `deepseek-v4-flash` | DeepSeek V4 Flash (fast) | Mapped via openai/deepseek-chat on DeepSeek base |
| `deepseek-v4-pro` | DeepSeek V4 Pro (reasoning) | Mapped via openai/deepseek-reasoner on DeepSeek base |
| `deepseek-chat` | DeepSeek V3 | Chat fallback |
| `deepseek-reasoner` | DeepSeek R1 | Full reasoning |
| `gpt-4o` | OpenAI GPT-4o | Backup |
| `gpt-4o-mini` | OpenAI GPT-4o-mini | Cheap backup |

## Running

### Manual (foreground)
```bash
litellm --config ~/.litellm/config.yaml --port 4000 --host 0.0.0.0 --num_workers 2
```

### Systemd User Service (auto-start + auto-restart)

**Unit file:** `~/.config/systemd/user/litellm-proxy.service`

```ini
[Unit]
Description=LiteLLM Proxy — OpenAI-compatible multi-model endpoint
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=%h/.local/bin/litellm --config %h/.litellm/config.yaml --port 4000 --host 0.0.0.0 --num_workers 2
Restart=always
RestartSec=10
Environment="PATH=%h/.local/bin:/usr/local/bin:/usr/bin:/bin"
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

**Enable and start:**
```bash
systemctl --user daemon-reload
systemctl --user enable litellm-proxy.service
systemctl --user start litellm-proxy.service
```

**Check status:**
```bash
systemctl --user status litellm-proxy.service
journalctl --user -u litellm-proxy.service --no-pager -n 50
```

## Verification

### Health check
```bash
curl -s http://localhost:4000/health
```
Returns JSON with `healthy_endpoints`, `unhealthy_endpoints`, `healthy_count`.

### List models
```bash
curl -s http://localhost:4000/v1/models | jq .
```

### Test chat completion
```bash
curl -s http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"say hello"}],"max_tokens":20}'
```

## Pitfalls

- **Not in venv** — LiteLLM installs system-wide via pip, NOT in a project virtualenv. Do NOT use the venv path. The binary lives at `~/.local/bin/litellm`. Do NOT try `python -m litellm` from a venv — it won't find the module unless installed there.
- **High memory usage** — LiteLLM uses ~600MB RAM at rest with 2 workers. Monitor with `systemctl --user status`.
- **No env injection** — API keys go in the config file directly. Keep `config.yaml` permissions at 600.
- **Systemd EXEC 203** — If you get exit-code 203/EXEC, you gave systemd a path that doesn't exist. Use `%h/.local/bin/litellm`, not a venv path.
- **Health check in cron** — The cron health check for OpenCrawl (monitoring multiple services) checks for LiteLLM on port 4000 and flags it as PROXY_DOWN if unreachable.
