---
name: mobile-app-prototyping
description: >-
  Build mobile-like app experiences for iOS/Android in a headless environment.
  Scaffolds React Native (Expo) projects first; falls back to standalone PWA
  (Add to Home Screen) when Expo Go has SDK compatibility issues or native
  build tools are unavailable. Covers Tesla-style dark UIs, energy monitoring
  dashboards, and API-connected live data.
tags: [mobile, ios, react-native, expo, pwa, prototyping]
---

# Mobile App Prototyping

## Overview

When a user asks for a mobile app in a headless environment (no Mac, no Xcode, no Apple Developer account), this skill provides the build-deploy workflow:

1. **Scaffold** an Expo React Native project with expo-router, tabs layout, dark theme, and SVG-based visualisation
2. **Deploy via PWA fallback** when Expo Go is incompatible (SDK version mismatch, headless terminal can't show QR codes)
3. **Deliver to user** — tell them to open the URL in Safari and "Add to Home Screen" for a native-feeling icon + full-screen experience

## Prerequisites

```bash
npm install -g create-expo-app @expo/ngrok
```

## Expo SDK Version Reference

> 📖 See `references/sdk-downgrade-debugging-recipes.md` for a full debugging transcript of a real SDK 56→54 downgrade with all errors encountered and fixes applied.
> 📖 See `references/sdk-version-drift.md` for details on how later Expo SDK point releases silently change their React/RN baseline — the table below may not match the latest published `expo` version.

When an existing Expo project needs SDK downgrade, use this version mapping (SDK 54 as reference — adjust RN version per target SDK):

| Package | SDK 56 | SDK 54 (early — RN 0.76) | SDK 54 (late — RN 0.81) |
|---|---|---|---|---|
| expo | ~56.0.x | 54.0.0–54.0.26 | **54.0.27+** (same SDK number, different stack) |
| react-native | 0.85.x | 0.76.7 | 0.81.5 |
| react | 19.2.x | 18.3.1 | 19.1.0 |
| react-dom | 19.2.x | 18.3.1 | 19.1.0 |
| react-native-screens | >=4.0.0 (4.25.0+ needs RN >=0.82) | **4.24.0** (last v4.x compatible with RN 0.76; 4.25.0+ requires RN >=0.82) | ~4.16.0 (or latest 4.x) |
| react-native-reanimated | ^4.0.x | ^3.16.x | ~4.1.1 |
| react-native-safe-area-context | ~5.7.x | 4.14.1 | ~5.6.0 |
| react-native-svg | 15.15.x | 15.8.0 | 15.12.1 |
| react-native-web | ~0.21.x | ~0.19.13 | ^0.21.0 |
| @expo/metro-runtime | ~56.0.x | ^4.0.0 | ~6.1.2 |
| expo-linear-gradient | ~56.0.x | ^14.0.0 | ~15.0.8 |
| expo-router | ~56.x (v4.x) | ^4.0.0 (v4.0.22 — needs expo-linking ~7.0.5, expo-constants ~17.0.8) | ~6.0.24 |
| expo-linking | ~56.x | ~7.0.5 (peer dep of expo-router@4.0.22) | ~8.0.12 |
| expo-constants | ~56.x | ~17.0.8 (peer dep of expo-router@4.0.22) | ~18.0.13 |
| expo-status-bar | ~56.x | **3.0.9** — no 54.x series exists; jumps from 3.x to 55.x | ~56.x |
| lucide-react-native | ^1.17.x | ^0.460.x | ^0.460.x |
| @react-navigation/native | ^7.x | ^7.x (uses legacy-peer-deps) | ^7.x |
| @react-navigation/bottom-tabs | ^7.x | ^7.x (but peer-dep conflict — see pitfall) | ^7.x |
| typescript | ~6.0.x | ~5.3.x | ~5.9.x |
| @types/react | ~19.2.x | ~18.3.x | ~19.1.x |

**⚠️ Critical: Same "SDK 54" — two completely different stacks.** Later point releases of `expo@^54.0.0` (54.0.27+) silently switched from RN 0.76/React 18 to RN 0.81/React 19. Both are published under `^54.0.0`. The server startup warnings ("expected version") are the authoritative truth for YOUR installed expo version. See `references/sdk-version-drift.md` for full details.

**Key conflicts with @react-navigation/bottom-tabs on SDK 54:**
- v7.x declares `react-native-screens >=4.0.0` as peer dependency
- SDK 54 (RN 0.76.7) needs react-native-screens 4.24.0 or older (4.25.0+ requires RN >=0.82)
- **Fix:** pin `react-native-screens: "4.24.0"` — this is the last v4.x that accepts RN 0.76. Avoid 3.x entirely (causes "Runtime not ready" invariant violation later)
- Install with `npm install --legacy-peer-deps` to resolve the peer-dep mismatch

## Workflow

### Phase 0: Detect Expo Go SDK Version

Before scaffolding, determine what SDK the user's Expo Go supports, and whether the "Enter URL manually" field is present:

1. Ask the user to check **Expo Go app → Settings → About** for the version number
2. SDK version = major version of Expo Go app (e.g. Expo Go 54.x = SDK 54)
3. Ask them to look at the Expo Go homescreen — **if they don't see a text field at the top** for pasting URLs, the app was updated and the field was removed. You'll need **Phase 1c** (tunnel + QR code) to deliver the project.
4. The latest published SDK is 56 — if user has an older version, **downgrade** (Phase 1b) instead of upgrading the app

### Phase 1a: Scaffold Expo Project (Fresh Start)

Use this when building from scratch with the user's known SDK version. For SDK 56:

```bash
npx create-expo-app@latest my-app --template blank-typescript
cd my-app
npx expo install expo-router expo-status-bar expo-linear-gradient react-native-svg react-native-safe-area-context @react-navigation/native @react-navigation/bottom-tabs lucide-react-native
```

### Phase 1b: Downgrade Existing Expo Project

Use this when the project was built on a newer SDK than the user's Expo Go supports (e.g. project on SDK 56 but user has Expo Go 54.x).

Steps:

1. **Kill any running Expo server** — port conflicts will block the new one
2. **Wipe and recreate** — delete `node_modules/` and `package-lock.json`
3. **Decide your approach:**

   **Approach A — Pin to well-known versions** (keep RN 0.76, React 18):
   Update `package.json` with the "SDK 54 (early)" column from the version table above.
   ```bash
   npm install --legacy-peer-deps
   ```

   **Approach B — Align to what this expo actually expects** (use RN 0.81, React 19):
   Start the server first to see the "expected version" warnings, then install those exact versions:
   ```bash
   ./node_modules/.bin/expo start --lan --port 8083
   # Read the "expected version" warnings from the output, then:
   npm install react@19.1.0 react-dom@19.1.0 react-native@0.81.5 \\
     @expo/metro-runtime@~6.1.2 expo-constants@~18.0.13 \\
     expo-linking@~8.0.12 expo-router@~6.0.24 \\
     react-native-reanimated@~4.1.1 react-native-safe-area-context@~5.6.0 \\
     react-native-screens@~4.16.0 react-native-svg@15.12.1 \\
     react-native-web@^0.21.0 --legacy-peer-deps
   ```

   **Which to choose?** Approach A keeps the older (but stable) RN 0.76 stack. Approach B uses what the latest expo point release expects and avoids CLI version mismatch errors for good. If user's Expo Go supports "SDK 54", either works — the Expo Go app handles both RN versions under the same SDK number.

4. **Start in LAN mode:**
   ```bash
   ./node_modules/.bin/expo start --lan --port 8083
   ```
   Use `./node_modules/.bin/expo` NOT `npx expo` — the global npx version may be a different SDK.

5. **Deliver the URL to the user** — give them the `exp://` address shown in the output (e.g. `exp://192.168.1.x:8083`). They paste it into Expo Go via "Enter URL manually".

6. If LAN mode doesn't work (different network), try tunnel mode instead:
   ```bash
   ./node_modules/.bin/expo start --tunnel --port 8083
   ```
   Note: Tunnel requires @expo/ngrok and may hang on first binary download in non-interactive mode.

**Verification:** The server output should show `› Using Expo Go` and `› Metro waiting on exp://...:8083` — no "expected version" warnings or version incompatibility errors.

Key configuration for expo-router:
- `package.json` → `"main": "expo-router/entry"`
- `app/_layout.tsx` — root layout wrapping `<Stack>`
- `app/(tabs)/_layout.tsx` — tab bar layout with `lucide-react-native` icons
- `app/(tabs)/index.tsx` — main screen

### Phase 2: Build Tesla-Style Dark Theme

```
Theme:
  bg:        #000000 (true black — OLED-friendly)
  bgCard:    #0d0d0d
  border:    #1a1a1a
  text:      #ffffff
  accent:    #30d158 (green) for battery/power
  accent2:   #ff9f0a (orange) for solar
  accent3:   #5ac8fa (teal) for home consumption
  accent4:   #8e8e93 (grey) for grid
```

**Key UI components:**
- Energy flow SVG: animated rings, arrows between solar→battery→home→grid
- Battery gauge: circular SVG path with dynamic `stroke-dasharray`
- Metric cards: card with left accent border, icon, title, value, subtitle
- Tab bar: 4-item bottom bar with lucide icons + active state

### Phase 3: API Integration

Connect to live data sources. For Tesla Powerwall / home energy:

```typescript
// Primary: NetZero API (no auth flow needed — just a bearer token)
const resp = await fetch(`https://netzero.energy/api/v1/${SITE_ID}/config`, {
  headers: { Authorization: `Bearer ${TOKEN}` },
});
const d = await resp.json();
const live = d.live_status || {};
// Returns: solar_power, battery_power, grid_power, load_power (watts),
//          percentage_charged, grid_status, island_status, storm_mode_active

// Fallback: Tesla Owner API (needs OAuth2 token + refresh)
const resp = await fetch(`${OWNER_API}/api/1/energy_sites/${SITE_ID}/live_status`, {
  headers: { Authorization: `Bearer ${TOKEN}` },
});
```

**Token management:** Store in `localStorage` under a known key. Provide a Settings screen with a password input and "Save" button. Auto-read on app load.

### Phase 4: PWA Fallback (When Expo Go Fails)

**Trigger:** User reports "Project is incompatible with this version of expo go" or "QR code won't scan"

**Build the standalone PWA:**

1. **Single-file approach:** Create a self-contained `index.html` with inline CSS + JS — no bundler, no build step, loads instantly
2. **iOS PWA meta tags:**
   ```html
   <meta name="apple-mobile-web-app-capable" content="yes">
   <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
   <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
   <link rel="apple-touch-icon" href="data:image/svg+xml,...">
   ```
3. **Data flow replaces React state:** Plain JS object for mock data, `fetch()` for live API, `setInterval(15000)` for auto-refresh, touch events for pull-to-refresh
4. **SVG energy flow** — inline `<svg>` elements instead of `react-native-svg`
5. **No dependencies:** One HTML file + `manifest.json` + `sw.js` (minimal)
6. **Safe area:** CSS `env(safe-area-inset-top)` and `env(safe-area-inset-bottom)` for iPhone notch + home indicator

**Deployment:**
```bash
# Kill old processes first (ports may conflict)
kill $(pgrep -f 'localhost.run') 2>/dev/null

# Start HTTP server on a unique port
cd ./dist && python3 -m http.server 8091 &

# Create SSH tunnel (don't use --tunnel with expo — use localhost.run directly)
ssh -R 80:localhost:8091 nokey@localhost.run
# Grab the URL from the output: https://<hash>.lhr.life

# Verify
curl -s -o /dev/null -w "%{http_code}" https://<hash>.lhr.life
# Should return 200
```

**Delivery to user:**
```
Open this URL in Safari on your iPhone:
https://<hash>.lhr.life

Then tap Share → Add to Home Screen → name it → Add.
It gets its own icon, full-screen with no browser chrome.
```

### Phase 5: Live Data Connection

User pastes their API token in the Settings screen. The token is stored in `localStorage` and picked up on every auto-refresh cycle.

```javascript
// On app load
let token = localStorage.getItem('netzero_token') || '';

// On save
function saveToken(t) {
  localStorage.setItem('netzero_token', t);
  token = t;
  fetchLiveData();
}

// On refresh cycle (15s interval)
async function fetchLiveData() {
  if (!token) return; // use mock data
  // ... fetch from NetZero or Tesla API
}
```

### Phase 1c: Deliver to Expo Go (No URL Entry Field)

> 📖 See `references/expo-go-tunnel-qr-delivery.md` for full workflow with QR code generation commands and the deep-link redirect page approach.
> 📖 See `references/octopus-energy-api.md` for UK energy tariff API endpoints, auth pattern, and account reference.
> 📖 See `references/powerwall-session.md` for the full Tesla/NetZero/Octopus energy dashboard session transcript.

Newer versions of Expo Go have **removed the "Enter URL manually" field** from the homescreen. You can no longer paste an `exp://` URL. Two workarounds:

**Option A — QR Code (recommended):** Start expo in `--tunnel` mode to get a public `exp://` URL, then generate a QR code the user can scan with their iPhone Camera app:

```bash
# 1. Start with tunnel
./node_modules/.bin/expo start --tunnel --port 8084

# 2. Grab the exp:// URL from output (e.g. exp://abc123-anonymous-8084.exp.direct)

# 3. Generate QR code via external API
curl -s "https://api.qrserver.com/v1/create-qr-code/?size=400x400&data=exp://abc123-anonymous-8084.exp.direct" \
  -o /tmp/expo-qr.png

# 4. Send QR image to user inline via MEDIA:/tmp/expo-qr.png
#    User opens iPhone Camera app, scans QR, taps the notification to open in Expo Go
```

**Option B — Deep Link Redirect Page:** Create an HTML page with an `exp://` anchor link and embedded QR code (from `api.qrserver.com`), serve it via a simple HTTP server, and tunnel it with `lhr.life`:

```bash
# Serve a redirect page on port 8085
cd /tmp && python3 -m http.server 8085 &

# Create index.html with:
# • <img src="https://api.qrserver.com/...&data=exp://..."> 
# • <a href="exp://...">Open in Expo Go</a>
```

Then user visits the tunnel URL in Safari and taps the "Open in Expo Go" button.

**Which to use?**
- QR code (Option A) is fastest — one curl command, send image, user scans
- Redirect page (Option B) is a fallback when QR scanning doesn't trigger (uncommon, but can happen on older iOS)
- Both work without the user finding a nonexistent "Enter URL manually" field

## Pitfalls

- **Expo CLI version mismatch — use local `./node_modules/.bin/expo`:**** The globally cached `npx expo` may resolve to a DIFFERENT SDK version than your project's installed packages (e.g. global v56 CLI with SDK 54 packages). This causes the Metro bundler to configure module resolution paths for the wrong React Native version, leading to cryptic errors like **"Unable to resolve module virtualization list"**. Fix: run `./node_modules/.bin/expo start` directly from the project directory — this guarantees the CLI matches the installed packages. Verify with `./node_modules/.bin/expo --version`.
- **"Unable to resolve module virtualization list":** This error is a symptom of Metro being configured for the wrong RN version. The module `@react-native/virtualized-lists` is bundled inside `react-native` itself, and its internal path layout differs between RN versions. When the global expo CLI (higher SDK) starts Metro, it sets up module resolution paths for its own RN version. **Diagnosis:** Check `npm ls @react-native/virtualized-lists` — if the package IS present but Metro can't find it, it's a CLI version mismatch. **Fix:** Use `./node_modules/.bin/expo start` instead of `npx expo start`. If that doesn't help, align all package versions to what the CLI expects (see the "expected version" warnings in the server output).
- **Expo point release version drift:** Within the same SDK major version (e.g. "SDK 54"), later point releases of `expo` (e.g. 54.0.35) can expect drastically different underlying dependencies than earlier ones (e.g. 54.0.0). expo@54.0.35 expects **React 19.1.0** and **RN 0.81.5**, while expo@54.0.0 used React 18 / RN 0.76. Always check the `npx expo start` server output for "The following packages should be updated" warnings — those "expected version" strings are the AUTHORITATIVE truth for THAT specific expo version. When you see this warning, align your packages to the expected versions, not the "well-known" SDK version mapping.
- **Port conflicts:** The Hermes VM may have other services on common ports (3000, 8080, 8081). Always use `--port 8083` or higher for expo, and a unique port for the PWA HTTP server (8090+). Kill stale processes before starting.
- **Ngrok/expo tunnel:** `@expo/ngrok` downloads its own binary on first use — this hangs in non-interactive mode. Use `--lan` (for local network) or skip expo tunnel entirely and use localhost.run directly for the PWA.
- **Expo Go not showing QR:** In a headless terminal, expo's QR code rendering doesn't work (ASCII art needs a display). Use `--lan` mode and give the user the `exp://` URL directly for manual entry in Expo Go.
- **SDK version mismatches:** Expo Go on the App Store often lags behind the latest SDK by 1-3 weeks (or more). **Before going straight to PWA, try downgrading the project** (Phase 1b). Only fall back to PWA when the user confirms their Expo Go simply won't open the project even after SDK matching.
  - Expo SDK version = major version of Expo Go app
  - Current latest: SDK 56 (expo@~56.0.x, RN 0.85.x, React 19.2.x)
  - Older stable: SDK 54 (expo@^54.0.0, RN 0.76.7, React 18.3.1)
- **react-native-screens version trap:** v4.25.0+ requires `react-native >=0.82.0`. On SDK 54 (RN 0.76.7), you MUST pin `react-native-screens: "4.24.0"` (the last v4.x compatible with RN 0.76). Do NOT use 3.x — it causes `@react-navigation/bottom-tabs` peer-dep warnings and can trigger a **"Runtime not ready" invariant violation** at bundle time because expo-router's navigation layer expects the v4.x API surface.
- **@react-navigation/bottom-tabs peer-dep conflict:** v7.x declares `react-native-screens >=4.0.0`, but SDK 54 can only use react-native-screens 3.x. Resolve with `npm install --legacy-peer-deps`.
- **expo-status-bar version quirk:** There is no 54.x series in npm. Available versions jump from 3.x (3.0.9) to 55.x. For SDK 54, install `expo-status-bar@3.0.9`.
- **`npx expo` version mismatch:** The globally installed `expo` CLI may be on a newer version than the project's SDK. `npx expo install expo@~54.0.0` will fail because the global CLI enforces its own version. Use `npm install expo@54.0.35 --legacy-peer-deps` directly instead.
- **"Runtime not ready" invariant violation:** This expo-router startup error is caused by `react-native-screens` version mismatch. If using screens 3.x with `@react-navigation/bottom-tabs` v7.x (which expects v4.x), Metro bundles the tab navigator against the wrong native screen interface. **Fix:** upgrade to `react-native-screens@4.24.0` (the last v4.x compatible with RN 0.76). Clear Metro cache (`rm -rf node_modules/.cache .expo`) and restart.
- **expo-constants dual install is harmless:** On SDK 54, `expo@54.0.35` bundles its own `expo-constants@18.0.13` (internal). Your project-level `expo-constants@17.0.8` is the one expo-router uses. Two copies won't cause issues — the deduped one is what importers resolve to.
- **expo-linking must be pinned for SDK 54:** `expo-router@4.0.22` declares `expo-linking@~7.0.5` as a peer dep. Using `^7.0.0` (which resolves to 7.0.0) misses this. Always pin to `~7.0.5` explicitly.
- **No `expo install` during downgrade:** The `expo install` command resolves packages against the _global_ expo version, not the project's. During a downgrade, use raw `npm install` with explicit version pins instead.
- **Expo-router import path depth trap:** Files in `app/(tabs)/` are two directories deep from the project root (`app/` → `(tabs)/`). Relative imports from `app/(tabs)/file.tsx` to `src/` MUST use `../../src/...` NOT `../src/...`. This is the #1 cause of "Unable to resolve module X" errors in expo-router projects. The same rule applies to any nested route group directory (e.g. `app/(auth)/`, `app/(stack)/`).
- **Metro stale cache after deps change:** After changing package versions or import paths, Metro may serve stale bundles from its cache. Fix: `rm -rf node_modules/.cache .expo` before restarting `npx expo start`.
- **Verify imports methodically:** When a user reports "Unable to resolve module X":
  1. Search for the module name in `import` statements across the codebase
  2. Check the relative path depth from each importing file's location in the `app/` tree
  3. Fix ALL instances — don't stop at the first error, Metro may throw subsequent errors on the next reload
  4. Kill the Expo server, clear cache, restart — this ensures a fresh bundle build
- **react-native-worklets missing plugin:** `react-native-reanimated` v4.x depends on `react-native-worklets` for its Babel transform. If Metro fails with `[BABEL] Cannot find module 'react-native-worklets/plugin'`, run:
  ```bash
  npm install react-native-worklets --legacy-peer-deps
  ```
  Then kill the Expo server, clear cache (`rm -rf node_modules/.cache .expo`), and restart. This error only appears at bundle time, not during install.
- **`btoa()` and `atob()` not available in React Native's Hermes engine:** React Native uses Hermes as its JavaScript engine, which does NOT provide the browser-native `btoa()` (binary-to-ASCII) or `atob()` (ASCII-to-binary) functions. This is a common gotcha when making API calls that need Basic Auth (`Authorization: Basic ${btoa(key + ':')}`) or decoding base64 data.
  
  **Symptoms:** `ReferenceError: Can't find variable: btoa` on React Native (not Expo Go, which uses JSC). Expo SDK 54+ with Hermes mode will hit this.
  
  **Fix — manual Base64 encoder:**
  ```typescript
  function base64Encode(str: string): string {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=';
    let output = '';
    for (let i = 0; i < str.length; i += 3) {
      const a = str.charCodeAt(i);
      const b = i + 1 < str.length ? str.charCodeAt(i + 1) : 0;
      const c = i + 2 < str.length ? str.charCodeAt(i + 2) : 0;
      output += chars[a >> 2];
      output += chars[((a & 3) << 4) | (b >> 4)];
      output += i + 1 < str.length ? chars[((b & 15) << 2) | (c >> 6)] : '=';
      output += i + 2 < str.length ? chars[c & 63] : '=';
    }
    return output;
  }
  ```
  
  **Usage:** `const auth = base64Encode(apiKey + ':');` — works identically to `btoa()`.
  
  **Note:** Some polyfill packages like `text-encoding` or `base-64` exist but add a dependency. The inline function above is dependency-free and handles the common case (ASCII keys). Unicode/base64url variants need extra encoding.
- **Babel errors at bundle time (not install time):** Some Babel plugins are lazily resolved by Metro only when it first processes JSX/TSX. You can install all deps cleanly with no npm errors, then hit a `[BABEL] Cannot find module` error when Expo Go loads the bundle. Common culprits: `react-native-worklets/plugin` (reanimated 4.x), `@babel/plugin-*` missing because expo included them transitively. **Diagnosis:** Read the full Metro error — it shows the require stack from the failing Babel plugin down to the entry file. The fix is always an npm install of the missing module.
- **Offline data:** The PWA with mock data is for demo/preview. Live data requires the API token. Always ship with sensible mock data (e.g. 3.2kW solar, 72% battery, exporting 1.2kW) so the app looks good immediately.
- **Pull-to-refresh on PWA:** Use touch events (`touchstart`/`touchend` with Y-delta > 100px) since the PWA doesn't have React Native's RefreshControl.
