# OpenCrawl Worker Provision Workflow

Session workflow that created VM 104 (opencrawl) on Proxmox pve1 as a remote Hermes worker, then configured it as a fully autonomous managed node.

## VM Creation (Proxmox)

1. Downloaded Ubuntu 24.04 cloud image to `/root/ubuntu-24.04-server-cloudimg-amd64.img`
2. Created VM:
   ```bash
   qm create 104 --name opencrawl --memory 16384 --cores 8 --cpu host \
     --net0 virtio,bridge=vmbr0 --agent enabled=1 --ostype l26
   qm importdisk 104 /root/ubuntu-24.04-server-cloudimg-amd64.img local-lvm
   qm set 104 --scsihw virtio-scsi-pci --scsi0 local-lvm:vm-104-disk-0 --boot order=scsi0
   qm set 104 --ide2 local-lvm:cloudinit
   qm set 104 --ciuser matth --sshkeys <(echo 'ssh-ed25519 <key>') --ipconfig0 ip=dhcp
   qm resize 104 scsi0 50G
   qm start 104
   ```

**Storage pitfall:** `local` storage doesn't support `images` content type. Use `local-lvm:cloudinit` for the cloud-init drive, not `local:cloudinit`.

**SSH key pitfall:** `--sshkey /root/.ssh/authorized_keys` injects the **Proxmox host's** keys, not the agent's. Pass the agent's key explicitly via process substitution.

## Post-Boot Setup

1. Found IP via `nmap -sn 192.168.1.0/24 | grep -B 2 'Proxmox'`
2. Installed qemu-guest-agent: `sudo apt-get install -y qemu-guest-agent && sudo systemctl start qemu-guest-agent`
3. Security hardening: `sudo apt-get install -y ufw fail2ban unattended-upgrades`
4. Docker: `curl -fsSL https://get.docker.com | sudo bash`
5. Re-login for docker group: `newgrp docker` (or new SSH session)
6. Ollama: `curl -fsSL https://ollama.com/install.sh | sudo bash`
7. Models: `ollama pull llama3.2:3b mistral:7b-instruct-q4_K_M deepseek-r1:7b`
8. Open WebUI: Docker container with `OLLAMA_BASE_URL=http://host.docker.internal:11434`
9. Node.js + Playwright: `curl -fsSL https://deb.nodesource.com/setup_22.x | sudo bash -` then `npx playwright install chromium`

## LiteLLM Proxy Connection

- Proxy on main host (192.168.1.121:4000)
- Open WebUI reconfigured: `-e OPENAI_API_BASE_URL=http://192.168.1.121:4000 -e ENABLE_OLLAMA=false`
- Worker Hermes config uses `provider: custom` with base_url pointing to proxy
- Provider gotcha: `provider: openai` fails with "Unknown provider 'openai'" — must use `provider: custom`

## Auto-Approval Configuration

To avoid security prompts when managing the worker:

```bash
hermes config set security.allow_private_urls true
hermes config set approvals.auto_accept_patterns '[
  "ssh matth@192\\.168\\.1\\.137",
  "192\\.168\\.1\\.137",
  "192\\.168\\.1\\.121",
  "litellm --config",
  "health-report\\.sh",
  "opencrawl",
  "\\.hermes-worker",
  "\\.litellm"
]'
```

## Auto-Routing

The main agent autonomously decides when to offload to the worker:
- **Offload:** crawling, scraping, batch processing, heavy ML, long-running compute, Ollama inference
- **Handle locally:** chat, config changes, quick lookups, simple queries

## Cron Jobs

Two Hermes cron jobs maintain the worker autonomously:

| Job | Schedule | Purpose |
|-----|----------|---------|
| Health check (246230cb7135) | Every 30 min | Checks uptime, Docker, Ollama, disk, memory, proxy. Auto-recovers. Silent when healthy. Only alerts on failure. |
| Skills sync (5e9d0516fa7f) | Daily 5 AM | rsync main agent skills → worker. Silent on success. |

Plus a VM-level crontab for auto-updates every Sunday 4 AM.

## Final State

| Metric | Value |
|--------|-------|
| IP | 192.168.1.137 |
| vCPU | 8 (host passthrough) |
| RAM | 16 GB |
| Disk | 50 GB (52% used) |
| Services | Open WebUI:3000, Ollama:11434, Docker, Playwright |
| Hermes | v0.14.0 at ~/.hermes-worker/bin/hermes |
| Config | `~/.hermes-worker-config/config.yaml` (provider: custom, proxy :4000) |
| Skills | 29 synced + 3 worker-specific |
| Memory | `~/.hermes-worker-memory/environment.md` |
| Autonomy level | **Full** — no user approvals needed for management |
