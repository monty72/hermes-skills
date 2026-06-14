# Flask API Deployment to Proxmox LXC

Deploy a Python Flask API with SQLite to a Proxmox LXC container, exposed via nginx reverse proxy. This complements the static-site model — the API runs persistently, and an SPA hosted elsewhere (Vercel, tunnel) calls it.

## Full Deployment Sequence

```bash
# ── 1. Create target directories ──
pct exec <VMID> -- mkdir -p /opt/<project>/data

# ── 2. Transfer files via PVE host ──
scp api.py schema.sql init_db.py pve-host:/tmp/
pct push <VMID> /tmp/api.py /opt/<project>/api.py
pct push <VMID> /tmp/schema.sql /opt/<project>/data/schema.sql
pct push <VMID> /tmp/init_db.py /opt/<project>/init_db.py

# ── 3. Install Python deps ──
pct exec <VMID> -- apt-get install -y python3-pip
pct exec <VMID> -- pip3 install flask flask-cors -q

# ── 4. Init database ──
pct exec <VMID> -- python3 /opt/<project>/init_db.py

# ── 5. Create systemd service ──
pct exec <VMID> -- bash -c 'cat > /etc/systemd/system/<project>.service << "EOF"
[Unit]
Description=<project> API
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/<project>
ExecStart=/usr/bin/python3 /opt/<project>/api.py
Restart=always
RestartSec=5
Environment=PORT=5011

[Install]
WantedBy=multi-user.target
EOF'

pct exec <VMID> -- systemctl daemon-reload
pct exec <VMID> -- systemctl enable <project>
pct exec <VMID> -- systemctl start <project>

# ── 6. Verify ──
pct exec <VMID> -- curl -s http://localhost:5011/api/health
```

## Nginx Reverse Proxy

Add a location block to the container's nginx config to proxy `/api/` to the Flask backend:

```nginx
# In /etc/nginx/sites-available/<site>
server {
    listen 80;
    server_name example.com;

    # API proxy — note: auth_basic OFF
    location /api/ {
        auth_basic off;
        proxy_pass http://127.0.0.1:5011/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # SPA or other sites can coexist
    location / {
        # auth_basic "Restricted";
        # auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://127.0.0.1:8081;
    }
}
```

## Pitfalls

- **auth_basic inheritance**: If the server block sets `auth_basic`, ALL location blocks inherit it. Add `auth_basic off;` explicitly to API locations. Without this, curl returns 401 instead of the expected JSON response.
- **pct push**: Overwrites existing files; no `--force` flag needed.
- **File transfer round-trip**: Copy files to the PVE host first (`scp`), then `pct push` into the container. There's no direct way to push from outside the PVE host.
- **init_db.py path resolution**: When the script is at `/opt/<project>/init_db.py`, use `os.path.dirname(os.path.abspath(__file__))` to get the project directory — NOT a chained `os.path.dirname()` which strips a level too far.
- **systemd WorkingDirectory**: The Flask app's `os.path.dirname(__file__)` resolves relative to the script location, not the working directory. Set `WorkingDirectory` anyway for log file paths and relative imports.
- **RestartSec**: Set to at least 5 to avoid rapid restart loops during DB init or config errors.
