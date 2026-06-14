---
name: cloudflare-dns-management
description: "Manage Cloudflare DNS zones, records, API tokens, tunnel routing, and programmatic email sending — create/update/delete DNS records, authenticate with API tokens, install cloudflared, configure Cloudflare Tunnel for permanent HTTPS, and send emails from custom domains via Gmail SMTP relay."
version: 1.3.0
author: Hermes Agent
---

# Cloudflare DNS Management

Use this skill when setting up DNS records on Cloudflare, configuring API tokens for automation, or deploying Cloudflare Tunnel (cloudflared) for permanent HTTPS access to self-hosted services.

## Overview

Three layers of Cloudflare integration, from basic to full-featured:

1. **DNS Records via API** — basic A/AAAA/CNAME/TXT/MX record management with an API token
2. **Cloudflare Tunnel (quick)** — `cloudflared tunnel --url` for instant HTTPS without opening ports
3. **Cloudflare Tunnel (named)** — persistent tunnel with stable `cfargotunnel.com` hostname for DNS CNAME

## Prerequisites

```
# Install cloudflared (when sudo is unavailable)
mkdir -p ~/.local/bin
curl -fsSL -o ~/.local/bin/cloudflared \
  "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
chmod +x ~/.local/bin/cloudflared
~/.local/bin/cloudflared version

# Verify API token
curl -s -X GET "https://api.cloudflare.com/client/v4/user/tokens/verify" \
  -H "Authorization: Bearer $CLOUDFLARE_TOKEN" | python3 -m json.tool
```

## Cloudflare API Permissions

### Token Scopes

When creating an API token in the Cloudflare dashboard, pick the relevant scopes:

| Task | Required Permissions |
|------|---------------------|
| DNS records only | `Zone > DNS > Edit` |
| DNS + Email Routing | `Zone > DNS > Edit` + `Zone > Email Routing > Edit` |
| DNS + Cloudflare Tunnel | `Zone > DNS > Edit` + `Account > Cloudflare Tunnel > Edit` |
| DNS + domain registration | `Zone > DNS > Edit` + `Account > Billing > Read` + `Account > Domain Registration > Read` |
| List zones / accounts | `Zone > Read` + `Account > Read` |
| All of the above + Tunnel management | `Zone > DNS > Edit` + `Account > Cloudflare Tunnel > Edit` |

### Token Prefix Quick Reference

| Prefix | Type | Can access API? |
|--------|------|-----------------|
| `cfut_` | Cloudflare User Token (API token) | ✅ Per scopes configured |
| `eyJ...` (JWT) | Tunnel secret / origin cert | ❌ cloudflared only |

If the user says "don't you already have a token" — check for `cfut_` prefixed values in vault/env BEFORE checking tunnel secrets. Tunnel secrets (`eyJ...`) are NOT API tokens.

### Token Scope Discovery Procedure

When given a Cloudflare API token with unknown scope, discover its capabilities step by step:

**Step 1: Verify the token is active**
```bash
curl -s -X GET "https://api.cloudflare.com/client/v4/user/tokens/verify" \
  -H "Authorization: Bearer $TOKEN"
```
If this returns `"success": false`, the token is invalid or expired. Stop.

**Step 2: Try listing zones**
```bash
curl -s -X GET "https://api.cloudflare.com/client/v4/zones" \
  -H "Authorization: Bearer $TOKEN"
```
- **Empty list** (`"result": []`) — token has DNS:Edit scoped to specific zones, NOT account-level read. You can still manage DNS but only on zones you know the ID of.
- **Error** — token lacks Zone:Read. You can still write DNS records if you know the zone ID.
- **Has results** — full access. Note the zone IDs and account IDs.

**Step 3: Try writing a DNS record on a known zone**
```bash
ZONE_ID="<known-zone-id>"
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"A","name":"cf-test","content":"192.0.2.1","ttl":120,"proxied":false}'
```
Success = DNS write works. Clean up the test record with DELETE.

**Step 4: Try Email Routing (only if you need it)**
```bash
curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/email/routing" \
  -H "Authorization: Bearer $TOKEN"
# Error 10000 = token lacks Email Routing scope. DNS:Edit token cannot enable Email Routing.
```

**Step 5: Try creating a tunnel** (only if you need one)
```bash
ACCOUNT_ID="<account-id>"
curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/cfd_tunnel" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"test-tunnel","tunnel_secret":"'$(openssl rand -hex 32)'"}'
```
- **Error 7003** (`Could not route to /client/v4/accounts/cfd_tunnel`) — token lacks `Account > Cloudflare Tunnel > Edit`. Cannot create named tunnels. Fall back to quick tunnel mode or localhost.run.
- **Success** — delete the test tunnel.

**Common token patterns:**
- A token with only `Zone > DNS > Edit` CAN: verify itself, write DNS records, read zone info (but not list zones)
- A token with only `Zone > DNS > Edit` CANNOT: list accounts, create tunnels, read account info, read domain registration, access Email Routing API
- A token with only `Zone > DNS > Edit` can still be very useful — point DNS A/CNAME/MX/TXT records at your services

### Important: Private IP Limitation

**DNS A records pointing to private LAN IPs (RFC 1918) CANNOT use `proxied: true` (orange cloud).**

```bash
# This will FAIL with error code 9003:
# 'Target 192.168.1.121 is not allowed for a proxied record.'
```

**Two workarounds:**
1. **Cloudflare Tunnel** (named, requires Tunnel API permissions) — creates a `cfargotunnel.com` CNAME target that CAN be proxied
2. **DNS-only mode** (`proxied: false`) — works but exposes your private IP to anyone who does a DNS lookup, and provides no SSL

## Email Routing DNS Setup

See `references/email-dns-records.md` for the full guide. Key points:

- MX records point at `mx1.email.cloudflare.net` / `mx2.email.cloudflare.net` (priority 10 and 20) — but the dashboard auto-adds `route1/2/3.mx.cloudflare.net` with different priorities
- SPF record: `v=spf1 include:_spf.email.cloudflare.net ~all` (manual) or `v=spf1 include:_spf.mx.cloudflare.net ~all` (auto-added by dashboard)
- **Email Routing requires dashboard activation** — DNS:Edit token alone cannot enable it
- For sending emails from a custom domain, you need a separate SMTP relay. See `references/gmail-smtp-relay.md` for the Gmail SMTP + App Password approach (relay from hermes@montygroup.uk through any Gmail account).

## Working with Zones

### Getting Zone ID

```bash
# From zone list (if token has Zone:Read)
curl -s -X GET "https://api.cloudflare.com/client/v4/zones" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for z in d.get('result',[]):
    print(f\"{z['name']}: {z['id']}\")
"

# Check if a specific zone is managed
curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=example.com" \
  -H "Authorization: Bearer $TOKEN"
```

### List Existing Records

```bash
ZONE_ID="<zone-id>"

curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for r in d.get('result',[]):
    print(f\"  {r['type']:5} {r['name']:40} -> {r['content']} (id={r['id'][:12]})\")
"
```

### DNS Record CRUD

```bash
TOKEN="<token>"
ZONE_ID="<zone-id>"

# CREATE an A record
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"A","name":"subdomain","content":"192.168.1.229","ttl":120,"proxied":false}'

# CREATE an MX record (email routing)
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"MX","name":"example.com","content":"mx1.email.cloudflare.net","priority":10,"ttl":120,"proxied":false}'

# CREATE a TXT SPF record
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"TXT","name":"example.com","content":"v=spf1 include:_spf.email.cloudflare.net ~all","ttl":120,"proxied":false}'

# CREATE a CNAME record (for Cloudflare Tunnel)
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"CNAME","name":"mc","content":"<tunnel-id>.cfargotunnel.com","ttl":120,"proxied":true}'

# UPDATE a record (by its ID)
curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"<new-ip>","ttl":120}'

# DELETE a record
curl -s -X DELETE "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID" \
  -H "Authorization: Bearer $TOKEN"

# DELETE ALL records of a type
for rec_id in $(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?type=CNAME" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for r in d.get('result', []):
    print(r['id'])
"); do
  curl -s -X DELETE "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$rec_id" \
    -H "Authorization: Bearer $TOKEN" > /dev/null
done
```

## Cloudflare Tunnel Setup

### Method A: Quick Tunnel (no Tunnel API needed)

A dynamic tunnel for temporary HTTPS access. No named tunnel, no cert needed — just runs `cloudflared tunnel --url`.

```bash
# Start tunnel pointing at a local server
~/.local/bin/cloudflared tunnel --url http://localhost:8000 --no-autoupdate

# The tunnel gets a random cfargotunnel.com hostname
# WITHOUT Tunnel API permissions, you cannot CNAME DNS records to it,
# so this is pure instant HTTPS preview (like localhost.run but via Cloudflare edge)
```

**Limitations:**
- Random hostname per session — not permanent
- Cannot create CNAME records to it without Tunnel API permissions
- Good for one-off testing

### Method B: Named Tunnel (requires Tunnel API permissions)

Creates a persistent tunnel you can route DNS records to. Needs `Account > Cloudflare Tunnel > Edit` in the API token.

#### Standard flow (browser login available)

```bash
# Step 1: Log in (browser-based)
~/.local/bin/cloudflared tunnel login

# Step 2: Create tunnel
~/.local/bin/cloudflared tunnel create my-tunnel-name

# Step 3: Route DNS to it
~/.local/bin/cloudflared tunnel route dns my-tunnel-name subdomain.yourdomain.com

# Step 4: Create config file
mkdir -p ~/.cloudflared
cat > ~/.cloudflared/config.yml << 'EOF'
tunnel: <tunnel-uuid>
credentials-file: /home/user/.cloudflared/<tunnel-uuid>.json
ingress:
  - hostname: subdomain.yourdomain.com
    service: http://localhost:8000
  - service: http_status:404
EOF

# Step 5: Run the tunnel
~/.local/bin/cloudflared tunnel run my-tunnel-name
```

#### API-only flow (no browser login, just an API token)

When you only have an API token (no way to run `cloudflared tunnel login`), create the tunnel entirely via the Cloudflare REST API. The key insight: the credentials file must contain a `TunnelSecret` that is the **32-byte hex secret** you passed at creation time (not the JWT from the `/token` endpoint).

**IMPORTANT:** `cloudflared tunnel run --api-token <token> <name>` does NOT work — cloudflared's CLI has no `--api-token` flag on `tunnel run`. It interprets the token as flags and just prints help. You MUST use the credentials file approach below.

**Step 1: Create the tunnel via API with a stored secret**

```bash
TOKEN="<api-token>"
ACCOUNT_ID="<account-id>"

# Generate and SAVE this secret — you'll need it again
TUNNEL_SECRET=$(openssl rand -hex 32)
echo "Secret: $TUNNEL_SECRET"

curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/cfd_tunnel" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"my-tunnel\",\"tunnel_secret\":\"$TUNNEL_SECRET\"}"
```

**Step 2: Save the credentials file** (format cloudflared expects)

```json
{
  "AccountTag": "<account-id>",
  "TunnelID": "<tunnel-uuid-from-create-response>",
  "TunnelSecret": "<same-hex-secret-from-step-1>"
}
```

Save to `~/.cloudflared/<tunnel-uuid>.json`.

**CRITICAL: The TunnelSecret MUST be the hex string from Step 1, not the JWT from the `/token` endpoint.** Using the JWT token causes `"Unauthorized: Invalid tunnel secret"` errors on every connection attempt. The credentials file authenticates the client via the pre-shared secret.

**Step 3: Route DNS records to the tunnel**

Point CNAME records at `<tunnel-uuid>.cfargotunnel.com` with `proxied: true`:

```bash
ZONE_ID="<zone-id>"
TUNNEL_ID="<tunnel-uuid>"

for sub in subdomain1 subdomain2; do
  curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"type\":\"CNAME\",\"name\":\"$sub\",\"content\":\"$TUNNEL_ID.cfargotunnel.com\",\"ttl\":120,\"proxied\":true}"
done
```

**Step 4: Create ingress config with mixed backends**

Ingress rules match hostnames top-to-bottom. You can route different subdomains to different local services:

```bash
mkdir -p ~/.cloudflared
cat > ~/.cloudflared/config.yml << INGRESS
tunnel: $TUNNEL_ID
credentials-file: /home/user/.cloudflared/${TUNNEL_ID}.json
ingress:
  - hostname: childminding.yourdomain.com
    service: http://192.168.1.229:80      # LXC container (nginx)
  - hostname: mc.yourdomain.com
    service: http://localhost:8000         # Flask on same host
  - hostname: energy.yourdomain.com
    service: http://localhost:8000         # Flask on same host
  - service: http_status:404
INGRESS
```

**Step 5: Run the tunnel**

```bash
~/.local/bin/cloudflared tunnel run my-tunnel-name
```

#### Background / persistence on systems without systemd

On environments without systemd (containers, Proxmox LXC, etc.), use a watchdog script + cron:

**Step 1: Create a watchdog script**
```bash
cat > ~/.hermes/scripts/tunnel-watchdog.sh << 'EOF'
#!/bin/bash
export PATH="$HOME/.local/bin:$PATH"
TUNNEL_NAME="hermes-dev"
if ! pgrep -f "cloudflared.*run $TUNNEL_NAME" > /dev/null; then
  $HOME/.local/bin/cloudflared tunnel run "$TUNNEL_NAME" 2>&1 &
fi
EOF
chmod +x ~/.hermes/scripts/tunnel-watchdog.sh
```

**Step 2: Schedule as a Hermes cron job**
```bash
hermes cron create \
  --name "Tunnel Watchdog" \
  --schedule "every 5m" \
  --script tunnel-watchdog.sh \
  --no-agent
```

**Step 3: Also add a systemd service if available**
```bash
cat > ~/.config/systemd/user/cloudflared-tunnel.service << 'EOF'
[Unit]
Description=Cloudflare Tunnel
After=network.target

[Service]
ExecStart=%h/.local/bin/cloudflared tunnel run my-tunnel-name
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user enable cloudflared-tunnel
systemctl --user start cloudflared-tunnel
```

### Recreating a Tunnel (delete + create)

When you need to delete and recreate (e.g., lost the tunnel secret):

```bash
TOKEN="<api-token>"
ACCOUNT_ID="<account-id>"
OLD_TUNNEL_ID="<old-uuid>"

# Delete old tunnel
curl -s -X DELETE "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/cfd_tunnel/$OLD_TUNNEL_ID" \
  -H "Authorization: Bearer $TOKEN"

# Create new tunnel with a fresh secret
TUNNEL_SECRET=$(openssl rand -hex 32)
curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/cfd_tunnel" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"my-tunnel\",\"tunnel_secret\":\"$TUNNEL_SECRET\"}"

# Then update DNS CNAME records to point to the new tunnel UUID,
# and update the ingress config + credentials file
```

## Integrating with Self-Hosted Services

### Pattern: LXC Container + Cloudflare DNS

For a Proxmox LXC container running nginx on a LAN IP:

```bash
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"A","name":"childminding","content":"192.168.1.229","ttl":120,"proxied":true}'
```

Setting `proxied: true` enables Cloudflare's proxy (orange cloud), which provides DDoS protection, SSL, and hides the origin IP. Setting `proxied: false` is a DNS-only (grey cloud) record.

### Pattern: Local Tunnel + Cloudflare DNS

For a local server behind a dynamic IP or CGNAT, use a tunnel:

```bash
~/.local/bin/cloudflared tunnel --url http://localhost:8000 --no-autoupdate

# Once named tunnel is set up, create a CNAME:
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer *** \
  -H "Content-Type: application/json" \
  -d '{"type":"CNAME","name":"mc","content":"<tunnel-id>.cfargotunnel.com","ttl":120,"proxied":true}'
```

## Programmatic Email Sending

After Email Routing is configured in the Cloudflare dashboard and MX/SPF records are set up (see `references/email-dns-records.md`), use this section to send programmatic emails FROM your custom domain THROUGH Gmail SMTP relay.

### Prerequisites

- Cloudflare Email Routing enabled + MX/SPF/DKIM records in place (via dashboard)
- Gmail account with **2-Step Verification** enabled
- **App Password** generated at https://myaccount.google.com/apppasswords (select Mail + Other, name it, copy the 16-char password)

### Gmail SMTP Settings

| Setting | Value |
|---------|-------|
| Host | `smtp.gmail.com` |
| Port | `587` (STARTTLS) |
| User | Full Gmail address |
| Password | App Password (16 chars, keep internal spaces) |

### Method A: Python smtplib (Recommended)

Save as `~/.hermes/scripts/send-email.py`:

```python
import smtplib, ssl, os
from email.mime.text import MIMEText

CONFIG = {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "address": os.environ.get("EMAIL_ADDRESS", ""),
    "password": os.environ.get("EMAIL_PASSWORD", ""),
    "default_to": os.environ.get("EMAIL_DEFAULT_TO", "user@example.com"),
}

def send_email(to, subject, body):
    msg = MIMEText(body, _charset="utf-8")
    msg["From"] = f"Your Bot Name <{CONFIG['address']}>"
    msg["To"] = to
    msg["Subject"] = subject
    ctx = ssl.create_default_context()
    with smtplib.SMTP(CONFIG["smtp_host"], CONFIG["smtp_port"], timeout=60) as s:
        s.starttls(context=ctx)
        s.login(CONFIG["address"], CONFIG["password"])
        s.sendmail(CONFIG["address"], [to], msg.as_string())

# One-liner for quick sends:
python3 -c "
import smtplib, ssl
from email.mime.text import MIMEText
msg = MIMEText('Body')
msg['From'] = 'Bot <bot@yourdomain.com>'
msg['To'] = 'you@example.com'
msg['Subject'] = 'Subject'
with smtplib.SMTP('smtp.gmail.com', 587, timeout=60) as s:
    s.starttls(context=ssl.create_default_context())
    s.login('sender@gmail.com', '<app-password>')
    s.sendmail('bot@yourdomain.com', ['you@example.com'], msg.as_string())
"
```

**⚠️ Timeout:** Gmail SMTP can be slow (5-30 seconds). Always use `timeout=60`.

### Method B: msmtp (Lightweight CLI)

```bash
sudo apt-get install -y msmtp msmtp-mta
```

Config at `~/.msmtprc` (chmod 600):
```toml
defaults
auth on
tls on
tls_starttls on
tls_trust_file /etc/ssl/certs/ca-certificates.crt

account gmail
host smtp.gmail.com
port 587
from bot@yourdomain.com
user sender@gmail.com
password <app-password>

account default : gmail
logfile ~/.hermes/logs/msmtp.log
```

Usage:
```bash
echo "Body text" | msmtp recipient@example.com
```

**Pitfall:** msmtp lacks a `--timeout` flag. If it hangs, use the Python method instead.

### Custom From Address

Gmail SMTP allows a custom `From` header even though the envelope sender is the Gmail address:
```python
msg["From"] = "Bot Name <bot@yourdomain.com>"
msg["Reply-To"] = "bot@yourdomain.com"
```

Set the envelope sender too for cleaner headers:
```python
server.sendmail("bot@yourdomain.com", [to], msg.as_string())
```

### Vault Integration

Store credentials in the Hermes vault:
```bash
hermes-vault set EMAIL_ADDRESS "sender@gmail.com"
hermes-vault set EMAIL_PASSWORD "xxxx xxxx xxxx xxxx"
```

For msmtp config, write the password directly (file is 0600). For Python, read from vault at runtime:
```python
import subprocess
addr = subprocess.run(["hermes-vault", "get", "EMAIL_ADDRESS"], capture_output=True, text=True).stdout.strip()
pwd = subprocess.run(["hermes-vault", "get", "EMAIL_PASSWORD"], capture_output=True, text=True).stdout.strip()
```

### Deliverability Testing

If emails land in spam:
1. Check SPF includes `_spf.email.cloudflare.net` or the relay domain
2. Verify DKIM is set up (Cloudflare dashboard auto-generates the key if Email Routing is enabled)
3. Add DMARC: `v=DMARC1; p=none`
4. Warm up reputation by sending low volumes initially

### Pitfalls
- **Gmail App Passwords require 2FA** — account MUST have 2-Step Verification enabled
- **App Password includes spaces** — use as-is (`xxxx xxxx xxxx xxxx`) in smtplib.login()
- **SMTP timeout on first send** — Gmail can take 10-30 seconds. Use `timeout=60`.
- **MX + CNAME cannot coexist at apex** — DNS RFC prohibits this. Always check for apex CNAME before adding MX records.
- **Cloudflare dashboard + Email Routing: API-only cannot enable** — DNS:Edit token cannot enable Email Routing. The dashboard button is required.

## Pitfalls

1. **Token scopes are restrictive** — A token with only `Zone > DNS > Edit` CANNOT list accounts, create tunnels, query domain registration, or access Email Routing API. Adding `Zone > Read` and `Account > Read` makes it more introspectable without giving dangerous write permissions.

2. **Token vs Origin Cert** — cloudflared can be used two ways: (a) with an origin cert (from `cloudflared tunnel login` browser flow) for full tunnel management, or (b) with `--url` flag for quick tunnels with no cert needed.

3. **Quick tunnel is not permanent** — `cloudflared tunnel --url` creates a dynamic connection with a random hostname you cannot route DNS to unless you have Tunnel API scopes. Use it like localhost.run for previews, not production.

4. **DNS `proxied: true` requires Cloudflare nameservers** — the domain must use Cloudflare as its authoritative DNS provider for the orange cloud to work. If the domain is on another DNS provider, use `proxied: false`.

5. **DNSSEC conflicts** — If the domain has DNSSEC enabled at the registrar AND Cloudflare has proxy enabled, DNS resolution may break. Resolve by disabling DNSSEC at the registrar or using DNS-only mode.

6. **TTL minimum** — Cloudflare's minimum TTL is 120 seconds. Lower values are silently clamped to 120.

7. **RDAP/WHOIS check failures** — The `.dev` TLD registry may block RDAP queries. Checking DNS (NXDOMAIN via nslookup) is a practical alternative for availability screening, but not authoritative. Only the registrar checkout flow is definitive.

8. **Sudo-free cloudflared install** — On environments without sudo (containers, shared hosts), install to `~/.local/bin/` and ensure it's in `PATH`.

9. **Credentials file secret mismatch** — The `TunnelSecret` in the credentials file (`~/.cloudflared/<uuid>.json`) must be the **32-byte hex string** you passed as `tunnel_secret` when creating the tunnel via the API. It is NOT the JWT token from the `/token` endpoint. Using the wrong secret produces "Unauthorized: Invalid tunnel secret" errors that loop forever. Fix: delete the tunnel, recreate with a known hex secret, and save it in the credentials file.

10. **Apex CNAME + local DNS resolution** — A CNAME record on the zone apex (`@` / `montygroup.uk`) resolving to `<tunnel-id>.cfargotunnel.com` works from the public internet but fails with "Could not resolve host" when tested from inside your local network. This is because your router's DNS (typically 192.168.1.254) doesn't forward or recurse to Cloudflare's authoritative nameservers for domains it doesn't natively know about. The subdomains (`mc.montygroup.uk`) work fine because Cloudflare's edge DNS handles them. **This is not a bug** — the site works from outside your network. Three fixes:
    - Access via subdomains from inside your network (they work)
    - Add entries to your router's local DNS or `/etc/hosts` pointing to the server's LAN IP
    - Test from a mobile device on cellular data to verify external access

12. **Vercel CNAME-at-apex + Email Routing conflict** — A CNAME record at the domain apex (common with Vercel deployments via `cname.vercel-dns.com`) DNS-conflicts with MX records. Cloudflare's Email Routing checker will show "misconfigured" even after adding proper MX/SPF records. Fix: delete the apex CNAME and add proxied A records for Vercel's static IPs (`76.76.21.21`, `76.76.21.98`). See `references/email-dns-records.md` for the exact API calls and workflow.\n\n13. **Email Routing prefers dashboard-driven DNS setup** — Do NOT add MX/SPF records via API before enabling Email Routing in the dashboard. The dashboard's "Add records and finish" button auto-creates them. Manual records cause Cloudflare to report "dns not configured" or "misconfigured". If you added them manually, delete them first, then click the dashboard button to let Cloudflare recreate them.

14. **Tunnel port must match an actual listening service** — The ingress `service: http://localhost:PORT` must point to a port that is actually listening. Before configuring the tunnel, verify with `ss -tlnp | grep <PORT>` that something is listening. A tunnel pointed at a dead port produces HTTP 530 errors from Cloudflare with no useful diagnostics.

15. **"Unauthorized: Tunnel not found" = stale/deleted tunnel** — If cloudflared connects to the edge but gets `"Unauthorized: Tunnel not found"`, the tunnel was deleted from the Cloudflare dashboard or the credentials file references a tunnel ID that no longer exists. Fix: recreate the tunnel (see Recreating a Tunnel section) and update the config. The existing DNS records pointing at the old tunnel UUID will also need updating.

16. **Tunnel credentials can survive tunnel deletion** — The credentials file (`~/.cloudflared/<uuid>.json`) and config.yml persist even after the tunnel is deleted from Cloudflare's side. On next `tunnel run`, cloudflared connects to the edge successfully but gets "Unauthorized: Tunnel not found". Verify tunnel existence with the API: `curl -s "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/cfd_tunnel" -H "Authorization: Bearer $TOKEN"`. If the token lacks `Account > Cloudflare Tunnel > Edit`, you can't verify via API — the user needs to check the Cloudflare dashboard under Zero Trust → Networks → Tunnels.

18. **Edge compression and BREACH attack** — Cloudflare applies automatic compression (Brotli/GZIP) to HTTPS responses by default. For sites with no user input reflection (static sites), BREACH is not exploitable. For dynamic sites that reflect user input alongside secrets, BREACH is a real risk. Mitigations:
    - Add a restrictive CSP (prevents response size oracle attacks)
    - Disable compression on sensitive endpoints via Cloudflare Page Rules (not possible for static sites on Vercel)
    - Add random bytes to response bodies (CSRF tokens, nonces, random padding)

19. **`cloudflared tunnel login` process must stay alive for callback** — `cloudflared tunnel login` opens a browser URL and then waits for Cloudflare to redirect back to a local callback server. **The process MUST stay running** to receive this callback. Common failure modes:
    - **Headless/remote terminal**: The URL is printed to stdout, but the process appears to hang. You must give the user the URL and wait for them to open it while the process runs in the foreground (or in a background PTY process). If it times out, restart with `~/.local/bin/cloudflared tunnel login`.
    - **Background process without PTY**: In `terminal(background=true)` without PTY mode, the URL isn't generated because the interactive prompt never fires. Always use foreground mode or `pty=true` for login.
    - **Cert not generated**: After successful login, the cert is saved as `~/.cloudflared/cert.pem`. Verify with `ls -la ~/.cloudflared/cert.pem`. If it's missing, the callback was never received.
    - **Workaround without browser**: If no browser is available, use the API-only flow (see above) with an API token that has `Account > Cloudflare Tunnel > Edit` scope. This bypasses the browser login entirely.
