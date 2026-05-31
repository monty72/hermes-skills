---
name: ollama-server
description: Deploy, configure, and manage a self-hosted Ollama inference server on Linux — install, pull models, serve via OpenAI-compatible API, deploy Open WebUI frontend, secure with firewall, monitor health, and manage model lifecycle.
version: 1.0.0
author: Hermes Agent
---
# Ollama Server

Use this skill when setting up or managing a **self-hosted LLM inference server using Ollama** on a Linux machine (CPU or GPU).

Ollama wraps llama.cpp under the hood but provides a much simpler model-management lifecycle (`pull`, `run`, `list`, `rm`) and an OpenAI-compatible REST API out of the box.

**When to use this vs. other inference approaches:**
- **Ollama** (this skill) — easiest CPU setup, model management built-in, good for general chat/code. Best for 3B–14B params on CPU, or 7B–70B on GPU.
- **llama.cpp** (`llama-cpp` skill) — finer control over GGUF quant selection, direct server process, advanced features (speculative decoding, grammar constraints, LoRA).
- **vLLM** (`serving-llms-vllm` skill) — GPU-optimized production serving, PagedAttention, best for high-throughput/high-concurrency.

## Install

### Quick install (Linux)

```bash
curl -fsSL https://ollama.com/install.sh | bash
```

This adds the Ollama systemd service, creates the `ollama` user, and starts the service on `127.0.0.1:11434`.

**WARNING:** The install script detects GPU drivers (NVIDIA, AMD) but defaults to CPU-only if none are found. On a CPU-only machine you'll see `WARNING: No NVIDIA/AMD GPU detected. Ollama will run in CPU-only mode.` — this is expected and fine.

### Post-install: user groups

The install script adds `ollama` to `render` and `video` groups and adds the current user to the `ollama` group. You may need to log out and back in for the group change to take effect.

## Configuration

### Listen on all interfaces (for remote API access)

By default Ollama binds to `127.0.0.1:11434` (localhost only). To allow other machines on the LAN to reach it:

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

**`OLLAMA_KEEP_ALIVE=5m`** — keeps models loaded in memory for 5 minutes after the last request, avoiding reload latency. Tune up for steady usage or down for memory-constrained setups.

### Verify the API is running

```bash
curl -s http://localhost:11434/api/tags
# Returns {"models":[]} on first install
curl -s http://localhost:11434/
# Returns "Ollama is running"
```

## Model Management

### Pull models

```bash
# Small/fast chat (2 GB) — runs on any machine with 8GB+ RAM
ollama pull llama3.2:3b

# Strong all-rounder 7B Q4 (4.4 GB) — needs 16GB RAM
ollama pull mistral:7b-instruct-q4_K_M

# Reasoning/chain-of-thought 7B (4.7 GB) — needs 16GB RAM
ollama pull deepseek-r1:7b

# Larger coding model (4.2 GB)
ollama pull codellama:7b-code

# Pull multiple in background (they download in parallel)
ollama pull llama3.2:3b &
ollama pull mistral:7b &
wait
```

### Model selection guide for CPU inference (16GB RAM host)

| Model | Size | RAM needed | Best for | Tokens/s (CPU) |
|-------|------|------------|----------|-------|
| llama3.2:3b | 2.0 GB | 8 GB | Chat, fast responses | ~20-30 t/s |
| mistral:7b-instruct-q4_K_M | 4.4 GB | 12 GB | All-rounder | ~8-12 t/s |
| deepseek-r1:7b | 4.7 GB | 14 GB | Reasoning, STEM | ~6-10 t/s |
| phi4:14b-q4_K_M | 9.1 GB | 24 GB | Strong quality | ~4-6 t/s |

For a 16GB host with 3 models loaded: expect ~11 GB disk used for models, ~4-5 GB RAM when serving (one model at a time).

### List, remove, inspect

```bash
ollama list                        # All pulled models
ollama rm <model>                  # Remove a model
ollama show <model> --modelfile    # Show model config
ollama show <model> --license      # Show license
```

## API Usage

Ollama exposes an OpenAI-compatible API at `http://<host>:11434/`.

### Chat completion (OpenAI-compatible)

```bash
curl -s http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:3b",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": false
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### Generate (non-chat)

```bash
curl -s http://localhost:11434/api/generate \
  -d '{"model":"mistral:7b-instruct-q4_K_M","prompt":"What is 2+2? Answer in one word.","stream":false}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['response'])"
```

### Using from Python (OpenAI client)

```python
from openai import OpenAI

client = OpenAI(base_url="http://192.168.1.137:11434/v1", api_key="ollama")
resp = client.chat.completions.create(
    model="llama3.2:3b",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(resp.choices[0].message.content)
```

### Using from LiteLLM (multi-provider router)

```python
from litellm import completion
resp = completion(
    model="ollama/llama3.2:3b",
    messages=[{"role": "user", "content": "Hello!"}],
    api_base="http://192.168.1.137:11434"
)
```

## Deploy Open WebUI (Web Chat Interface)

Open WebUI provides a ChatGPT-like browser interface that connects to the local Ollama API.

### Docker deployment

```bash
docker run -d \
  --name open-webui \
  --restart unless-stopped \
  -p 3000:8080 \
  -v open-webui-data:/app/backend/data \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --add-host host.docker.internal:host-gateway \
  ghcr.io/open-webui/open-webui:main
```

**Note:** `host.docker.internal` resolves to the Docker host. If Ollama runs on the same host, this works. If Ollama is on a different server, use its IP instead.

### Verify

```bash
# Health endpoint
curl -s http://localhost:3000/health
# Returns: {"status":true}

# Web UI is at http://<host>:3000
```

## Security

### Firewall rules

```bash
# Allow SSH
sudo ufw allow ssh
sudo ufw --force enable

# Allow Ollama API from LAN
sudo ufw allow from 192.168.1.0/24 to any port 11434 comment "Ollama API"

# Allow Open WebUI
sudo ufw allow 3000 comment "Open WebUI"

# Default deny incoming
sudo ufw default deny incoming
sudo ufw default allow outgoing
```

**Never expose Ollama on port 11434 to the open internet** — it has no authentication. If you need remote access, use a reverse proxy with auth (e.g., nginx + htpasswd, Cloudflare Tunnel, or SSH tunnel).

### System hardening

```bash
sudo apt-get install -y fail2ban unattended-upgrades
sudo dpkg-reconfigure -f noninteractive unattended-upgrades
```

## Proxmox VM Integration

### QEMU Guest Agent

If running in a Proxmox VM, install the guest agent so Proxmox can detect the IP, issue graceful reboots, and exec commands:

```bash
sudo apt-get install -y qemu-guest-agent
sudo systemctl start qemu-guest-agent
```

**Pitfall:** `systemctl enable qemu-guest-agent` fails — the Ubuntu cloud image package has no `[Install]` section. The service is activated automatically by virtio-serial udev on reboot. Only `start` is needed.

### Cloud-init VM creation

For creating a fresh VM from a cloud image (using Proxmox's built-in cloud-init), see the `proxmox-host-creation` skill section "Creating a VM from a Cloud Image (Cloud-Init)". The key steps: `qm create` → `qm importdisk` → `qm set` with cloud-init config → `qm resize` → `qm start`.

## Monitoring

### Quick health check script

Save as `~/scripts/system-status.sh`:

```bash
#!/bin/bash
echo "=== System Status $(date) ==="
echo ""
echo "--- CPU Load ---"
uptime
echo ""
echo "--- Memory ---"
free -h
echo ""
echo "--- Disk ---"
df -h /
echo ""
echo "--- Docker ---"
docker ps --format 'table {{.Names}}\t{{.Status}}' 2>/dev/null
echo ""
echo "--- Ollama Models ---"
ollama list
echo ""
echo "--- Active Connections ---"
ss -tlnp | grep -E ':(22|3000|11434) ' | head -10
```

## Pitfalls

1. **CPU-only warning is not an error** — `WARNING: No NVIDIA/AMD GPU detected.` is expected on CPU machines. Tokens/s will be lower but functional.
2. **`systemctl enable qemu-guest-agent` fails** — the Ubuntu cloud image package has no `[Install]` section. The service auto-starts via udev on reboot. Use `systemctl start` only.
3. **SSH host key changes after rebuild** — when you delete and recreate a VM, SSH warns of host key mismatch. Fix: `ssh-keygen -f ~/.ssh/known_hosts -R <vm-ip>`.
4. **No auth on Ollama API** — never expose port 11434 to the public internet. Use a VPN, SSH tunnel, or authenticate via nginx reverse proxy.
5. **Open WebUI first-boot** — the first request creates an admin account. Sign up with any email/password on a self-hosted instance.
6. **Model download directory** — models store in `~/.ollama/models/`. Monitor with `du -sh ~/.ollama/`.
7. **Memory pressure** — loading multiple large models simultaneously can OOM a 16GB host. Reduce `OLLAMA_KEEP_ALIVE` on memory-constrained machines.
8. **Python `pip` on Ubuntu Server cloud image** — the base image often lacks pip. Install: `sudo apt-get install -y python3-pip`. Use `python3 -m pip install --user --break-system-packages <pkg>` on Ubuntu 24.04+.
