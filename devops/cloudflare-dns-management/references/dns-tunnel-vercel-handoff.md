# DNS / Tunnel / Vercel Handoff Pattern

When deploying to Vercel or another external platform while running a Cloudflare Tunnel, you have two options for subdomain routing:

## Option A: All traffic through tunnel

Cloudflare DNS CNAME → tunnel → local server (Flask on :8000)

Best when: no external platform, staying fully self-hosted.

## Option B: Split routing (subdomain per platform)

```
mc.montygroup.uk  → CNAME → cname.vercel-dns.com  (Vercel)
energy.montygroup.uk → CNAME → <tunnel>.cfargotunnel.com  (Tunnel → Flask API)
childminding.montygroup.uk → CNAME → <tunnel>.cfargotunnel.com  (Tunnel → Flask)
```

Best when: migrating gradually, or when some services need Vercel's edge and others need local backend access.

### Vercel DNS Setup

1. In Vercel project settings > Domains > Add `mc.montygroup.uk`
2. Vercel tells you to create a CNAME record pointing to `cname.vercel-dns.com`
3. In Cloudflare DNS, delete the tunnel CNAME for that subdomain and create a new CNAME:

```bash
# Update a single subdomain to point to Vercel instead of tunnel
ZONE_ID="<zone-id>"
TOKEN="<token>"
RECORD_ID=$(curl -s "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?name=mc.montygroup.uk" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result'][0]['id'])")

curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"CNAME","content":"cname.vercel-dns.com","ttl":120,"proxied":true}'
```

4. Vercel auto-provisions an SSL cert for the domain

### Note for Astro sites

Astro builds to static HTML by default. Deploy the `dist/` folder to Vercel. The tunnel can continue running the Flask API backend (Tesla data, etc.) on a different subdomain.
