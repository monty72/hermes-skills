# MC Deployment on Web LXC (VM 200)

> **⚠️ DEPRECATED — Data Source Mismatch**  
> The collector runs on the Hermes host and writes `observability.json` to `~/.hermes/data/`.  
> The MC server on the web LXC reads from the same path locally but the file doesn't exist there,  
> so all dashboard data falls back to zeros.  
> **Use the Hermes-host deployment with Basic Auth instead** (see SKILL.md → Deployment Options → Stage 1).  
> The technical details below are preserved as a reference for pct push / nginx / PVE env var patterns.

## Container: web (VMID 200)

- Static IP: 192.168.1.200/24
- Gateway: 192.168.1.1
- OS: Debian 12
- Specs: 1GB RAM, 2 vCPU, 4GB disk
- nginx on port 80 → proxy_pass localhost:8081 (MC Python server)
- SSH with key via `~/.ssh/proxmox` keypair

## Proxmox Host Access

SSH to Proxmox host uses a dedicated key:

```bash
ssh -i ~/.ssh/proxmox root@192.168.1.6
```

This key was generated and added to the Proxmox host's authorized_keys (separate from the `id_ed25519` key used for Hermes VM).

## File Transfer Pattern

Files cannot be written directly to `/var/lib/lxc/200/rootfs/` because unprivileged LXC uses uid mapping. Always use `pct push`:

```bash
# Stage on Proxmox host first
scp -i ~/.ssh/proxmox /path/to/file root@192.168.1.6:/tmp/

# Push into container
ssh -i ~/.ssh/proxmox root@192.168.1.6 "
  pct exec 200 -- mkdir -p /destination/dir
  pct push 200 /tmp/file /destination/dir/file
"
```

## Service Unit

`/etc/systemd/system/mission-control.service` with PVE auth env vars:

```ini
[Unit]
Description=Mission Control Dashboard
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/mission-control/src
Environment=PROXMOX_API_TOKEN=PVEAPIToken=hermes2@pve!api=19b5fd1b-9354-47fd-8847-4ebbe28a4abb
Environment=PROXMOX_URL=https://192.168.1.6:8006/api2/json
ExecStart=/usr/bin/python3 /opt/mission-control/src/server.py
Restart=on-failure
RestartSec=5
Environment=PORT=8081

[Install]
WantedBy=multi-user.target
```

## Nginx Config

`/etc/nginx/sites-available/mission-control`:

```nginx
server {
    listen 80 default_server;
    server_name _;

    location /childminding {
        alias /var/www/childminding;
        index index.html;
    }

    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

The old `childminding` site was at `/etc/nginx/sites-enabled/childminding` and was replaced by the MC config.

## Tunnel

localhost.run tunnel runs from the Hermes VM (192.168.1.121), proxying to 192.168.1.200:80:

```bash
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 \
  -R 80:192.168.1.200:80 nokey@localhost.run
```

The tunnel URL changes each session (anonymous auth).

## Access Points

- **Local network:** http://192.168.1.200/
- **Tunnel:** https://<hash>.lhr.life (current: 5fab49bbe80ee3)

## Service Management

```bash
ssh -i ~/.ssh/proxmox root@192.168.1.6 "
  pct exec 200 -- systemctl daemon-reload
  pct exec 200 -- systemctl restart mission-control.service
  pct exec 200 -- systemctl status mission-control.service
  pct exec 200 -- journalctl -u mission-control -n 20 --no-pager
"
```
