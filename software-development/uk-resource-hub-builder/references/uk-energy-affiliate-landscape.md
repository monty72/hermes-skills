# UK Energy Supplier Affiliate & Monetization Landscape

Research findings for monetizing a UK energy comparison / EV / solar site.

## Summary

Only **Octopus Energy** has a straightforward referral program. Most other suppliers have no public affiliate or referral links. The viable monetization routes for a UK energy site are:

1. **Octopus referral** (direct, working now)
2. **Cashback site publisher programs** (TopCashback, Quidco)
3. **Comparison site affiliate networks** (uSwitch, MoneySuperMarket via CJ/Awin/Impact)
4. **Solar installer directories** (generator companies, installers with affiliate programs)
5. **Grid services referrals** (Axle Energy — battery/grid balancing)

---

## Supplier-by-Supplier

### Octopus Energy ✅ Referral
- **Your link**: `https://share.octopus.energy/open-lake-523`
- **Structure**: Standard share link format
- **Commission**: £50 each way (referrer + referee gets credit)
- **Partner program**: Octopus offers custom `affiliate=<name>.octopus.energy` links for content creators. GaryDoesSolar uses `affiliate=garywaite.octopus.energy` — applied as a query param on the quote page URL: `octopus.energy/quote/?affiliate=garywaite.octopus.energy`
- **How to get the upgraded format**: Email Octopus's partnership team and ask for a custom affiliate subdomain or quote URL param. Having a live site with energy comparison content is usually enough.
- **Key tariffs to mention**: Agile, Intelligent Octopus Go (7p/kWh off-peak), Cosy (12p day / 9p night), Flux (up to 15p export), Tracker (daily wholesale), Outgoing Agile (half-hourly export)

### E.ON Next ❌ No referral
- No public referral or affiliate program
- Their "Refer a Friend" is customer-only via the app
- **Best tariff**: Next Drive (6.9p/kWh off-peak — lowest in UK for EV owners)
- **Monetization route**: Cashback site only

### British Gas ❌ No referral
- No public referral or affiliate program
- Best known: PeakSave Sunday (free electricity some Sundays), EV Tariff (~8p off-peak + free charging miles)
- **Monetization route**: Cashback site only

### OVO ❌ No referral
- Had a referral program, closed it
- **Monetization route**: Cashback site only

### Scottish Power ⚠️ Via cashback
- **TopCashback**: Up to £95 cashback per switch
- Not accessible as a direct affiliate link — you'd need to sign up as a TopCashback publisher

### EDF ❌ No referral
- No public program

### Utilita ❌ No referral
- No public program (specialist PAYG supplier)

---

## Monetization Route Options

### Route A: Cashback Site Publisher

Both **TopCashback** and **Quidco** have publisher (affiliate) programs. You create pages with comparison content and link through their platform:

- **TopCashback publisher**: Join their affiliate program via Awin or their own platform. You get a cut of the cashback when users switch.
- **Quidco publisher**: Similar model.
- **Payout per switch**: £20–£95 depending on supplier and cashback rate.
- **How to integrate**: Create `/switch-to-[supplier]` pages on your site that explain the tariff, show estimated savings, then link to the cashback site's tracking URL.

### Route B: Comparison Site Affiliate Networks

The major UK comparison sites have publisher programs through standard affiliate networks:

| Network | Platform | Comparison Sites |
|---------|----------|-----------------|
| **CJ Affiliate** | CJ.com | uSwitch, CompareTheMarket |
| **Awin** | Awin.com | MoneySuperMarket, GoCompare |
| **Impact** | Impact.com | Energy Helpline, Look After My Bills |

- **Payout**: £30–£80+ per completed switch
- **How it works**: You sign up as a publisher, get a tracking link, embed it in comparison content
- **Lead time**: Application takes 1-2 weeks, sites must meet quality standards

### Route C: Solar / Battery / Installer Affiliates

Gary Does Solar's "Installer Directory" page (`getreadyfor.solar`) is monetized via **lead generation** — users enter their email and postcode, installers pay per qualified lead. Other opportunities:

- **GivEnergy** (battery manufacturer) — has a partner/referral program
- **Fox ESS** (battery/inverter manufacturer) — dealer program
- **MyEnergi** (zappi EV charger) — installer finder partner
- **Solar Together / Solarplicity** — community solar buying schemes

### Route D: Grid Services (Axle Energy)

Gary promotes **Axle Energy** with a custom referral code: `vpp.axle.energy/landing?ref=R-GARYSOLAR`. This is a grid flexibility service:

- **How it works**: Battery owners sign up, Axle manages grid events (discharge during high demand), owner gets paid £100–£300/yr
- **Compatible with**: Sigenergy, FOX ESS, GivEnergy, SolaX, Solis, SolarEdge
- **Your angle**: Your site has a real Powerwall 27 kWh setup with live data — you're an authentic voice for grid services content
- **Referral model**: Custom referral codes are issued per partner (like `R-<YOURNAME>`)

---

## GaryDoesSolar Model Breakdown

Gary runs a multi-revenue energy/solar site at `garydoessolar.com`. Here's his model:

### Revenue Streams
1. **Octopus Energy referral** — `garydoessolar.com/octopus` redirects to `octopus.energy/quote/?affiliate=garywaite.octopus.energy`. £50 per signup.
2. **Axle Energy grid services** — `garydoessolar.com/axle` redirects to `vpp.axle.energy/landing?ref=R-GARYSOLAR`. Commission per signup.
3. **Installer directory** — `getreadyfor.solar` — lead-gen for solar installers. Users enter email → get matched with MCS-certified installers. Installers pay per lead.
4. **Patreon** — `patreon.com/GaryDoesSolar` — membership/community, recurring monthly income.
5. **YouTube** — main traffic driver with regular solar/energy content. Monetized via ads + all the above links in descriptions.
6. **Modelling tools** — `solarazma.com` — solar generation estimator and battery payback calculators, driving organic traffic.

### How the Installer Directory Works
```
User → garydoessolar.com → clicks "Installer Directory"
→ getreadyfor.solar → enters email
→ gets OTP → enters postcode → gets matched with installers
→ Installers pay per qualified lead
```
The flow is email-gated (email + OTP verification), which ensures lead quality for installers.

### Key Takeaway
Gary's site isn't really about energy **supplier** referral income — it's about:
- **Solar installer lead-gen** (biggest earner)
- **Octopus referral** (secondary, runs on autopilot)
- **Axle Energy** (newer, growing)
- **Patreon + YouTube** (community monetization)

---

## Content Strategy

### Pages to build on your site
1. **`/energy-providers`** — 7 supplier comparison (done)
2. **`/ev`** — EV ownership guide with cost per mile calculator (done)
3. **`/energy/calculator`** — tariff comparison tool (done)
4. **`/switch-to-octopus`** — dedicated landing page pushing your referral link
5. **`/best-ev-tariffs`** — SEO play for "best EV tariff UK"
6. **`/solar-payback`** — real Powerwall savings data with referral links

### Affiliate disclosure placement
UK law (ASA/CAP Code) requires clear disclosure before any affiliate link. Place an amber-highlighted banner on every page with monetized links:

```html
<div style="background: rgba(251,191,36,0.1); border: 1px solid rgba(251,191,36,0.3); padding: 12px; border-radius: 12px;">
  ⚖️ <strong>Affiliate Disclosure:</strong> Some links on this page are referral/affiliate links.
  I may earn a small commission at no extra cost to you. GOV.UK and official supplier links are never affiliate links.
</div>
```

### Octopus referral placement (proven patterns from GaryDoesSolar)
- Redirect page: `/redirect/octopus` → `https://share.octopus.energy/open-lake-523`
- Featured on landing page as a card
- In-content callout boxes on energy/EV/solar pages
- Footer link
- Tooltip/Callout on tariff comparison results (if someone picks Octopus)

## Research Sources

- **GaryDoesSolar**: `https://garydoessolar.com` — Octopus link on homepage, Axle Energy affiliate (`R-GARYSOLAR`), Patreon, installer directory at `getreadyfor.solar`
- **Octopus Energy**: `https://octopus.energy/quote/?affiliate=<partner>.octopus.energy`
- **Axle Energy**: `https://vpp.axle.energy/landing?ref=<code>`
- **TopCashback**: Scottish Power £95 cashback visible on `topcashback.co.uk/energy`
- **CJ Affiliate**: `cj.com` — uSwitch and CompareTheMarket publisher programs
- **Awin**: `awin.com/gb/publisher/affiliate-partners` — MoneySuperMarket publisher program
- **Impact**: `impact.com` — performance partnerships platform
