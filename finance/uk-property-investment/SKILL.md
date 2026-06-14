---
name: uk-property-investment
description: "Research, model, and evaluate UK property investment strategies (BRRR, flip, refurb & rent). Covers macro market data, regional yields, tax rules, Rightmove search for investment properties, and full financial modelling with the 70% rule and refinance calculations."
version: 1.0.0
---

# UK Property Investment Research

## Overview

Research UK property investment opportunities: flipping (buy-refurbish-sell) vs BRRR (Buy-Refurbish-Refinance-Rent). Find live listings, model the numbers, and evaluate deals. For investors who want concrete property-level analysis, not generic market commentary.

## Workflow

### Phase 1: Macro Research

Understand the national picture before narrowing down:

- **National house price trends** — search "UK house price index [year]" (ONS/Land Registry data). Current context: modest price growth (1-4% forecast), rental yields at national avg ~5.8%. Only ~60% of flips profitable.
- **Regional yield data** — use web_search for "average rental yield [city] [year]" or "best rental yields UK [year]". Top cities (as of 2026): Newcastle (9.7%), Leeds (9.6%), Nottingham (9.0%), Southampton (9.0%).
- **Tax regime** — current rates: SDLT second home = 5-17% (3% surcharge on top of standard), CGT = 18% (basic) / 24% (higher), CGT allowance £3k/yr. Business Asset Disposal Relief rising to 18% from Apr 2026.
- **Council tax premium** — from Apr 2025, councils can charge up to 100% premium on second homes. Check local council policy.

### Phase 2: Narrow by Geography

When the user specifies a location (e.g. "local to Rotherham"):

1. **Get local market stats** — search "average house price [town/city] [year]", "rental yield [postcode area]", "property market [town] [year]"
2. **Identify target areas by postcode** — use local knowledge or web_search for area reputation, regeneration projects, transport links
3. **Regeneration tailwinds** — check for Levelling Up Fund allocations, town centre regeneration, new transport infrastructure, university campuses

For Rotherham specifically (from 2026 fieldwork):
- S62 Parkgate/Rawmarsh: best postcode (S62 named top 20 UK family postcodes). Entry £120-140k, yields ~6-7%
- S65 Eastwood: highest yields (7.6%), cheapest entry (£80-130k), but carries some area stigma
- S61 Kimberworth/Maltby: affordable terraced stock, ~6.5% yields
- S66 Wickersley: too expensive for investment (£254k avg, 3.3% yield)

### Phase 3: Find Live Listings on Rightmove

Search approach for investment properties:

1. **Open a Rightmove search** in the browser for the target town/area, filtered by:
   - `maxPrice` = the BRRR entry budget (typically £100-150k for North/Midlands)
   - `minBedrooms` = 2 (minimum for rental demand)
   - `propertyTypes` = `terraced%2Csemi-detached` (sweet spot for refurbs)
   - `dontShow` = `retirement%2CsharedOwnership`
   - `sortType` = 6 (newest first — catch fresh listings)

2. **URL template:**
   ```
   https://www.rightmove.co.uk/property-for-sale/[TOWN].html?sortType=6&maxPrice=[MAX]&minBedrooms=2&dontShow=retirement%2CsharedOwnership
   ```

3. **When the Rightmove result page loads**, use `web_extract` or `browser_snapshot(full=true)` to parse the listing cards. Look for:
   - Properties with **"investment potential"** or **"investor"** in the description — signals motivated seller
   - **No chain** / **vacant possession** — faster completion
   - Listed **>3 months ago** — room to negotiate
   - Properties needing work (lower entry = more equity to manufacture)

4. **Open individual listings** to get full details: price, EPC rating, tenure, council tax band, descriptions. Extract image URLs for the user.

5. **Look for multiple candidates** — present a shortlist with comparison table.

### Phase 4: Financial Modelling

#### BRRR Model

```
Buy:         [negotiated price below asking]
Refurb:      [cosmetic: £10-15k, full: £50-70k, per sqm: £1,200-2,500]
All-in:      Buy + Refurb + SDLT + legal + bridging interest
New value:   [conservative ARV — check comparable sold prices]
Refinance:   75% of New Value = BTL mortgage
Cash pulled: Refinance amount - Buy - Refurb costs
Left in:     All-in - Refinance (target: £0-10k)
Rent:        [check Zoopla/Rightmove rental estimates for comparable]
Yield:       (Annual rent / New value) × 100
ROI on cash: (Annual rent - costs) / Cash left in × 100
```

The BRRR magic is when `Refinance >= Buy + Refurb`, meaning you pull ALL your capital back out.

#### The 70% Rule (for flipping)

```
Max Offer = (After Repair Value × 0.70) – Renovation Costs
```

If you can't buy at or below 70% of ARV minus refurbs, the flip margin is too thin after SDLT, agents fees (1-1.5%), and CGT.

#### Stamp Duty Calculation (Second Home)

```
£0-£250k:   5% (2% standard + 3% surcharge)
£250k-£925k: 10% (7% + 3%)
£925k-£1.5m: 17% (12% + 5%)
```

For sub-£250k in the North, SDLT is typically ~5% of purchase price.

#### Flip Profit Waterfall

```
Gross profit:    ARV - (Buy + Refurb + SDLT + Legal + Agents)
CGT:             (Gain - £3k allowance) × 18% (basic) or 24% (higher)
Net profit:      Gross profit - CGT
ROI on cash:     Net profit / (Deposit + Refurb + SDLT + Fees) × 100
```

#### Rent Affordability Check

- Most BTL lenders stress-test at 125% of mortgage payment at 5.5-6% interest rate
- Minimum rent to cover: (Mortgage × 1.25) per month
- Council Tax Band A = ~£1,200-1,600/yr, Band B = ~£1,400-1,800/yr

## Key Tax Rates (2026/27)

| Item | Rate |
|------|------|
| SDLT second home (sub-£250k) | 5% |
| SDLT second home (£250-925k) | 10% |
| CGT (basic rate taxpayer) | 18% |
| CGT (higher rate taxpayer) | 24% |
| CGT annual allowance | £3,000 |
| Income tax on rent | Marginal rate (20/40/45%), interest relief limited to 20% tax credit |
| Council tax (second home premium) | Up to 100% from Apr 2025 |
| Corporation tax (SPV, profits <£50k) | 19% |
| Dividend tax (basic rate, 2026/27) | 10.75% |
| Dividend tax (higher rate, 2026/27) | 35.75% |

## Limited Company vs Personal Name

### Decision Tree

```
User tax bracket?
├── Basic rate (20%):
│   └─ Personal name — simpler, Section 24 credit matches their rate
├── Higher rate (40% / 45%):
│   ├─ Plans 1-2 properties, needs cash flow → Personal (simpler, but taxed heavily)
│   └─ Plans 3+ properties, can reinvest → Limited Company (SPV) ← DEFAULT for this user
└── Already has properties personally:
    └─ DO NOT transfer — triggers SDLT + CGT. Keep personal or start fresh SPV.
```

### Why Limited Company Wins for Higher-Rate Taxpayers

1. **Full mortgage interest deduction** — treated as a business expense before corporation tax. Personal only gets 20% tax credit (Section 24).
2. **Lower tax rate** — 19% corporation tax vs 40-45% income tax on rental profit.
3. **Profit retention** — leave profits in the company to buy more properties. Only pay dividend tax when you extract cash.

### The Maths (1 BRRR property, single year)

| | Personal (40% taxpayer) | Ltd Company |
|---|---|---|
| Annual rent | £8,400 | £8,400 |
| Mortgage interest | -£3,300 | -£5,625 (0.75% higher rate) |
| Other costs | -£1,500 | -£1,500 |
| Taxable income | £6,900 (S24 calc) | £1,275 (actual profit) |
| **Tax** | **~£1,800** | **~£242** |
| Net retained | ~£2,800 | ~£1,033 (or more retained in co.) |

The company wins decisively at 3+ properties due to compounding retained profits.

### SPV Setup Checklist

Do in this order before making an offer:

1. **Register company at Companies House** — £100 (fee increased Feb 2026)
   - SIC code: **68209** (Other letting and operating of own or leased real estate)
   - Company name: something like "MH Property Holdings Ltd"
   - Can DIY in ~20 mins at companieshouse.gov.uk

2. **Open a business bank account**
   - Starling: free, good accounting integration via Open Banking
   - Monzo: free, less accounting integration
   - Metro Bank: free (limited period), physical branches

3. **Select specialist property accountant**
   | Option | Monthly | For 1-2 properties | Includes |
   |--------|---------|-------------------|----------|
   | ForeTwo Accounting | £60/mo | £720/yr | FreeAgent, CT returns, 1x SA return, registered office |
   | Provestor (Pro Accounts) | ~£45-60/mo | ~£540-720/yr | Bank feeds, year-end accounts, CT600, 1 property |
   | Local accountant | NA | £450-900/yr | Personal service, less software, may lack property specialism |

   **Recommended:** ForeTwo Accounting at £60/mo — fixed fee, includes everything, specialist in SPVs.

4. **Find an SPV mortgage broker**
   - Fewer lenders than personal BTL. Specialist lenders: Together, Fleet Mortgages, Aldermore, Foundation Home Loans, The Mortgage Works (SPV arm)
   - Rates are typically 0.5-1% higher than personal BTL
   - Fox Davidson is a known broker who handles SPV cases
   - Bridging finance needed first (0.5-0.8%/mo), then refinance to BTL

### Total SPV Running Cost (Year 1)

| Item | Cost |
|------|------|
| Incorporation | £100 (one-off) |
| Confirmation statement | £50/yr |
| Accountant (ForeTwo) | £720/yr |
| Business bank account | £0 (Starling) |
| Extra mortgage interest (~0.75% on £90k) | ~£675/yr |
| **Total** | **~£1,445/yr** |

### Warning: Don't Buy Now, Transfer Later

If you buy the first property in your personal name and later try to transfer it into a company, you trigger:
- **SDLT** at market value (3% surcharge on whatever it's worth at transfer)
- **CGT** at 24% on any gain since purchase
- **Legal fees** for the transfer

The "buy now, transfer later" path is the most expensive option. Buy into the SPV from day one.

## SPV Mortgage Strategy for BRRR

1. **Bridging loan** (6-12 months, 0.5-0.8%/mo, up to 75% LTV) — covers purchase + refurb
2. **Refurbish** — draw down from the bridge as works complete
3. **Refinance to BTL** — 70-75% LTV on the **new, higher** valuation
4. Target: refinance enough to repay the bridge + pull your deposit back out

The bridge interest is higher than a standard mortgage but it's short-term (months), and the refinance step unlocks the equity you manufactured through refurb.

## Rightmove Search Tips for Investors

- **Sort by newest first** (`sortType=6`) — investors snap up good deals fast
- **Keywords in search**: "investment", "project", "renovation", "chain free", "vacant possession", "modernisation"
- **Check listing age** — properties listed 3+ months ago are stale; offer 10-15% below asking (5+ months = 15-20% off)
- **Flats are cheaper but check leasehold terms**, ground rent, service charges — these eat yield
- **Auction properties** (Modern Method of Auction) — buyer pays 4.5% reservation fee (min £6,600) + £349 pack fee. Non-refundable. Must complete in 56 days. Higher risk but can find deals.
- **EPC rating** — minimum C for new tenancies from 2028 (proposed). Budget for upgrades.
- **Agent's own website often has more detail than Rightmove** — check for full tenure info, PDF brochures, and additional photos. Example: uflit.co.uk for Rotherham properties.

### Rightmove Search URL Template

```text
https://www.rightmove.co.uk/property-for-sale/[TOWN].html?sortType=6&maxPrice=[MAX]&minBedrooms=2&dontShow=retirement%2CsharedOwnership
```

For Rotherham sub-£150k:
```text
https://www.rightmove.co.uk/property-for-sale/Rotherham.html?sortType=6&maxPrice=150000&minBedrooms=2&dontShow=retirement%2CsharedOwnership
```

### Listing Evaluation Workflow

1. `web_search("site:rightmove.co.uk <postcode> <price> <type>")` — fast initial scan
2. `browser_navigate` to the full Rightmove search URL for the target town
3. `web_extract` the search results page to see listing summaries
4. `browser_navigate` individual listings for full detail (tenure, EPC, description, photos)
5. `browser_get_images` to extract photo URLs for sharing with the user
6. **Check agent's website** — often has PDF brochures and leasehold details not on Rightmove
7. Share photos directly via `![alt](url)` markdown — Telegram delivers them as native photos

### Negotiation Leverage

| Time on market | Negotiation room |
|----------------|------------------|
| < 1 month | Face value or small offset for costs |
| 1-3 months | 5-10% below asking |
| 3-5 months | 10-15% below asking |
| 5+ months | 15-25% below asking — seller is motivated |

### Leasehold Due Diligence

When a property is listed as Leasehold, check these with the agent:

1. **Years remaining** — 80+ is mortgageable; under 80 creates major issues (costly to extend, lenders refuse)
2. **Annual ground rent** — under £250 is standard; over can be "onerous lease" and spook lenders
3. **Subletting restrictions** — critical for BTL. Some old leases require landlord's consent
4. **Service charges** (for flats) — these eat directly into yield

**Important pattern:** Victorian/Edwardian terraces in Northern cities typically have 999-year leases with peppercorn ground rent — effectively freehold. Always verify, but don't automatically dismiss leasehold in this context.

## Pitfalls

- **Don't trust the "tastefully appointed" language** — it's agent-speak that could mean anything. Always view or get photos.
- **Leasehold properties** — check remaining term (>80 yrs minimum for mortgage), ground rent, service charges. Short leases kill mortgageability.
- **Rightmove bot detection** — the site may block automated browsing without residential proxies. If you hit a block wall, give the user the direct search URL.
- **Modern Method of Auction** — the £6,600+ reservation fee is non-refundable. You can't do a survey and then walk. Only bid if you're confident.
- **Vision analysis may not work** with all models (e.g., DeepSeek doesn't support image_url). Fallback: use `browser_get_images` to extract photo URLs and present as `![alt](url)` markdown.
- **SPV mortgage rates are higher** — 0.5-1% above personal BTL. Factor into BRRR models.
- **Leasehold details often not on Rightmove** — check agent's own website for PDF brochures. If still missing, call the agent.
- **Rightmove postcode search can misfire** — use town/city names for reliable results, narrow by postcode manually.
- **Void periods in the North** — lower tenant demand in some areas. Budget 1-2 months void per year (8-16% vacancy rate).
- **Bridging loans** charge 0.5-1% per month. A 6-month delay on flip completion eats ~£5k+ in interest on a £100k bridge.
- **Capital gains from flipping** — if you flip more than 6 properties in 12 months, HMRC may treat you as trading (income tax instead of CGT). Know the boundaries.

## Full Pipeline Workflow

When the user says they want to invest or hands you a property link, run the full pipeline:

### Phase 1: Research & Find Deals
1. Load `uk-property-investment` for market context
2. Search Rightmove for the target area (use the URL template in this skill)
3. Extract listings, identify candidates with investment potential
4. Open individual listings for full detail (photos, tenure, EPC, room sizes)
5. Check agent's own website for PDF brochures / leasehold detail

### Phase 2: Model the Deal
1. Load `brrr-calculator` skill
2. Run the BRRR model with negotiated price (adjust for days on market)
3. Present the full deal output: acquisition, refurb, refinance, rental, ROI
4. Compare SPV vs personal ownership numbers
5. Flag leasehold concerns and recommend next steps (e.g., "call the agent")

### Phase 3: Set Up the Vehicle (first deal only)
1. Register SPV at Companies House (SIC 68209, £100)
2. Open business bank account (Starling)
3. Engage specialist accountant (ForeTwo £60/mo)
4. Find SPV mortgage broker (Fox Davidson etc.)

### Phase 4: Communicate with Agents
1. Use `wacli` (load wacli skill) to read/reply to estate agent WhatsApp messages
2. Follow the Negotiation Template below
3. Send offers, arrange viewings, request legal packs
4. Forward key updates to the user on their preferred channel

### Phase 5: Track & Manage
- Track refurb budget vs actual spend
- Track timeline toward the 56-day completion window (auction) or refinance trigger
- Log expenses categorised for year-end accountant pack
- Monthly portfolio snapshot: equity, debt, yield, cash position

## Agent Communication via WhatsApp

After finding a property, load the `wacli` skill and use WhatsApp (wacli CLI) to communicate with estate agents on the user's behalf.

### Setup
Run `wacli auth --phone "+44..."` — generates a pairing code. User enters it on their phone: WhatsApp → Linked Devices → Link a Device → Link with phone number. One-time, 30 seconds.

### Use Cases
- **Read agent messages:** `wacli chats list --query "Uflit"` → `wacli messages search "St Anns" --chat <jid> --limit 10`
- **Send replies:** `wacli send text --to "+447090000000" --message "Thanks for the lease info. We'll put in an offer at £70,000."`
- **Forward to user:** Summarise the agent's message on Telegram with your response and next steps
- **Autonomous negotiation:** When the user says "handle it", monitor the thread and reply without asking at every step

### Negotiation Template (Used Autonomously)

When the user says "handle the back-and-forth on [property]":

1. Confirm lease terms: "Could you confirm the remaining lease length and ground rent?"
2. Confirm chain: "Is there an onward chain or is this vacant possession?"
3. Ask for EPC: "Can you share the EPC certificate?"
4. Make a conditional offer referencing days on market: 
   - 3+ months: "We'd like to offer £[10-15% below] considering it's been on the market for X months."
   - 5+ months: "The property has been listed for 5+ months. We can offer £[15-20% below] with a fast completion."
5. Ask for legal pack: "Please send the legal pack / seller's information form over."

### Behaviour Mode
The user prefers **maximum autonomy** — push hard without asking. When they say "handle the negotiations" or "deal with the agent", do it. Don't ask "shall I reply saying X?" — just reply and tell the user what you did.

## References

- **brrr-calculator** skill: Run `skill_view(name='brrr-calculator')` for full deal modelling
- **references/example-deal.md** in brrr-calculator: worked St. Anns Road example
- **wacli** skill: Run `skill_view(name='wacli')` for WhatsApp agent communication setup and commands
- **references/agent-templates.md**: Pre-written agent message templates for lease enquiries, offers, viewing requests

## Regional Reference Data (March 2026)

See `references/top-yields-by-city.md` for the full table of yields by city.

Top 5:
1. Newcastle — 9.7% gross (£1,177/mo avg rent, £76k deposit)
2. Leeds — 9.6% gross (£1,118/mo avg rent, £85k deposit)
3. Nottingham — 9.0% gross
4. Southampton — 9.0% gross
5. Aberdeen — 8.6% gross (cheapest deposit at £47k)

For Rotherham-specific research, see `references/rotherham-local-market.md`.
