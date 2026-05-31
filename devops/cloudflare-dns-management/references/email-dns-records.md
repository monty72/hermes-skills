# Cloudflare Email Routing — DNS Records Setup

When setting up email for a Cloudflare-managed domain (montygroup.uk or any other), you need three DNS record types. This reference covers the exact API calls.

## Required Records

### 1. MX Records (mail routing)

Route incoming email to Cloudflare's mail servers:

```bash
ZONE_ID="<zone-id>"
TOKEN="<cf-api-token>"

# Primary MX (priority 10)
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"MX","name":"montygroup.uk","content":"mx1.email.cloudflare.net","priority":10,"ttl":120,"proxied":false}'

# Secondary MX (priority 20)
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"MX","name":"montygroup.uk","content":"mx2.email.cloudflare.net","priority":20,"ttl":120,"proxied":false}'
```

### 2. SPF Record (sender policy)

Authorizes Cloudflare to send emails on behalf of the domain:

```bash
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"TXT","name":"montygroup.uk","content":"v=spf1 include:_spf.email.cloudflare.net ~all","ttl":120,"proxied":false}'
```

### 3. DKIM Record (optional, for signing)

Cloudflare Email Routing generates DKIM keys automatically in the dashboard under Email Routing → Settings. Once enabled, copy the DKIM TXT record value from the dashboard and add it:

```bash
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"TXT","name":"<dkim-selector>._domainkey.montygroup.uk","content":"v=DKIM1; k=rsa; p=<public-key>","ttl":120,"proxied":false}'
```

## CNAME-at-Apex Conflict (Vercel / Static Hosting)

**This is the #1 gotcha.** DNS standards forbid both a CNAME and MX record at the domain apex. If your site is hosted on Vercel (which uses a CNAME like cname.vercel-dns.com at the apex), adding MX records for email will silently break — Cloudflare's DNS checker will show "misconfigured" or "dns not configured" because the CNAME blocks the MX records.

**Fix:** Replace the apex CNAME with A records pointing to Vercel's anycast IPs, with proxied: true (orange cloud):

```bash
# Delete the existing apex CNAME first
RECORD_ID=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?name=montygroup.uk&type=CNAME" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result'][0]['id'] if d.get('result') else '')")
curl -s -X DELETE "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID" \
  -H "Authorization: Bearer $TOKEN"

# Add Vercel A records (proxied so Cloudflare edge handles traffic)
for ip in 76.76.21.21 76.76.21.98; do
  curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"type\":\"A\",\"name\":\"montygroup.uk\",\"content\":\"$ip\",\"ttl\":120,\"proxied\":true}"
done
```

The A records with orange-cloud proxying preserve the Vercel site while allowing MX records to coexist. Do not manually add MX/SPF records before enabling Email Routing — Cloudflare's dashboard tries to auto-add them when you click "Get started" and will either fail silently (records already exist) or create duplicates.

## Activation

After resolving any CNAME-at-apex conflict, enable Email Routing in the Cloudflare dashboard:

1. Navigate to **Cloudflare Dashboard → Zone → Email → Email Routing**
2. Click **Get started** or **Enable**
3. Click **Add records and finish** / **Add records and onboard** — this triggers Cloudflare to auto-add the required MX and SPF records
4. Add a destination address (where forwarded emails go)
5. Create a catch-all or specific routing rule

**Important:** Do NOT manually add MX/SPF records before dashboard enablement. The dashboard expects to create them itself. If you added them manually first, delete them, then click the dashboard button to let Cloudflare recreate them properly.

The DNS:Edit API token CANNOT enable Email Routing — that requires either the Cloudflare dashboard or an API token with Zone → Email Routing → Edit scope.

## Token Prefixes

- `cfut_` = Cloudflare User Token (API token). Full REST API access per configured scopes.
- `eyJ...` (JWT format) = Tunnel secrets or origin certificates. Only authenticate cloudflared, NOT the REST API.

## Token Scope Check

To see what a token can do:

```bash
# Verify the token is active
curl -s -X GET "https://api.cloudflare.com/client/v4/user/tokens/verify" \
  -H "Authorization: Bearer $TOKEN"

# Try listing zones (needs Zone:Read)
curl -s -X GET "https://api.cloudflare.com/client/v4/zones" \
  -H "Authorization: Bearer $TOKEN"

# Try Email Routing (needs separate scope)
curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/email/routing" \
  -H "Authorization: Bearer $TOKEN"
# → Error 10000 = token lacks Email Routing scope
```

## Outbound Sending

Cloudflare Email Routing handles **incoming** email only. For **sending** from a custom domain, you need a separate SMTP relay. Common options:

- **Gmail "Send mail as"** — Add the custom address in Gmail settings, verify ownership via DNS TXT record, send via Gmail SMTP. Requires a Gmail account with App Password.
- **Mailgun/SendGrid/Resend** — Free tiers available (100 emails/day), API-based, but require browser-based signup.
- **Cloudflare Workers + send-email binding** — Programmatic sending via Workers, needs Workers subscription.

## SMTP Configuration (msmtp)

Lightweight SMTP client installed at `/usr/bin/msmtp`:

```toml
# ~/.msmtprc
account default
host smtp.gmail.com
port 587
auth on
tls on
tls_starttls on
tls_trust_file /etc/ssl/certs/ca-certificates.crt
from hermes@montygroup.uk
user hermes.bot.agent@gmail.com
password <app-password>
logfile ~/.hermes/logs/msmtp.log
```

Python smtplib script at `~/scripts/hermes-email.py`:
```bash
python3 ~/scripts/hermes-email.py "recipient@example.com" "Subject" << 'EOF'
Body text here
EOF
```
