---
name: brrr-calculator
description: Full BRRR (Buy, Refurb, Refinance, Rent) deal calculator for UK property investment via SPV limited company. Run this whenever the user shares a Rightmove/Zoopla property URL or asks you to model a BRRR deal. Handles SDLT (3% surcharge), refurb budget, refinance at 75% LTV, gross/net yield, cash-on-cash ROI, and retained equity.
---

# BRRR Calculator

Run this whenever the user shares a UK property investment opportunity. Accept inputs via conversation, then output a complete deal model.

## Required Inputs

Ask for any the user hasn't provided:

- **Purchase price** (what you'd pay, not the asking price)
- **Refurb budget** (estimate)
- **After-refurb value (ARV)** — the estimated market value post-renovation
- **Monthly rent** (estimated)
- **Ownership structure** — 'personal' or 'spv' (limited company)

Infer defaults where reasonable:
- **Deposit**: assume **75% LTV** on the BTL mortgage (post-refinance)
- **BTL mortgage rate**: **5.5%** personal, **6.25%** SPV (allow user to override)
- **Bridging loan**: assume **0.6%/mo** for 6 months, interest rolled up
- **SDLT**: assume 3% surcharge (second home / SPV) — use the standard SDLT rates

## SDLT Calculation (as of 2026)

For second homes / SPV purchases (3% surcharge on all bands):

| Property band | Standard rate | +3% surcharge |
|--------------|--------------|---------------|
| Up to £250,000 | 0% | **3%** |
| £250,001–£925,000 | 5% | **8%** |
| £925,001–£1.5M | 10% | **13%** |
| Above £1.5M | 12% | **15%** |

Scotland: use LBTT rates instead (different bands, no 3% surcharge for companies in the same way).

## Output Format

Present the results in this structure:

```
━━━ BRRR DEAL MODEL ━━━━━━━━━━━━━━━━━━━━━━━━

📥 ACQUISITION
  Purchase price:      £X
  SDLT (3% surcharge): £X
  Legal fees:          £1,500 (estimate)
  Survey:              £500 (estimate)
  Bridging interest:   £X (0.6%/mo × 6mo on purchase)
  ───────────────────────────
  Acquisition total:   £X

🔧 REFURBISHMENT
  Refurb budget:      £X
  Contingency (10%):  £X
  ───────────────────────────
  Refurb total:       £X

💰 ALL-IN COST:        £X

🏠 REFINANCE (75% LTV on ARV)
  ARV:                 £X
  BTL mortgage (75%): £X
  ───────────────────────────
  Cash left in:       £X (negative = surplus pulled out)

📈 RENTAL & YIELD
  Monthly rent:       £X
  Annual rent:        £X
  Gross yield:        X.X% (on ARV)
  Gross yield:        X.X% (on all-in cost)

  Mortgage payment:   -£X/mo (75% @ X.X%)
  Insurance:          -£15/mo
  Mgmt fee (10%):     -£X/mo
  Repairs (5%):       -£X/mo
  ───────────────────────────
  Net monthly:         £X/mo
  Net annual:          £X/yr

📊 ROI
  Cash-on-cash ROI:   X.X% (net annual ÷ cash left in)
  Retained equity:    £X (ARV - mortgage - cash left in)

📋 OWNERSHIP: SPV / Personal
```

## Notes & Pitfalls

- **Headline yield on ARV** is the standard metric lenders use — always calculate it
- **Cash-on-cash ROI** is what matters for the user: return on actual cash put in (not total property value)
- A BRRR succeeds when **cash left in is ~zero or negative** (all capital recycled)
- Target: net yield > 6%, cash-on-cash ROI > 15%
- For SPV purchases: mortgage rates are ~0.75% higher than personal — factor this in
- Bridging interest is typically rolled up (added to loan balance, not paid monthly) — include in acquisition costs
- Refurb contingency of 10-15% is non-negotiable — always apply it
- Do NOT include the user's personal income tax or dividend extraction tax in the deal model — those are extraction decisions, not deal metrics
- If the user hasn't specified purchase price, ask them what they think they could get it for (usually less than asking for stale listings)

## Deterministic Script

For exact computation without manual arithmetic, run the bundled Python script:

```
python3 scripts/buy-to-let-brrr.py
```

Edit the config block at the top of the script to change inputs (purchase, refurb, ARV, rent, structure). Output uses the format above.

## SPV Company Setup

For the pre-requisite setup (SPV formation, accountant, bank, mortgage broker), see `references/spv-setup.md` in this skill.
