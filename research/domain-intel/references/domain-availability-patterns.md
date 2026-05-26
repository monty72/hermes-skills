# Domain Availability Checking Patterns

## Context

Collected from a session where a user wanted to register a .dev domain for a dev workspace. The `.dev` TLD is aggressively squatted — most short, brandable names are taken. The session checked ~200+ domains and found almost all taken.

## Techniques in order of reliability

| Method | Reliability | Speed | Notes |
|--------|-------------|-------|-------|
| Registrar checkout (browser) | **Definitive** | Slow | Bot-protected, user must do it |
| RDAP registry query | Authoritative | Medium | .dev blocks; others vary |
| Google DNS over HTTPS | Good heuristic | Fast | NXDOMAIN = no NS records |
| nslookup / dig NXDOMAIN | Good heuristic | Fastest | Same as Google DNS but local |
| WHOIS | Authoritative | Medium | `whois` binary not always installed |

## Practical approach for batch checking

1. Use nslookup or Google DNS API (`dns.google/resolve`) for fast batch screening
2. Filter candidates further with RDAP where available
3. Verify final picks at a registrar

## Batch checking 200+ domains at once

When screening a large set of candidates, use a loop with nslookup:

```bash
for domain in candidate1.dev candidate2.dev candidate3.dev; do
  result=$(nslookup "$domain" 2>&1 | grep 'NXDOMAIN')
  if [ -n "$result" ]; then
    echo "🟢 NO-DNS: $domain"
  fi
done
```

**Note:** This only shows domains with NO DNS at all. If a domain is registered but parked (has NS records but no A/AAAA), it shows as taken. False negatives are possible.

## When whois is not installed

On minimal Linux installations (containers, slim Docker images), `whois` may not be available. Alternative approaches:

```bash
# Method A: Try installing it
apt-get update -qq && apt-get install -y -qq whois

# Method B: Skip whois entirely — use nslookup NXDOMAIN check
# Method C: Use Google DNS over HTTPS
curl -sf "https://dns.google/resolve?name=$domain&type=NS" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('AVAILABLE' if d.get('Status') == 3 else 'TAKEN/UNKNOWN')
"
```

## Sample bulk check command

```bash
for domain in candidate1.dev candidate2.dev candidate3.dev; do
  status=$(curl -sf "https://dns.google/resolve?name=$domain&type=NS" | \
    python3 -c "import sys,json; print(json.load(sys.stdin).get('Status'))")
  if [ "$status" = "3" ]; then echo "🟢 $domain"; fi
done
```

## Common TLD patterns

- `.dev` — $10.18/yr, Google-operated, heavily squatted
- `.app` — $12/yr, Google-operated, same squatting level
- `.co.uk` — £3-5/yr, Nominet, more affordable and less squatted
- `.tech` — $6-8/yr, usually has availability
- `.io` — $30-40/yr, premium pricing, tech startups snap them up
