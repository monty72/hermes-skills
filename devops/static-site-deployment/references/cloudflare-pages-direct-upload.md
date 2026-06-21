# Cloudflare Pages Direct Upload Reference

## Overview

Complete Python deployment script for uploading pre-built static sites to Cloudflare Pages via the Direct Upload API. Use this when wrangler CLI is unavailable (e.g. `cfut_` token bug in wrangler, non-interactive CI, Python-only environments).

## Prerequisites

- Cloudflare API token with `Cloudflare Pages > Edit` scope
- Cloudflare Account ID (from dashboard sidebar)
- Project name (created once via API or dashboard)
- Pre-built `dist/` directory

## Endpoints Used

| Step | Method | Endpoint | Auth | Purpose |
|------|--------|----------|------|---------|
| 1 | POST | `/client/v4/accounts/{acct}/pages/projects` | Bearer API token | Create project (one-time) |
| 2 | POST | `/client/v4/accounts/{acct}/pages/projects/{proj}/deployments` | Bearer API token (multipart) | Create deployment with manifest |
| 3 | POST | `/client/v4/pages/assets/upload` | Bearer JWT (from deployment) | Upload missing files |
| 4 | POST | `/client/v4/pages/assets/upsert-hashes` | Bearer JWT (from deployment) | Register uploaded hashes |
| 5 | POST | `/client/v4/accounts/{acct}/pages/projects/{proj}/deployments/{id}/start` | Bearer API token | Start build |

## Complete Working Script

```python
import os, hashlib, json, mimetypes, subprocess, http.client, sys

tok = subprocess.run(
    ['hermes-vault', 'get', 'CLOUDFLARE_PAGES_TOKEN'],
    capture_output=True, text=True
).stdout.strip()

ACCT = "a6f9315a00dae2ea1f45a82f75e43d44"    # Your account ID
PROJ = "my-project"                            # Your project name
DIST = os.path.expanduser("~/dev-site/dist")   # Your dist directory

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk: break
            h.update(chunk)
    return h.hexdigest()

def mime_type(fname):
    ct, _ = mimetypes.guess_type(fname)
    if ct: return ct
    ext = os.path.splitext(fname)[1].lower()
    m = {'.js': 'application/javascript', '.css': 'text/css', '.svg': 'image/svg+xml',
         '.html': 'text/html', '.ico': 'image/x-icon', '.json': 'application/json',
         '.zip': 'application/zip', '.pdf': 'application/pdf',
         '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}
    return m.get(ext, 'application/octet-stream')

def request(method, path, body=None, headers=None):
    conn = http.client.HTTPSConnection('api.cloudflare.com')
    hdrs = {'Authorization': 'Bearer ' + tok}
    if headers: hdrs.update(headers)
    conn.request(method, path, body=body, headers=hdrs)
    resp = conn.getresponse()
    data = json.loads(resp.read().decode())
    conn.close()
    return resp.status, data

# Step 1: Create project (one-time)
print("Creating project...")
request('POST', f'/client/v4/accounts/{ACCT}/pages/projects',
    json.dumps({'name': PROJ, 'production_branch': 'main'}).encode(),
    {'Content-Type': 'application/json'})

# Step 2: Build file manifest
manifest = {}
for root, dirs, files in os.walk(DIST):
    for fname in files:
        fpath = os.path.join(root, fname)
        rel = os.path.relpath(fpath, DIST)
        manifest[rel] = {"content_type": mime_type(fname), "sha256": sha256_file(fpath)}

# Step 3: Create deployment (multipart, NOT JSON)
manifest_json = json.dumps(manifest)
boundary = b'----FormBoundary7MA4YWxkTrZu0gW'
parts = []
parts.append(b'--' + boundary + b'\r\n')
parts.append(b'Content-Disposition: form-data; name="manifest"\r\n')
parts.append(b'Content-Type: application/json\r\n\r\n')
parts.append(manifest_json.encode('utf-8'))
parts.append(b'\r\n')
parts.append(b'--' + boundary + b'\r\n')
parts.append(b'Content-Disposition: form-data; name="branch"\r\n\r\n')
parts.append(b'main')
parts.append(b'\r\n')
parts.append(b'--' + boundary + b'--\r\n')
body_bytes = b''.join(parts)

conn = http.client.HTTPSConnection('api.cloudflare.com')
conn.request('POST',
    f'/client/v4/accounts/{ACCT}/pages/projects/{PROJ}/deployments',
    body=body_bytes,
    headers={
        'Authorization': 'Bearer ' + tok,
        'Content-Type': f'multipart/form-data; boundary={boundary.decode()}',
    })
resp = conn.getresponse()
data = json.loads(resp.read().decode())
conn.close()

if data.get('success'):
    dep = data['result']
    print(f"Deployment: {dep['id']}")
    print(f"URL: https://{dep['id']}.{PROJ}.pages.dev")
    
    # Step 4: Upload missing files (if any)
    jwt = dep.get('jwt', '')
    missing = dep.get('missing_hashes', [])
    if missing and jwt:
        print(f"Uploading {len(missing)} files...")
        for rel_path, info in manifest.items():
            if info['sha256'] not in missing: continue
            with open(os.path.join(DIST, rel_path), 'rb') as f:
                file_data = f.read()
            
            file_boundary = b'----FileBoundary'
            fb_parts = []
            fb_parts.append(b'--' + file_boundary + b'\r\n')
            fb_parts.append(b'Content-Disposition: form-data; name="key"\r\n\r\n')
            fb_parts.append(rel_path.encode())
            fb_parts.append(b'\r\n--' + file_boundary + b'\r\n')
            fb_parts.append(b'Content-Disposition: form-data; name="value"\r\n')
            fb_parts.append(b'Content-Type: ' + info['content_type'].encode() + b'\r\n\r\n')
            fb_parts.append(file_data)
            fb_parts.append(b'\r\n--' + file_boundary + b'\r\n')
            fb_parts.append(b'Content-Disposition: form-data; name="metadata"\r\n\r\n')
            fb_parts.append(json.dumps({"contentType": info['content_type']}).encode())
            fb_parts.append(b'\r\n--' + file_boundary + b'--\r\n')
            fb_body = b''.join(fb_parts)
            
            conn2 = http.client.HTTPSConnection('api.cloudflare.com')
            conn2.request('POST', '/client/v4/pages/assets/upload',
                body=fb_body,
                headers={
                    'Authorization': 'Bearer ' + jwt,
                    'Content-Type': f'multipart/form-data; boundary={file_boundary.decode()}',
                })
            r2 = json.loads(conn2.getresponse().read().decode())
            conn2.close()
            print(f'  {"✓" if r2.get("success") else "✗"} {rel_path}')
else:
    print(f"Error: {data.get('errors')}")

# Step 5: Build starts automatically — check status via GET
```

## Custom Domain Setup

After the Pages project is live on `*.pages.dev`, add a custom domain:

```python
# POST /client/v4/accounts/{acct}/pages/projects/{proj}/domains
# IMPORTANT: use 'name' key, NOT 'domain'
body = json.dumps({'name': 'example.com'}).encode()
req = urllib.request.Request(
    f'https://api.cloudflare.com/client/v4/accounts/{acct}/pages/projects/{proj}/domains',
    data=body, method='POST')
req.add_header('Authorization', 'Bearer ' + pages_token)
req.add_header('Content-Type', 'application/json')
```

**API quirk:** The body uses `{"name": "example.com"}` — using `{"domain": "..."}` returns error `8000015: "The domain you have entered contains an invalid TLD"` even with a valid domain.

### DNS Records for Custom Domain

Once the domain is added to Pages, update DNS:

1. **Remove** existing A records for the apex domain
2. **Add** a CNAME record: `example.com → project-name.pages.dev` with `proxied: true` (Cloudflare handles CNAME flattening at the apex)
3. Cloudflare Pages handles SSL certificate issuance automatically

```python
# Delete old A records
for rec in existing_a_records:
    DELETE /client/v4/zones/{zone_id}/dns_records/{rec_id}

# Add CNAME (works at apex on Cloudflare)
POST /client/v4/zones/{zone_id}/dns_records
{"type": "CNAME", "name": "example.com", "content": "project-name.pages.dev",
 "proxied": true, "ttl": 1}
```

## Pitfalls

1. **CRITICAL: Multipart, not JSON** — The deployment creation endpoint expects `multipart/form-data` with the manifest as a FORM FIELD, not as a JSON request body. Sending `{"manifest": ...}` as JSON fails with `code 8000096: "A manifest field was expected"`.

2. **Domain API uses `name` not `domain`** — The `create domain` endpoint body key is `name`, not `domain`. Using `domain` produces the confusing error `"The domain you have entered contains an invalid TLD"` (code 8000015).

3. **Project source type is locked** — Once created as Direct Uploads project, you cannot change to GitHub source (error code 8000069). Delete and recreate if needed.

4. **Deployment shows success but URL returns 404** — The `deploy` stage may show `status: success` while `queued` stage stays `active` and other stages (initialize, build) never start. This is a stuck Direct Upload deployment. Create a new one rather than waiting.

5. **Node version for Astro 5** — Requires `>=22.12.0`. Pinning to Node 20 in GitHub Actions causes build failures with `"Node.js v20 is not supported by Astro!"`.

6. **GitHub Actions token format** — `cfut_`-prefixed tokens fail in wrangler CLI but work in GitHub Actions via `cloudflare/wrangler-action@v3` and in direct API calls via Python/curl.
