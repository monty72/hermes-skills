---
name: domain-intel
description: "Passive domain reconnaissance using Python stdlib. Subdomain discovery, SSL inspection, WHOIS, DNS records."
version: 1.0.0
---

# Domain Intel

## Overview

Passive domain reconnaissance using Python stdlib. No API keys required.

## WHOIS Lookup

```python
import socket, ssl, json

def whois(domain):
    import subprocess
    result = subprocess.run(["whois", domain], capture_output=True, text=True, timeout=10)
    lines = result.stdout.split('\n')
    info = {}
    for line in lines:
        if ':' in line:
            key, val = line.split(':', 1)
            info[key.strip()] = val.strip()
    return info

# info = whois("example.com")
```

## DNS Records

```python
import dns.resolver  # pip install dnspython

def get_dns_records(domain):
    records = {}
    for qtype in ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME', 'SOA']:
        try:
            answers = dns.resolver.resolve(domain, qtype)
            records[qtype] = [str(r) for r in answers]
        except:
            records[qtype] = []
    return records
```

## SSL Certificate

```python
import socket, ssl, datetime

def get_ssl_info(hostname, port=443):
    ctx = ssl.create_default_context()
    with ctx.wrap_socket(socket.socket(), server_hostname=hostname) as s:
        s.settimeout(5)
        s.connect((hostname, port))
        cert = s.getpeercert()
    
    return {
        "subject": dict(x[0] for x in cert["subject"]),
        "issuer": dict(x[0] for x in cert["issuer"]),
        "expires": cert.get("notAfter"),
        "san": [x[1] for x in cert.get("subjectAltName", [])],
    }
```

## Simple Subdomain Discovery

```python
import subprocess

# Requires subfinder or similar
def find_subdomains(domain):
    result = subprocess.run(
        ["subfinder", "-d", domain, "-silent"],
        capture_output=True, text=True, timeout=60
    )
    return result.stdout.strip().split('\n')
```

## Domain Availability Checking

Useful when researching domains to register. These methods check whether a domain is free without visiting a registrar's website (which often has bot protection).

### Method A: DNS NXDOMAIN Check (fastest)

Available everywhere — no dependencies, works with any TLD:

```bash
# Check if a domain has NO DNS records (likely available)
domain="example.com"
nslookup "$domain" 2>&1 | grep -q 'NXDOMAIN'
if [ $? -eq 0 ]; then
    echo "🟢 NO DNS records (may be available)"
else
    echo "🔴 Has DNS records (likely taken)"
fi
```

**Caveat:** NXDOMAIN means the domain has no DNS records, but it could still be registered (parked domains, domains between registrations). Not definitive — always verify at a registrar.

### Method B: Batch DNS Check

```bash
for domain in example1.com example2.io example3.dev; do
    result=$(nslookup "$domain" 2>&1 | grep 'NXDOMAIN')
    if [ -n "$result" ]; then
        echo "🟢 NO-DNS: $domain"
    else
        echo "🔴 HAS-DNS: $domain"
    fi
done
```

### Method C: WHOIS Check (when `whois` binary is available)

```bash
# Install on Debian
sudo apt-get install -y whois

# Check
whois example.com 2>&1 | grep -iE '(No match for|NOT FOUND|No Data Found|DOMAIN NOT FOUND)'
# If any of those patterns match, the domain is unregistered
```

### Method D: Google DNS over HTTPS (bypasses local DNS resolver)

```bash
domain="example.dev"
curl -sf "https://dns.google/resolve?name=$domain&type=NS" | python3 -c "
import sys, json
d = json.load(sys.stdin)
status = d.get('Status')
# Status 0 = NOERROR (has records), 3 = NXDOMAIN (doesn't exist)
if status == 3:
    print('🟢 AVAILABLE (NXDOMAIN)')
elif status == 0:
    print('🔴 TAKEN (has NS records)')
else:
    print(f'Status={status}')
"
```

### Method E: Registry RDAP (authoritative for gTLDs like .dev, .app)

```bash
# .dev TLD is operated by Google Registry
curl -s "https://rdap.nic.dev/domain/example.dev" -o /dev/null -w "%{http_code}"
# 404 = not registered, 200 = registered, 000 = unreachable

# Generic RDAP for most gTLDs
curl -s "https://rdap.verisign.com/com/v1/domain/example.com" -o /dev/null -w "%{http_code}"
```

**Note:** RDAP endpoints may block non-browser requests. DNS NXDOMAIN is a practical fallback but not authoritative — only a registrar's checkout confirms availability.

### Method F: Bulk checking with Python stdlib

```python
import socket
import subprocess
import json

def check_domain_available(domain: str) -> str:
    \"\"\"Returns 'available', 'taken', or 'unknown'\"\"\"
    try:
        socket.getaddrinfo(domain, 80, socket.AF_INET)
        return "taken"
    except socket.gaierror:
        return "available"
    except Exception:
        return "unknown"
```

## Certificate Transparency (subdomains via crt.sh)

```python
import requests

def crtsh_subdomains(domain):
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    resp = requests.get(url, timeout=15)
    if resp.ok:
        subdomains = set()
        for entry in resp.json():
            name = entry.get('name_value', '')
            for n in name.split('\n'):
                if domain in n:
                    subdomains.add(n.strip())
        return sorted(subdomains)
    return []
```
