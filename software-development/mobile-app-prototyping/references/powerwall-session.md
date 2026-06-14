# Powerwall + Octopus Energy Monitor Session

## Project Structure

```
powerwall-app/
├── app/
│   ├── _layout.tsx           # Root expo-router layout
│   └── (tabs)/
│       ├── _layout.tsx       # 5-tab bar (Dashboard, Energy, Solar, Battery, Settings)
│       ├── index.tsx         # Dashboard — live Powerwall data, cost card, energy flow
│       ├── energy.tsx        # Octopus tariffs, IOG slots, cost analysis
│       ├── solar.tsx         # Solar-specific view
│       ├── battery.tsx       # Battery-specific view
│       └── settings.tsx      # NetZero/Octopus/Tesla credential entry
├── src/
│   ├── api.ts                # NetZero + Tesla Powerwall API + Octopus state fetcher
│   ├── octopus.ts            # Octopus Energy API module (tariffs, consumption, IOG)
│   ├── theme.ts              # Tesla-style dark theme constants
│   ├── types.ts              # All TypeScript interfaces
│   └── components/
│       ├── EnergyFlow.tsx    # SVG energy flow visualization
│       └── MetricCard.tsx    # Live metric display card
```

## API Integration Architecture

### Data Flow
```
Settings → Store tokens (in-memory) → Dashboard/Energy fetch
     ↓
  fetchPowerwallData() → NetZero API (primary) → Tesla API (fallback) → Mock
  fetchOctopusState()  → Octopus API rates + IOG slots + consumption
     ↓
  Dashboard: live data + cost card (combines Powerwall + Octopus)
  Energy tab: tariff rates, cost analysis, IOG slots, upcoming rates
```

### NetZero API (Powerwall 3)
```
GET https://netzero.energy/api/v1/{site_id}/config
Auth: Bearer token
Response includes: live_status (solar_power, battery_power, grid_power, 
  load_power, percentage_charged, grid_status, island_status, 
  storm_mode_active, battery_count, nominal_full_pack_energy)
```

### Tesla Owner API (Fallback)
```
GET https://owner-api.teslamotors.com/api/1/energy_sites/{site_id}/live_status
GET https://owner-api.teslamotors.com/api/1/energy_sites/{site_id}/site_info
Auth: OAuth2 Bearer token with refresh flow
```

### Octopus Energy API
See `references/octopus-energy-api.md` for full endpoint reference.

## Key Design Decisions

- **Dark Tesla-style theme** (#000 background, green accents, tab bar)
- **5 tabs** — Dashboard (primary), Energy (new), Solar, Battery, Settings
- **Octopus data on Dashboard** — Live Cost card shows real-time import/export £/h
- **Energy tab** — dedicated deep-dive into tariffs, IOG slots, cost analysis
- **Settings** — central credential management with connection status indicators
- **Mock data fallback** — works without any API keys for preview/demo

## Token Storage

All tokens stored in-memory only (no AsyncStorage/persistence yet):
- `setNetZeroToken()` / `getNetZeroToken()`
- `setTeslaCredentials()` / `getTeslaCredentials()`
- `setOctopusCredentials()` / `getOctopusCredentials()`

Tokens lost on app restart. User must re-enter in Settings.
