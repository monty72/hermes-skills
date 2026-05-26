# Axle Energy & Gary Does Solar Model — Research Notes

## Gary Does Solar (`garydoessolar.com`)

### Site Structure
- Landing page with 11 link cards: New To Solar, YouTube, Installer Directory, Chat With Gary, Solar Generation Estimator, Battery Payback Calculator, Modelling Tools, Patreon, **Octopus Energy (£50 credit)**, **Alex/Axle Energy (£25 sign-up)**
- Clean HTML/CSS, no framework (basic static site)
- YouTube-driven content with Patreon for deeper support

### Octopus Energy Link
- `/octopus` → redirects to `octopus.energy/quote/?affiliate=garywaite.octopus.energy`
- That URL parameter `?affiliate=garywaite.octopus.energy` — Octopus assigns per-account affiliate IDs
- Your link format: `share.octopus.energy/open-lake-523` — same system, different format
- Renders as a link card image (`img/menu_octopus.jpg`)

### Axle Energy (Alex Energy) Link
- Label on his site says "Alex Energy Get £25 on Sign-up!"
- `/axle` → redirects to `vpp.axle.energy/landing?ref=R-GARYSOLAR`
- Gary's referral code on Axle is `R-GARYSOLAR`
- The referral is for the VPP grid services program, not an energy supplier
- Pays £25 per sign-up? (label says £25, but Axle's own docs say £50/installer referral)

### Installer Directory
- `getreadyfor.solar` — separate subdomain for installer lead-gen
- `/directory/start` — email capture, sends 4-digit OTP
- Private directory (paywalled behind email authentication) — "handpicked by me"
- Model: installers pay per lead or per placement in directory
- Installers: he's building trust via YouTube, then monetises via lead sales

### Full Monetisation Stack
1. **YouTube** → builds trust, drives traffic
2. **Octopus referral** → £50 per sign-up (low friction, everyone can switch)
3. **Axle Energy referral** → £25–£50 per VPP enrolment (solar/battery owners)
4. **Installer directory lead-gen** → £50–£200+ per lead (highest margin)
5. **Patreon** → recurring subscription from super-fans
6. **Solar modelling tools** → free tools that drive traffic

## Axle Energy VPP

### Compatible Brands (as of May 2026)
- **Solis** — partnership announced March 2026. Works via Solis hybrid inverters + batteries
- **SolaX** — partnership announced February 2026
- **FoxESS** — partnership announced January 2026
- **GivEnergy** — supported (listed on their "Works With" section)
- **SolarEdge** — supported
- **Sigenergy** — supported

### NOT Compatible
- Tesla Powerwall (all generations)
- Any closed-protocol system

### Earnings Model
- ~£1/kWh of battery capacity during grid events
- £10/month minimum guarantee (until March 2026)
- Fully automated — battery charges/discharges during events
- User keeps full control of schedule
- Works alongside Octopus Agile/Tracker/Flux

### Installer Referral
- Installers get £50 per customer enrolled
- Sign-up: `https://vpp.axle.energy/landing/grid`

### How It Works
1. Axle participates in UK flexibility markets (DFS, Capacity Market, frequency response, local DNO markets)
2. During grid events, Axle signals compatible batteries to discharge (shave peak demand) or charge (absorb excess renewables)
3. The VPP aggregates thousands of batteries into a single marketable asset
4. Payments distributed to battery owners minus Axle's fee

### Key URLs
- Main site: `axle.energy`
- VPP landing: `vpp.axle.energy/landing`
- VPP landing (grid): `vpp.axle.energy/landing/grid`
- Blog: `axle.energy/blog`
- Blog articles: `axle.energy/blog/solis`, `axle.energy/blog/foxess-and-axle-partner-to-boost-battery-earnings`, `axle.energy/blog/solax-and-axle-announce-global-partnership`
