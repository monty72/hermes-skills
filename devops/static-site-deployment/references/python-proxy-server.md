# Python Proxy Server: SPA + API from One Port

When deploying a static SPA that calls a separate API backend, use a Python proxy server to serve both from a single port. This is essential when exposing through a tunnel (localhost.run, Cloudflare Tunnel) since a tunnel forwards one port.

## Implementation

`serve.py` at project root — subclasses `SimpleHTTPRequestHandler`:

```python
#!/usr/bin/env python3
"""Serves static files from dist/ and proxies /api/* to backend."""

import http.server, urllib.request, os, json

PORT = int(os.environ.get('PORT', 5173))
API_TARGET = os.environ.get('API_TARGET', 'http://localhost:5011')
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'dist')


class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def _proxy(self, method='GET', body=None):
        target_url = API_TARGET + self.path
        try:
            req = urllib.request.Request(target_url, data=body,
                headers={'Content-Type': 'application/json'} if body else {})
            req.method = method
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
                self.send_response(resp.status)
                self.send_header('Content-Type',
                    resp.headers.get('Content-Type', 'application/json'))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.URLError as e:
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e.reason)}).encode())

    def do_GET(self):
        if self.path.startswith('/api/'):
            self._proxy('GET')
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith('/api/'):
            body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
            self._proxy('POST', body or b'{}')
        else:
            self.send_response(404)
            self.end_headers()

    def do_DELETE(self):
        if self.path.startswith('/api/'):
            self._proxy('DELETE')
        else:
            self.send_response(404)
            self.end_headers()

    def do_PUT(self):
        if self.path.startswith('/api/'):
            body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
            self._proxy('PUT', body or b'{}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt, *args):
        # Cleaner logging: "GET /api/health → 200"
        if '/api/' in str(args):
            print(f"→ {args[0]} {args[1]} {args[2]}")


if __name__ == '__main__':
    os.chdir(STATIC_DIR)
    http.server.HTTPServer(('0.0.0.0', PORT), ProxyHandler).serve_forever()
```

## Usage

```bash
npm run build                    # Build SPA → dist/
python3 api.py &                 # Start API (port 5011)
python3 serve.py &               # Serves dist/ + proxies /api
ssh -R 80:localhost:5173 nokey@localhost.run
# → https://<hash>.lhr.life — both SPA and API work
```

## Pitfalls

- **URL encoding**: `urllib.request` handles URL encoding natively, but if the backend expects raw bytes in the body, pass `data=body` without encoding.
- **Timeout**: `timeout=10` prevents hung proxy from holding the tunnel connection. Adjust for slow backends.
- **Large payloads**: `SimpleHTTPRequestHandler` reads the entire body into memory. Not suitable for file uploads >50MB.
- **CORS**: The proxy adds `Access-Control-Allow-Origin: *` on proxied responses. Remove if the API handles its own CORS.
- **Static file path**: `os.chdir(STATIC_DIR)` is called at startup. All static paths are relative to that directory.
