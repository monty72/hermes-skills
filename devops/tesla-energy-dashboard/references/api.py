#!/usr/bin/env python3
"""Energy data API server — bridges Powerwall local API to JSON."""
import os, json, sys, logging
from http.server import HTTPServer, BaseHTTPRequestHandler

PW_IP = os.environ.get("POWERWALL_IP", "192.168.1.108")
PW_PASS = os.environ.get("POWERWALL_PASSWORD", "")
PW_USER = os.environ.get("POWERWALL_USERNAME", "customer")
BASE = f"https://{PW_IP}"

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

session = requests.Session()
session.verify = False

def login():
    if not PW_PASS:
        return False
    resp = session.post(f"{BASE}/api/login/Basic",
        json={"username": PW_USER, "password": PW_PASS, "email": "", "force_sm_off": False})
    return resp.status_code == 200

logged_in = False

def fetch_data():
    global logged_in
    if not logged_in:
        logged_in = login()
    if not logged_in:
        return {"error": "Not authenticated. Set POWERWALL_PASSWORD."}

    try:
        soe = session.get(f"{BASE}/api/system_status/soe").json()
        meters = session.get(f"{BASE}/api/meters/aggregates").json()
        grid = session.get(f"{BASE}/api/system_status/grid_status").json()
    except Exception as e:
        logged_in = False
        return {"error": str(e)}

    solar = meters.get("solar", {})
    battery = meters.get("battery", {})
    site = meters.get("site", {})
    load = meters.get("load", {})

    return {
        "battery_percent": soe.get("percentage", 0),
        "solar_kw": solar.get("instant_power", 0) / 1000,
        "battery_kw": battery.get("instant_power", 0) / 1000,
        "grid_kw": site.get("instant_power", 0) / 1000,
        "home_kw": load.get("instant_power", 0) / 1000,
        "solar_energy_today_kwh": solar.get("energy_exported", 0) / 1000,
        "grid_import_kwh": site.get("energy_imported", 0) / 1000,
        "grid_export_kwh": site.get("energy_exported", 0) / 1000,
        "grid_status": grid.get("grid_status", "unknown"),
        "off_grid": grid.get("grid_status") == "SystemIslandedActive",
    }

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        data = fetch_data()
        self.wfile.write(json.dumps(data).encode())
    def log_message(self, *a): pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8081))
    print(f"Energy API on :{port} (PW3 at {PW_IP})")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
