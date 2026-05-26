# Migrating from Cloudflare Tunnel to Vercel

When moving from a Cloudflare Tunnel-based deployment (originally serving static sites from a Flask server on localhost:8000) to a Vercel-based deployment (Astro framework, auto-deploy from GitHub), follow this migration sequence.

## Before/After Architecture

```
Before:                          After:
User → Cloudflare DNS →         User → Cloudflare DNS →
  Tunnel → localhost:8000          Vercel CDN (global)
  (Flask serving HTML+API)        (Astro static HTML)

API stays:                        API moves to:
api.domain.com → Tunnel →         api.domain.com → Tunnel →
  localhost:8000/api/*              localhost:8000/api/*
  (no change)                     (no change — separate subdomain)
```

## Migration Steps

### 1. Deploy Astro site to Vercel first

```bash
cd /path/to/astro-project
npx vercel link --token $VERCEL_TOKEN --yes
npx vercel deploy --prod --token $VERCEL_TOKEN --yes
```

Verify the Vercel URL works before touching DNS.

### 2. Add custom domains to Vercel project

```bash
PROJECT_ID=$(cat .vercel/project.json | python3 -c "import sys,json; print(json.load(sys.stdin)['projectId'])")

# Root domain
curl -X POST "https://api.vercel.com/v10/projects/$PROJECT_ID/domains" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -d '{"name": "yourdomain.uk"}'

# Subdomains
for sub in www mc energy bots childminding dev; do
  curl -X POST "https://api.vercel.com/v10/projects/$PROJECT_ID/domains" \
    -H "Authorization: Bearer $VERCEL_TOKEN" \
    -d "{\"name\": \"${sub}.yourdomain.uk\"}"
done
```

### 3. Update Cloudflare DNS

```bash
CF_TOKEN="Bearer $CF_TOKEN"
ZONE_ID=$(curl -s -H "Authorization: $CF_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones?name=yourdomain.uk" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['result'][0]['id'])")

# List existing records
curl -s -H "Authorization: $CF_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  | python3 -c "import sys,json; [print(f\"{r['id']}: {r['name']} → {r['content']} ({r['type']})\") for r in json.load(sys.stdin)['result']]"

# Update subdomains: CNAME → cname.vercel-dns.com (NOT proxied — DNS-only)
for record_id in <subdomain-record-ids>; do
  curl -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$record_id" \
    -H "Authorization: $CF_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"type":"CNAME","content":"cname.vercel-dns.com","ttl":1,"proxied":false}'
done

# Update apex: CNAME → cname.vercel-dns.com (PROXIED — Cloudflare CNAME flattening)
curl -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$APEX_RECORD_ID" \
  -H "Authorization: $CF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"CNAME","content":"cname.vercel-dns.com","ttl":1,"proxied":true}'
```

### 4. Add API subdomain back to tunnel

Create a new CNAME record for the API and update the tunnel ingress config:

```bash
# DNS for API
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: $CF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"CNAME","name":"api.yourdomain.uk","content":"<tunnel-id>.cfargotunnel.com","ttl":1,"proxied":true}'

# Tunnel config (config.yml)
tunnel: <tunnel-id>
credentials-file: /home/user/.cloudflared/<tunnel-id>.json
ingress:
  - hostname: api.yourdomain.uk
    service: http://localhost:8000
  - service: http_status:404
```

### 5. Restart tunnel

```bash
pkill -f "cloudflared tunnel"
cloudflared tunnel --config ~/.cloudflared/config.yml run
```

### 6. Verify

```bash
curl -sI https://yourdomain.uk          # Should return 200 from Vercel
curl -sI https://api.yourdomain.uk       # Should return 200 from tunnel
```

## DNS Rule Summary

| Record | Target | Proxied | Reason |
|--------|--------|---------|--------|
| Apex (`domain.uk`) | `cname.vercel-dns.com` | Yes (orange) | Cloudflare CNAME flattening — allows CNAME at root |
| Subdomains (`www`, `mc`, etc.) | `cname.vercel-dns.com` | No (grey) | Vercel handles SSL; two layers of TLS (Cloudflare + Vercel) causes issues |
| API subdomain | `<tunnel-id>.cfargotunnel.com` | Yes (orange) | Protected by Cloudflare, terminated at local server |

## Common Issues

- **"Cannot add domain X since it's already assigned to another project"** — means the domain is attached to a different Vercel project. Either use the correct project ID or remove it from the old project first via the Vercel dashboard.
- **SSL takes 10-60s** after domain verification. The Vercel async SSL service generates Let's Encrypt certs; the domain returns insecure errors during this window.
- **Two tunnel IDs in credentials** — if you see old/conflicting `.json` files in `~/.cloudflared/`, the config may reference the wrong one. Check `cat ~/.cloudflared/<tunnel-id>.json` and match the tunnel ID in `config.yml`.
- **Cloudflared prints help instead of running** — this happens when arguments are in wrong order. Use `cloudflared tunnel --config <path> run` (NOT `cloudflared tunnel run --config <path>`).
