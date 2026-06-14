# React Native / Expo — Energy Monitoring App Integration

This reference covers building a cross-platform mobile energy monitoring app (Expo/React Native) that integrates Tesla Powerwall (via NetZero API) and Octopus Energy API. Built and tested on Expo SDK 54.

## Architecture

```
app/(tabs)/
  index.tsx      — Dashboard: live Powerwall data + cost card
  energy.tsx     — Octopus tariffs, IOG slots, cost analysis
  solar.tsx      — Solar generation detail
  battery.tsx    — Battery status detail
  settings.tsx   — API key config, tariff codes, connection testing
src/
  api.ts         — Powerwall data (NetZero → Tesla → mock fallback)
  octopus.ts     — Octopus Energy API module
  types.ts       — All TypeScript interfaces
  theme.ts       — Dark theme tokens
  components/
    EnergyFlow.tsx   — SVG energy flow diagram
    MetricCard.tsx   — Reusable metric card
```

## Key React Native Gotchas

### 1. `btoa()` / `atob()` NOT available in Hermes

React Native (Hermes engine) does not have `btoa()` or `atob()`. Any API that uses Basic Auth must implement Base64 manually:

```typescript
function authHeader(apiKey: string): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=';
  const str = apiKey + ':';
  let output = '';
  for (let i = 0; i < str.length; i += 3) {
    const a = str.charCodeAt(i) || 0;
    const b = str.charCodeAt(i + 1) || 0;
    const c = str.charCodeAt(i + 2) || 0;
    output += chars[a >> 2];
    output += chars[((a & 3) << 4) | (b >> 4)];
    output += chars[((b & 15) << 2) | (c >> 6)];
    output += chars[c & 63];
  }
  const pad = str.length % 3;
  if (pad === 1) output = output.slice(0, -2) + '==';
  if (pad === 2) output = output.slice(0, -1) + '=';
  return 'Basic ' + output;
}
```

### 2. Text MUST be in `<Text>` components

React Native throws "Text strings must be rendered within a <Text> component" if you put raw strings/numbers in a `<View>`. Common mistake: styling a `<View>` to look like text, putting the value inside. All text content must be `<Text>` or nested `<Text>`.

```tsx
// WRONG — View with text content
<View style={styles.labelValue}>{value}</View>

// RIGHT — Text component
<Text style={styles.labelValue}>{value}</Text>
```

### 3. `react-native-screens` version must match RN

| RN Version | Compatible react-native-screens |
|-----------|--------------------------------|
| 0.76.x | 3.37.0 or 4.24.0 (*) |
| 0.81.x | 4.24.0 or 4.25.x (**) |

(*) 4.24.0 is the last version with `react-native: *` peer dep — 4.25.0+ requires RN >= 0.82.
(**) Use 4.24.0 for maximum compatibility with SDK 54.

## Octopus Energy API — React Native Patterns

### API Auth
- HTTP Basic Auth with API key as username, empty password
- Base64-encode `api_key:` (see gotcha #1 above)
- API keys from https://octopus.energy/dashboard/developer/

### Tariff Codes
The user's specific tariff codes must be configurable in Settings — never hardcode. Common Octopus tariff formats:

| Tariff | Product Code | Tariff Code | Example |
|--------|-------------|-------------|---------|
| Intelligent Octopus Go | `INTELLI-VAR-22-10-14` | `E-1R-INTELLI-VAR-22-10-14` | Import |
| Agile Octopus | `AGILE-FLEX-22-11-25` | `E-1R-AGILE-FLEX-22-11-25` | Import |
| Octopus Go | `GO-V3-22-10-14` | `E-1R-GO-V3-22-10-14` | Import |
| Agile Outgoing | `AGILE-OUTGOING-19-05-17` | `E-1R-AGILE-OUTGOING-19-05-17` | Export |
| Outgoing Fixed | `OUTGOING-FIXED-24-04-23` | `E-1R-OUTGOING-FIXED-24-04-23` | Export |

The `E-1R-` prefix means "electricity, single register" and the `-C` suffix (e.g. `-C` for Climate) is sometimes optional.

### API Endpoint Pattern
```
GET /v1/products/{product_code}/electricity-tariffs/{tariff_code}/standard-unit-rates/
GET /v1/electricity-meter-points/{mpan}/meters/{serial}/consumption/
```

### Handling Rate Data
- Times are UTC — convert to local for display
- Results are newest-first — reverse for chronological
- Rates are in pence (GBX) per kWh — divide by 100 for £
- Agile has 48 half-hour slots per day, published ~16:00 for next day

### Error Handling Pattern
```typescript
try {
  const data: any = await octoGet(path);
  return (data.results || []).map(...);
} catch { return []; }  // Don't crash the UI — return empty
```

### Connection Testing
```typescript
async function testOctopusConnection(apiKey: string, accountNumber: string): Promise<string | null> {
  const resp = await fetch(`${API}/accounts/${accountNumber}/`, {
    headers: { Authorization: authHeader(apiKey) },
  });
  if (resp.status === 401) return 'Invalid API key';
  if (resp.status === 404) return 'Account not found';
  if (!resp.ok) return `HTTP ${resp.status}`;
  return null; // success
}
```

## NetZero API — React Native Pattern

```typescript
const NETZERO_API = 'https://netzero.energy/api/v1';
const SITE_ID = '1689543131745218';

async function fetchPowerwallData(token: string) {
  const resp = await fetch(`${NETZERO_API}/${SITE_ID}/config`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await resp.json();
  // live_status is NESTED inside config response
  const live = data.live_status || {};
  return {
    solar_kw: (live.solar_power || 0) / 1000,
    battery_kw: (live.battery_power || 0) / 1000,
    grid_kw: (live.grid_power || 0) / 1000,
    home_kw: (live.load_power || 0) / 1000,
    battery_percent: live.percentage_charged || 0,
  };
}
```

## Tab Navigation Pattern (expo-router)

```tsx
<Tabs
  screenOptions={{
    tabBarStyle: { backgroundColor: '#0d0d0d', borderTopColor: '#1a1a1a' },
    tabBarActiveTintColor: '#30d158',  // green
    tabBarInactiveTintColor: '#636366',
  }}
>
  <Tabs.Screen name="index" options={{ title: 'Dashboard', tabBarIcon: ... }} />
  <Tabs.Screen name="energy" options={{ title: 'Energy', tabBarIcon: ... }} />
  ...
</Tabs>
```

## Mock Data Fallback

Always provide mock data as a fallback so the UI is visible without credentials:

```typescript
return {
  solar_kw: 3.2, battery_kw: -1.8, grid_kw: -1.2, home_kw: 0.8,
  battery_percent: 72, timestamp: new Date().toISOString(),
  source: 'mock',  // track data source
};
```

## API Token Storage

Tokens are stored in-memory (module-level variables) since this is a personal mobile app. No secure storage/Keychain is used — tokens persist only as long as the app is in memory (not between app restarts). For production, use `expo-secure-store`.
