# Combined Static + API Server

When deploying the Tesla Energy Dashboard with live data, the front-end HTML and the API backend must be served from the **same port** so they work behind a single tunnel (localhost.run, Surge, etc.). The dashboard JS fetches `/api/energy` (relative path), not an absolute `localhost` URL.

## Two Patterns

### Pattern A: Proxy (Recommended — backend already running)

The front-end server proxies `/api/*` requests to a separate backend API server that holds credentials and handles Tesla token refresh:

| Port | Role | What runs |
|------|------|-----------|
| 8000 | Static files + proxy | SimpleHTTPRequestHandler that serves HTML and forwards `/api/*` to port 8081 |
| 8081 | Backend API only | `energy_api.py` with embedded Tesla token, auto-refresh, and CORS headers |

```
Browser ──► tunnel (port 80) ──► server:8000 ──► /api/* ──► server:8081
                                            └── / ──► index.html
```

**api.py proxy (on port 8000):**

```python
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.request import Request, urlopen
from urllib.error import URLError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND = "http://localhost:8081"

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_GET(self):
        if self.path.startswith("/api/"):
            target = f"{BACKEND}{self.path}"
            try:
                req = Request(target, headers={"User-Agent": "HermesEnergy/1.0"})
                resp = urlopen(req, timeout=10)
                body = resp.read()
                self.send_response(resp.status)
                self.send_header("Content-Type", resp.headers.get("Content-Type", "application/json"))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)
                return
            except URLError as e:
                self.send_response(502)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Backend unreachable: {e.reason}"}).encode())
                return
        super().do_GET()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
```

### Pattern B: Monolithic (all-in-one)

The Python API server handles BOTH the `/api/energy` endpoint AND serves static files from the parent directory directly.

```python
import os, json, mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path
        if path == "/api/energy":
            # API endpoint
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            data = fetch_data()  # your data function
            self.wfile.write(json.dumps(data).encode())
        else:
            # Static files
            if path == "/" or path == "":
                path = "/index.html"
            filepath = os.path.join(os.path.dirname(__file__), "..", path.lstrip("/"))
            if os.path.isfile(filepath):
                ext = os.path.splitext(filepath)[1]
                ctype = mimetypes.types_map.get(ext, "application/octet-stream")
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                with open(filepath, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"404 Not Found")
```

## Directory Layout

For the **proxy pattern** (recommended):

```
~/dev-site/
└── src/
    ├── api.py          # Proxy server (static files + /api/* → :8081)
    ├── index.html      # Product hub / entry page
    ├── mc.html         # Mission Control dashboard
    └── energy.html     # Tesla Energy dashboard

~/energy-dashboard/
└── src/
    └── energy_api.py   # Backend API (Tesla token, port 8081)
```

The proxy server's `directory=BASE_DIR` serves files from its own directory — HTML and API server coexist.

## Deployment

```bash
# Start the backend API server (has credentials)
python3 ~/energy-dashboard/src/energy_api.py &

# Start the combined proxy + static server
cd ~/dev-site/src && python3 api.py 8000 &

# Tunnel to the internet
ssh -o StrictHostKeyChecking=no -R 80:localhost:8000 nokey@localhost.run

# Dashboard available at:
# https://xxxx.lhr.life/          (product hub)
# https://xxxx.lhr.life/energy.html (energy dashboard)
# https://xxxx.lhr.life/api/energy  (API data)
```

## API Response Format

```json
{
  "solar_kw": 7.966,
  "battery_kw": 0.0,
  "grid_kw": -5.304,
  "home_kw": 2.662,
  "battery_percent": 89.7,
  "grid_status": "Active",
  "island_status": "on_grid",
  "storm_mode": false,
  "wall_connectors": [],
  "battery_count": 2,
  "battery_capacity_kwh": 0.0,
  "timestamp": "2026-05-25T12:50:39+00:00",
  "source": "tesla_cloud"
}
```

## Critical Gotchas

- **Dashboard JS must use relative paths.** `const API = '/api/energy'` (not `http://localhost:8081/api/energy`). Absolute localhost URLs break from tunnels — the browser running remotely can't reach `localhost:8081` on the server.
- **Kill duplicate tunnels before starting new ones.** Multiple SSH tunnels to localhost.run for the same port create race conditions. `kill $(pgrep -f 'ssh.*localhost.run')` before starting fresh.
- **localhost.run is slow to connect** — it can take 15-30s to print the URL. Use a timeout of 45-60s on the process, or use `-v` flag and watch for "remote forward success" in stderr.
- **Kill old HTTP servers before starting new ones.** A stale `python3 -m http.server` on the same port prevents the new combined server from binding. `fuser -k 8000/tcp` first.
- **Backend API on 8081 must start first** — if the proxy starts before the backend, it returns 502 errors until the backend is up.
- **Reserve a port for each role** — 8000 = public (static + proxy), 8081 = internal (backend API only). Never run them on the same port.

### Tunnel URL Distribution

When delivering the dashboard URL to the user:
- The tunnel prints the URL once, then hangs forever waiting. Parse it from `process(action='log')` on the background tunnel process.
- The URL line looks like: `abc123.lhr.life tunneled with tls termination, https://abc123.lhr.life`
- After reading the URL, **test it** with `curl -s https://abc123.lhr.life/api/energy` before sharing — the tunnel may take another few seconds to be fully live.
- If you close a tunnel process and start a new one, the URL **always changes** — a new random hash is generated each session.
