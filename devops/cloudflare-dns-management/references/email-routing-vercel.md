# Email Routing DNS Setup (Custom Domain + Vercel)

Setting up Cloudflare Email Routing for a custom domain that's also served by Vercel requires careful DNS handling because MX records and CNAME records cannot coexist at the zone apex per RFC standards.

## The Conflict

When a domain is served by Vercel:

```
CNAME montygroup.uk → cname.vercel-dns.com   # Vercel hosting
MX    montygroup.uk → mx1.email.cloudflare.net  # Email Routing
```

Per DNS standards, a CNAME at the apex prevents any other record type (MX, TXT, A) from coexisting. Cloudflare will show "DNS misconfigured" when both exist.

## The Fix: Replace Apex CNAME with Proxied A Records

Remove the apex CNAME and add A records pointing to Vercel's static IPs with the orange cloud (proxied) enabled:

```bash
# 1. Find and delete the apex CNAME
CNAME_ID=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?name=example.com&type=CNAME" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; print(json.load(sys.stdin).get('result',[{}])[0].get('id',''))")

curl -s -X DELETE "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$CNAME_ID" \
  -H "Authorization: Bearer $TOKEN"

# 2. Add Vercel A records
for ip in 76.76.21.21 76.76.21.98; do
  curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"type\":\"A\",\"name\":\"example.com\",\"content\":\"$ip\",\"ttl\":120,\"proxied\":true}"
done
```

The `proxied: true` (orange cloud) keeps the Vercel site working via Cloudflare's proxy while allowing MX records at the apex.

## Records Cloudflare Email Routing Auto-Adds

When Email Routing is enabled via the dashboard (clicking "Add records and finish"), Cloudflare automatically adds:

| Type | Name | Content |
|------|------|---------|
| MX | example.com | route1.mx.cloudflare.net (prio 95) |
| MX | example.com | route2.mx.cloudflare.net (prio 46) |
| MX | example.com | route3.mx.cloudflare.net (prio 49) |
| TXT | example.com | v=spf1 include:\_spf.mx.cloudflare.net ~all |
| TXT | cf2024-1.\_domainkey.example.com | v=DKIM1; h=sha256; k=rsa; p=... |

Do NOT add these manually via the DNS API — Cloudflare adds them with the exact format it expects. Manual additions can conflict and cause "DNS misconfigured" errors.

## Dashboard Setup Flow

1. Go to Cloudflare Dashboard -> zone -> Email -> Email Routing
2. Click "Get started" or "Add records and finish"
3. If "DNS misconfigured" appears after, check for apex CNAME conflicts
4. After fixing DNS, refresh the page — Cloudflare re-checks every few minutes
5. Once green, create routing rules: "Add route" -> email address -> forward destination

## API Token Permissions

Managing Email Routing itself requires `Zone > Email Routing > Edit` scope on the API token. The setup above uses DNS API only (MX/SPF records via DNS:Edit). For programmatic Email Routing rule management, create a token with both scopes.

## DKIM Signing

Cloudflare auto-generates a DKIM key when Email Routing is enabled. The `cf2024-1._domainkey` TXT record is created automatically. DKIM ensures forwarded emails pass SPF/DKIM checks at the destination (important for Gmail/Hotmail delivery).
