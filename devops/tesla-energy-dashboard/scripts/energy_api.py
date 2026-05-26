#!/usr/bin/env python3
"""Energy API server — serves /api/energy endpoint on a single port.
   Can be used standalone or as a backend behind a proxy server.
   Usage: python3 energy_api.py [port]
   Default port: 8081
   Env: PORT (alternative way to set port)
"""
import os, json, time, ssl, urllib.request, urllib.parse, urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone

# ── Credentials (embedded for persistence) ────────────────────────────
# These are stored in the file so the API server works across restarts.
# Tokens auto-refresh using REFRESH_TOKEN when they expire.
ACCESS_TOKEN = "eyJhbG...BNlQ"       # Replace with your actual token
REFRESH_TOKEN = "eyJhbG...hmGg"      # Replace with your actual refresh token
ENERGY_SITE_ID = "1689543131745218"
OWNER_API = "https://owner-api.teslamotors.com"

ssl_ctx = ssl.create_default_context()
token = ACCESS_TOKEN
token_expires = 0
last_cache_time = 0
cached_data = None

def refresh_access_token():
    global token, token_expires
    data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "client_id": "ownerapi",
        "refresh_token": REFRESH_TOKEN,
        "scope": "openid email offline_access",
    }).encode()
    req = urllib.request.Request(
        "https://auth.tesla.com/oauth2/v3/token",
        data=data, method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    try:
        resp = urllib.request.urlopen(req, context=ssl_ctx, timeout=15)
        body = json.loads(resp.read())
        token = body["access_token"]
        token_expires = time.time() + body.get("expires_in", 28800)
        return True
    except Exception as e:
        print(f"Token refresh failed: {e}")
        return False

def api_get(path):
    global token
    req = urllib.request.Request(f"{OWNER_API}{path}",
        headers={"Authorization": f"Bearer {token}"})
    try:
        resp = urllib.request.urlopen(req, context=ssl_ctx, timeout=15)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 401:
            if refresh_access_token():
                req = urllib.request.Request(f"{OWNER_API}{path}",
                    headers={"Authorization": f"Bearer {token}"})
                resp = urllib.request.urlopen(req, context=ssl_ctx, timeout=15)
                return json.loads(resp.read())
        raise

def fetch_data():
    global last_cache_time, cached_data
    now = time.time()
    if now - last_cache_time < 5:
        return cached_data
    try:
        live = api_get(f"/api/1/energy_sites/{ENERGY_SITE_ID}/live_status")
        resp = live.get("response", {})
        cached_data = {
            "solar_kw": resp.get("solar_power", 0) / 1000,
            "battery_kw": resp.get("battery_power", 0) / 1000,
            "grid_kw": resp.get("grid_power", 0) / 1000,
            "home_kw": resp.get("load_power", 0) / 1000,
            "battery_percent": round(resp.get("percentage_charged", 0), 1),
            "grid_status": resp.get("grid_status", "Unknown"),
            "island_status": resp.get("island_status", "on_grid"),
            "storm_mode": resp.get("storm_mode_active", False),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "tesla_cloud"
        }
        last_cache_time = now
        return cached_data
    except Exception as e:
        return {"error": str(e), "source": "tesla_cloud"}

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(json.dumps(fetch_data()).encode())
    def log_message(self, *a): pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8081))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
