---
name: tesla-vehicle-charging
description: "Monitor Tesla/EV charging via Powerwall Gateway diagnostics data. Track vehicle charge state, battery level, power draw, and charging history. Integrates with the Powerwall local API."
version: 1.0.0
---

# Tesla/EV Vehicle Charging Monitor

## Overview

Monitor your EV charging at home via the Powerwall Gateway diagnostics endpoint. Track battery level, charge state, and power draw alongside your home energy data.

## Your Vehicle

From diagnostics:
- **Audi ETron** (VIN: WAUZZZGF5SA048308)
- **94.9 kWh** battery capacity
- Connected via Wall Connector / charging cable

## Get Vehicle Charge State

```python
import requests, os, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PW_IP = os.environ.get("POWERWALL_IP", "192.168.1.108")
PW_PASS = os.environ.get("POWERWALL_PASSWORD", "")
BASE = f"https://{PW_IP}"

session = requests.Session()
session.verify = False

def login():
    resp = session.post(f"{BASE}/api/login/Basic",
        json={"username": "customer", "password": PW_PASS, "email": "", "force_sm_off": False})
    return resp.status_code == 200

def get_vehicle_status():
    """Get EV charging status from the Powerwall diagnostics."""
    # The diagnostics data comes from the /api/devices/vitals or /api/system_status endpoint
    # Vehicle info is embedded in the Powerwall system data
    resp = session.get(f"{BASE}/api/system_status")
    resp.raise_for_status()
    data = resp.json()

    # Parse vehicle data from the response
    vehicles = data.get("vehicles", [])
    if not vehicles:
        return {"connected": False}
    
    v = vehicles[0]
    cs = v.get("charge_state", {})
    return {
        "connected": True,
        "vin": v.get("info", {}).get("vin", ""),
        "battery_level": cs.get("batteryLevel"),
        "battery_capacity_kwh": cs.get("batteryCapacity"),
        "power_delivery_state": cs.get("powerDeliveryState"),
        "is_charging": "CHARGING" in str(cs.get("powerDeliveryState", "")),
        "charge_rate_miles_per_hour": cs.get("chargeRate"),
        "charge_limit": cs.get("chargeLimit"),
        "time_to_full": cs.get("minutesToFull"),
    }

# Usage
if __name__ == "__main__":
    if not PW_PASS:
        print("Set POWERWALL_PASSWORD")
        exit(1)
    login()
    v = get_vehicle_status()
    if v.get("connected"):
        print(f"🚗 Vehicle: {v.get('battery_level', '?')}%")
        print(f"🔋 Battery: {v.get('battery_capacity_kwh', '?')} kWh")
        print(f"⚡ State: {v.get('power_delivery_state', '?')}")
    else:
        print("No vehicle detected")
```

## Combined Energy + Vehicle Report

```python
def full_report():
    """Get home energy + vehicle charging in one call."""
    login()
    import json
    
    # Get power flow
    m = session.get(f"{BASE}/api/meters/aggregates").json()
    soe = session.get(f"{BASE}/api/system_status/soe").json()
    v = get_vehicle_status()
    
    report = f"""⚡ HOME ENERGY REPORT
🔋 Powerwall: {soe.get('percentage', 0):.1f}%
☀️  Solar:     {m.get('solar', {}).get('instant_power', 0)/1000:.2f} kW
🏠  Home:      {m.get('load', {}).get('instant_power', 0)/1000:.2f} kW
🔌  Grid:      {m.get('site', {}).get('instant_power', 0)/1000:.2f} kW"""
    
    if v.get("connected"):
        report += f"""
🚗 Vehicle: {v.get('battery_level', '?')}% ({v.get('power_delivery_state', '?')})"""
    
    return report
```

## Cron Job: Hourly Energy + EV Report

```python
# ~/hermes_scripts/energy_report.py
# Run via: POWERWALL_PASSWORD="x" python3 this_script.py

if __name__ == "__main__":
    print(full_report())
```

Set up with:
```
hermes cron create --schedule "0 * * * *" --prompt "Run ~/hermes_scripts/energy_report.py"
```
