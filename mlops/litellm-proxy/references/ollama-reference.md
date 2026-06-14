# Ollama — Local Inference Reference

## Proxmox VM Integration

### QEMU Guest Agent

If running in a Proxmox VM, install the guest agent so Proxmox can detect the IP, issue graceful reboots, and exec commands:

```bash
sudo apt-get install -y qemu-guest-agent
sudo systemctl start qemu-guest-agent
```

**Pitfall:** `systemctl enable qemu-guest-agent` fails — the Ubuntu cloud image package has no `[Install]` section. The service is activated automatically by virtio-serial udev on reboot. Only `start` is needed.

### Cloud-init VM Creation

For creating a fresh VM from a cloud image (using Proxmox's built-in cloud-init), the key steps are: `qm create` → `qm importdisk` → `qm set` with cloud-init config → `qm resize` → `qm start`.

## System Monitoring Health Check Script

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

## Python pip on Ubuntu Cloud Images

The base Ubuntu Server cloud image often lacks pip:

```bash
sudo apt-get install -y python3-pip
python3 -m pip install --user --break-system-packages <pkg>
```

## SSH Host Key Remediation After VM Rebuild

When you delete and recreate a VM, SSH warns of host key mismatch:

```bash
ssh-keygen -f ~/.ssh/known_hosts -R <vm-ip>
```

## Model Management Commands

```bash
ollama list                        # All pulled models
ollama rm <model>                  # Remove a model
ollama show <model> --modelfile    # Show model config
ollama show <model> --license      # Show license
```

Model download directory: `~/.ollama/models/`. Monitor with `du -sh ~/.ollama/`.

## Memory Pressure

Loading multiple large models simultaneously can OOM a 16GB host. Reduce `OLLAMA_KEEP_ALIVE` on memory-constrained machines. Default is 5 minutes — lower to 1m or 0 to unload immediately after each request.

## API Endpoints

Chat completion (OpenAI-compatible):
```
POST /v1/chat/completions
```
```bash
curl -s http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.2:3b", "messages": [{"role": "user", "content": "Hello!"}], "stream": false}'
```

Generate (non-chat):
```
POST /api/generate
```
```bash
curl -s http://localhost:11434/api/generate \
  -d '{"model":"mistral:7b-instruct-q4_K_M","prompt":"What is 2+2?","stream":false}'
```

## Verification

```bash
curl -s http://localhost:11434/api/tags
# Returns {"models":[...]}
curl -s http://localhost:11434/
# Returns "Ollama is running"
```
