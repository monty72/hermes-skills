---
name: uk-energy-research
description: "Research UK energy market (suppliers, tariffs, solar/battery, VPPs) AND UK retail pricing/availability (Amazon, John Lewis, Currys, etc.) — Brave Search API research patterns, affiliate/referral monetisation opportunities, and browser automation workarounds."
version: 1.0.0
---

# UK Market Research

## Overview

Researching the UK energy landscape and UK retail pricing/availability: suppliers, tariff structures, solar/battery hardware and installers, grid services (VPPs), affiliate/referral monetisation opportunities, and product price checking at major UK retailers.

## Key Findings — May 2026

### UK Energy Suppliers — Referral & Affiliate Landscape

| Supplier | Has Referral? | How to monetise | Notes |
|----------|--------------|-----------------|-------|
| **Octopus Energy** | ✅ Referral (£50 each) | Use `share.octopus.energy/YOUR-CODE` — works like Gary Does Solar's `garywaite.octopus.energy` | Best opportunity. Promote on every energy page. |
| **E.ON Next** | ❌ No public referral | — | Customer-only via app |
| **British Gas** | ❌ No public program | — | — |
| **OVO** | ❌ Referral closed | — | Had one, discontinued |
| **Scottish Power** | ⚠️ Via TopCashback | Up to £95 via cashback sites | Sign up as publisher on TopCashback/Quidco |
| **EDF** | ❌ No referral | — | — |

### Affiliate Networks for Comparison Sites

| Network | URL | Sign-up | Payouts |
|---------|-----|---------|---------|
| **Awin** | awin.com/gb/publisher/affiliate-partners | Free to join as Publisher | uSwitch, MSE, CompareTheMarket on Awin. £30–£80 per energy switch |
| **CJ Affiliate** | cj.com/publisher | Free | Big UK brands (E.ON, British Gas historically) |
| **Impact** | impact.com | Free as Partner | Newer energy brands |

### Solar Installer Lead-Gen Model

Gary Does Solar runs `getreadyfor.solar` — an installer directory that collects leads via email capture. The flow:
1. User enters email → receives 4-digit OTP
2. Paywalled behind email verification
3. Installers pay per lead or per customer

This is **higher margin than energy supplier referrals** — solar installs are £5k–£18k, lead costs are £50–£200+.

To replicate: build a directory page of MCS-certified installers, collect emails, sell leads back to installers.

### Virtual Power Plants (VPPs) & Grid Services

**Axle Energy** (`axle.energy` / `vpp.axle.energy/landing`)
- **Compatible batteries:** Solis, SolaX, FoxESS, GivEnergy, SolarEdge, Sigenergy
- **NOT compatible:** Tesla Powerwall (proprietary protocol), any battery without Modbus/CAN bus open protocol
- **Installer referral:** £50 per successful customer enrolment
- **Consumer earnings:** ~£1/kWh, £10/month minimum (until March 2026)
- **Gary's referral code:** `R-GARYSOLAR`
- **How to get your own:** Sign up at `vpp.axle.energy/landing` — use the "More brands coming soon" button to request Powerwall support
- **Alternative for Powerwall owners:** Octopus Flux (export up to 15p/kWh), Octopus Saving Sessions (DFS events)

### Octopus Energy Referral

Your referral link: `share.octopus.energy/open-lake-523`

When someone signs up via your link:
- They get £50 credit
- You get £50 credit
- They can switch to any Octopus tariff (Agile, IOG, Cosy, Flux, Tracker) after sign-up

**How Gary Does Solar does it:** His Octopus affiliate link redirects to `octopus.energy/quote/?affiliate=garywaite.octopus.energy`. He has his own Gary Does Solar page at `/octopus` that renders as a link card with `Get £50 Credit!` CTA.

## Research Methods

### For Energy Supplier Data
- Octopus Energy API: `api.octopus.energy/v1/products/{PRODUCT}/electricity-tariffs/{TARIFF}/standard-unit-rates/`
- Ofgem price cap: Search "Ofgem price cap [quarter] [year]" for latest
- Supplier ratings: Which?, MoneySavingExpert, Trustpilot

### For Solar/Installer Research
- MCS certified installer database: `mcscertified.com`
- Solar generation estimates: Energy Saving Trust regional tables
- Hardware specs: Manufacturer websites (Tesla, GivEnergy, FoxESS, Solis, SolaX)

### For Affiliate Programs
- Awin: `awin.com/gb/publisher/affiliate-partners` — check advertiser directory for energy brands
- CJ Affiliate: `cj.com/publisher` — browse by category
- Impact: `impact.com` — request demo, check partner directory

## Pitfalls

- **No UK supplier has a true "affiliate program"** (percentage commission). They only have customer referral links (fixed £25–£50 credit). Real affiliate payouts come via comparison sites (uSwitch/MSE) through Awin/CJ.
- **Cashback sites (TopCashback, Quidco) pay for switching** but you can't link directly — you need to join their publisher program. However, you CAN use your own TopCashback/Quidco *referral link* to earn from people signing up to those sites.
- **Awin's site** aggressively redirects to a "page not found" placeholder for some URLs. The advertiser directory URL is `awin.com/gb/advertiser-directory` but it may not work without being logged in. The sign-up flow works.
- **Solar installer directories** need MCS certification checks. Don't list installers without MCS — it's a legal requirement for them to install solar/battery with 0% VAT and SEG eligibility.
- **Tesla Powerwall compatibility with VPPs:** Tesla uses a proprietary protocol. Only inverters using open standards (Modbus RTU/TCP, SunSpec, CAN bus) can integrate with third-party VPPs like Axle. This is a fundamental hardware limitation, not something Axle can fix by writing an API integration — they'd need Tesla to open up bidirectional control on the Powerwall API.

## UK Retail Price Research

For checking product pricing and availability at UK retailers from within an agent session.

### Known Blocked Retailers

These consistently block browser automation:

| Retailer | Block Pattern | Workaround |
|----------|--------------|------------|
| **John Lewis** | ERR_HTTP2_PROTOCOL_ERROR or 403 | Cannot scrape — give user the search URL |
| **Currys** | Cloudflare "Just a moment..." | Cannot bypass — give user the search URL |
| **AO.com** | Cloudflare challenge | Cannot bypass — give user the search URL |
| **Argos** | "Access Denied" | Cannot bypass — give user the search URL |
| **Google Shopping** | CAPTCHA page | Try Amazon only |

### Amazon UK (Partially Works)

Amazon.co.uk works with the browser tool, but with caveats:

1. **Cookie banner** — must click "Accept" before results render
2. **Extract via JS** — use `browser_console` with JS queries, not `browser_snapshot`:
   ```javascript
   Array.from(document.querySelectorAll('[data-component-type="s-search-result"]'))
     .map(el => {
       const title = el.querySelector('h2 a')?.textContent?.trim() || 'n/a';
       const price = el.querySelector('.a-price')?.textContent?.trim().replace(/\s+/g,' ') || 'n/a';
       const link = el.querySelector('h2 a')?.href || '';
       return `${title} | ${price} | ${link}`;
     })
     .join('\n')
   ```
3. **Sort by price ascending**: `https://www.amazon.co.uk/s?k=PRODUCT&s=price-asc-rank`
4. **Results are noisy** — includes accessories and unrelated items. Filter for exact brand + model.
5. **Use category param**: `&i=kitchen`, `&i=electronics`, etc.

### When to Hand Off to the User

Do NOT keep trying blocked sites. After two failed attempts:
1. Tell the user the site blocks automation
2. Provide the direct search URL they can open manually: `https://www.johnlewis.com/search?q=PRODUCT`
3. Include known RRP info so they can judge if the price is fair

### Pitfalls
- **Cookie banners on every Amazon session** — each new browser_navigate requires accepting cookies
- **Safari on iPhone blocks Amazon product links** for certain categories — tell user to copy-paste the URL
