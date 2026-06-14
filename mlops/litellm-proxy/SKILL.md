---
name: litellm-proxy
description: Deploy, configure, and manage a LiteLLM proxy server and/or Ollama local inference — multi-model OpenAI-compatible endpoint with systemd service, auto-restart, health monitoring, model routing configuration, local model management, and Open WebUI deployment.
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

## Local Inference with Ollama

Ollama wraps llama.cpp to provide a simple model-management lifecycle and an OpenAI-compatible REST API. It complements LiteLLM — you can run a local model via Ollama and proxy it through LiteLLM alongside cloud providers.

### When to Use

- **Ollama** (this section) — easiest CPU setup, model management built-in, good for general chat/code. Best for 3B–14B params on CPU, or 7B–70B on GPU.
- **llama.cpp** (`llama-cpp` skill) — finer control over GGUF quant selection, direct server process, advanced features (speculative decoding, grammar constraints, LoRA).
- **vLLM** (`serving-llms-vllm` skill) — GPU-optimized production serving, PagedAttention, best for high-throughput/high-concurrency.

### Quick Install

```bash
curl -fsSL https://ollama.com/install.sh | bash
```

This adds the Ollama systemd service, creates the `ollama` user, and starts the service on `127.0.0.1:11434`.

**WARNING:** The install script detects GPU drivers but defaults to CPU-only if none are found. On a CPU-only machine you'll see `WARNING: No NVIDIA/AMD GPU detected.` — this is expected and fine.

### Expose to LAN (for LiteLLM routing)

By default Ollama binds to `127.0.0.1:11434`. To allow LiteLLM on another host to reach it:

```bash
sudo mkdir -p /etc/systemd/system/ollama.service.d
cat << 'EOF' | sudo tee /etc/systemd/system/ollama.service.d/override.conf
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_KEEP_ALIVE=5m"
EOF
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

### Pull Models

```bash
ollama pull llama3.2:3b          # 2 GB, runs on 8GB RAM
ollama pull mistral:7b-instruct-q4_K_M  # 4.4 GB, needs 16GB
ollama pull deepseek-r1:7b       # 4.7 GB, needs 16GB
```

### Route Through LiteLLM

Add to your `litellm` config.yaml:

```yaml
  - model_name: llama3.2
    litellm_params:
      model: ollama/llama3.2:3b
      api_base: http://192.168.1.137:11434
```

### Open WebUI (Browser Chat Interface)

```bash
docker run -d --name open-webui --restart unless-stopped \
  -p 3000:8080 -v open-webui-data:/app/backend/data \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --add-host host.docker.internal:host-gateway \
  ghcr.io/open-webui/open-webui:main
```

### Safety

**Never expose Ollama on port 11434 to the open internet** — it has no authentication. Use a firewall, VPN, SSH tunnel, or nginx reverse proxy with auth:

```bash
sudo ufw allow from 192.168.1.0/24 to any port 11434 comment "Ollama LAN"
sudo ufw default deny incoming
sudo ufw --force enable
```

### Model Selection Guide (CPU)

| Model | Size | RAM needed | Best for | Tokens/s |
|-------|------|------------|----------|----------|
| llama3.2:3b | 2.0 GB | 8 GB | Chat, fast responses | ~20-30 t/s |
| mistral:7b-instruct-q4_K_M | 4.4 GB | 12 GB | All-rounder | ~8-12 t/s |
| deepseek-r1:7b | 4.7 GB | 14 GB | Reasoning, STEM | ~6-10 t/s |

For a 16GB host with 3 models loaded: ~11 GB disk for models, ~4-5 GB RAM when serving one at a time.

### Full Reference

See `references/ollama-reference.md` for:
- Proxmox VM integration (QEMU guest agent, cloud-init VM creation)
- System monitoring health check script
- Python `pip` on Ubuntu cloud images
- SSH host key remediation after VM rebuild
