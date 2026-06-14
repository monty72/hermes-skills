#!/bin/bash
# Helper: Provision an LXC container with nginx on Proxmox
# Usage: Run the commands in this script via pct exec on the Proxmox host.
# This is a reference script — the user runs it on their Proxmox shell.
# Replace <VMID> with the container ID and <HERMES_IP> with Hermes VM IP.

set -e

CTID=${1:-<VMID>}
SITENAME=${2:-childminding}
HERMES_IP=${3:-192.168.1.6}
HERMES_PORT=${4:-8000}

echo "=== Installing nginx ===)"
pct exec $CTID -- apt-get update -qq
pct exec $CTID -- apt-get install -y -qq nginx curl

echo "=== Creating site directory ==="
pct exec $CTID -- mkdir -p /var/www/$SITENAME

echo "=== Configuring nginx ==="
pct exec $CTID -- bash -c 'cat > /etc/nginx/sites-available/childminding << EOF
server {
    listen 80;
    server_name _;
    root /var/www/childminding;
    index index.html;
    location / { try_files \$uri \$uri/ =404; }
}
EOF'
pct exec $CTID -- rm -f /etc/nginx/sites-enabled/default
pct exec $CTID -- ln -sf /etc/nginx/sites-available/childminding /etc/nginx/sites-enabled/
pct exec $CTID -- systemctl restart nginx

echo "=== Copying site files ==="
# Pull from Hermes VM and push into container
curl -s "http://${HERMES_IP}:${HERMES_PORT}/childminding.html" > /tmp/${SITENAME}.html 2>/dev/null || \
  curl -s "http://${HERMES_IP}:${HERMES_PORT}/" > /tmp/${SITENAME}.html
if [ -s "/tmp/${SITENAME}.html" ]; then
  pct push $CTID /tmp/${SITENAME}.html /var/www/$SITENAME/index.html
  rm /tmp/${SITENAME}.html
  echo "Files copied successfully."
else
  echo "WARNING: Could not pull files from Hermes VM. Copy manually."
  echo "  pct push $CTID /path/to/index.html /var/www/$SITENAME/index.html"
fi

echo "=== Verifying ==="
IP=$(pct exec $CTID -- hostname -I | awk '{print $1}')
echo "Container IP: $IP"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://$IP/ 2>/dev/null || echo "no response")
echo "HTTP status: $HTTP_CODE"

echo "=== Setup complete ==="
echo "Site: http://${IP}/"
echo ""
echo "To update files later, run from Proxmox shell:"
echo "  curl -s http://${HERMES_IP}:8000/childminding.html > /tmp/site.html"
echo "  pct push $CTID /tmp/site.html /var/www/$SITENAME/index.html"
echo "  rm /tmp/site.html"
