#!/usr/bin/env python3
"""
BRRR Deal Model — Deterministic Calculator
Run: python3 buy-to-let-brrr.py

Ideal for: Rightmove/Zoopla property URLs the user pastes.
Pass inputs by editing the config block below or piping from another tool.
"""

import math

# ── CONFIG ─────────────────────────────────────────────
PURCHASE = 70_000      # What you'll pay (offer, not asking)
REFURB = 10_000        # Renovation budget
ARV = 120_000          # After-refurb value
RENT_MO = 700          # Expected monthly rent
STRUCTURE = "SPV"      # "SPV" or "PERSONAL"

# Advanced overrides (leave as None for defaults)
BRIDGE_RATE = None     # e.g. 0.006 for 0.6%/mo
BRIDGE_MONTHS = None   # e.g. 6
BTL_LTV = None         # e.g. 0.75
BTL_RATE = None        # SPV default 6.25%, personal 5.5%
BTL_TERM = None        # e.g. 30 (years)
CONTINGENCY = None     # e.g. 0.10
LEGAL = None           # e.g. 1500
SURVEY = None          # e.g. 500
# ───────────────────────────────────────────────────────

# Defaults
br_rate = BRIDGE_RATE or 0.006
br_mos = BRIDGE_MONTHS or 6
btl_ltv = BTL_LTV or 0.75
btl_rate = BTL_RATE or (0.0625 if STRUCTURE.upper() == "SPV" else 0.055)
btl_term = BTL_TERM or 30
cont = CONTINGENCY or 0.10
legal = LEGAL or 1500
survey = SURVEY or 500

def fmt(n):
    return f"£{round(n):,}"

def pct(n):
    return f"{n:.1f}%"

print(f"""
━━━ BRRR DEAL MODEL ━━━━━━━━━━━━━━━━━━━━━━━━
                {fmt(PURCHASE)} → {fmt(ARV)}

📥 ACQUISITION
  Purchase (offer):    {fmt(PURCHASE)}
  SDLT (3% surcharge): {fmt(PURCHASE * 0.03)}
  Legal + survey:      {fmt(legal + survey)}
  ────────────────────────────────────────
""")

# Bridging
bridge_loan = PURCHASE * 0.75
bridge_int = round(bridge_loan * br_rate * br_mos)
deposit = PURCHASE - bridge_loan

acq = round(deposit + PURCHASE * 0.03 + legal + survey + bridge_int)
print(f"  Bridging loan (75%): {fmt(bridge_loan)}")
print(f"  Your deposit (25%):  {fmt(deposit)}")
print(f"  Bridge interest:     {fmt(bridge_int)} ({pct(br_rate*100)}/mo × {br_mos}mo)")
print(f"")
print(f"  Cash you put in:     {fmt(acq)}")

# Refurb
refurb_total = round(REFURB * (1 + cont))
print(f"""
🔧 REFURBISHMENT
  Budget:              {fmt(REFURB)}
  Contingency ({pct(cont*100)}):        {fmt(round(REFURB * cont))}
  ────────────────────────────────────────
  Refurb cash:         {fmt(refurb_total)}

💰 TOTAL CASH IN:       {fmt(acq + refurb_total)}
""")

# Refinance
btl_mortgage = round(ARV * btl_ltv)
repay_bridge = round(bridge_loan + bridge_int)
surplus = btl_mortgage - repay_bridge
cash_in = (acq + refurb_total) - surplus

print(f"🏠 REFINANCE ({pct(btl_ltv*100)} LTV on {fmt(ARV)} ARV)")
print(f"  BTL mortgage:       {fmt(btl_mortgage)}")
print(f"  Repays bridge:     -{fmt(repay_bridge)}")
print(f"  ────────────────────────────────────────")
print(f"  Surplus to you:     {fmt(surplus)}")
print(f"")
if cash_in <= 0:
    print(f"  ✅ ALL CAPITAL RECYCLED (surplus of {fmt(abs(cash_in))})")
else:
    print(f"  ⚠️  Cash left in deal: {fmt(cash_in)}")

# Rental
annual_rent = RENT_MO * 12
gross_yield_arv = (annual_rent / ARV) * 100
gross_yield_cost = (annual_rent / (PURCHASE + refurb_total + PURCHASE * 0.03 + legal + survey)) * 100

# Mortgage payment (monthly)
r = btl_rate / 12
n = btl_term * 12
mort_mo = btl_mortgage * (r * (1 + r)**n) / ((1 + r)**n - 1)

ins_mo = 15
mgmt_mo = RENT_MO * 0.10
rep_mo = RENT_MO * 0.05
net_mo = round(RENT_MO - mort_mo - ins_mo - mgmt_mo - rep_mo)
net_yr = net_mo * 12

co_cash = cash_in if cash_in > 0 else 1
cocr = (net_yr / co_cash) * 100
retained_eq = round(ARV - btl_mortgage - cash_in)

print(f"""
📈 RENTAL
  Monthly rent:         {fmt(RENT_MO)}
  Annual rent:          {fmt(annual_rent)}
  Gross yield (on ARV): {pct(gross_yield_arv)}
  Gross yield (on cost):{pct(gross_yield_cost)}

  Mortgage ({btl_term}yr @ {pct(btl_rate*100)}): -{fmt(mort_mo)}/mo
  Insurance:            -{fmt(ins_mo)}/mo
  Management (10%):     -{fmt(mgmt_mo)}/mo
  Repairs reserve (5%): -{fmt(rep_mo)}/mo
  ────────────────────────────────────────
  Net monthly:          {'+'+fmt(net_mo) if net_mo >=0 else fmt(net_mo)}/mo
  Net annual:           {'+'+fmt(net_yr) if net_yr >=0 else fmt(net_yr)}/yr

📊 ROI
  Cash-on-cash ROI:     {pct(cocr)}{' (∞ — surplus returned)' if cash_in <= 0 else ''}
  Retained equity:      {fmt(retained_eq)}
  Total equity:         {fmt(ARV - btl_mortgage)}

📋 STRUCTURE: {STRUCTURE}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
