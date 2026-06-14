# Expo SDK Downgrade Debugging Recipes

## Session: SDK 56 → 54 Downgrade (Powerwall App)

### Problem
Project was built on Expo SDK 56 (expo@~56.0.11, RN 0.85.3, React 19.2.3). User's Expo Go on iPhone only supported SDK 54.

### Step-by-step

1. **Killed running expo server** (port 8083)
2. **Wiped node_modules + lock**
3. **Wrote new package.json** with SDK 54 versions
4. **Installed with `--legacy-peer-deps`** — required because @react-navigation/bottom-tabs v7.x peer-dep on react-native-screens >=4.0.0 conflicts with RN 0.76's constraint

### Errors Encountered & Fixes

**Error 1: "Unable to resolve module theme"**
- Cause: expo-router app directory structure. Files at `app/(tabs)/file.tsx` are 2 levels deep from root.
- Imports used `'../src/theme'` which resolves to `app/src/theme` — doesn't exist.
- Fix: Change to `'../../src/theme'` — resolves correctly to `src/theme`.
- All sibling imports from the same directory also broken: EnergyFlow, MetricCard, api, types.

**Error 2: "Module expo-linking not available"**
- Cause: `expo-linking` was in the peer deps of expo-router but never explicitly installed.
- Fix: `npm install expo-linking@~7.0.5 --legacy-peer-deps`

**Error 3: "Runtime not ready" invariant violation**
- Cause: `react-native-screens@3.37.0` installed. @react-navigation/bottom-tabs v7.x expects screens v4.x API surface. At bundle time, expo-router's navigation layer blows up.
- Fix: Upgrade to `react-native-screens@4.24.0` (last v4.x compatible with RN 0.76; 4.25.0+ requires RN >=0.82).
- Also fixes the npm peer-dep warnings about "invalid".

**Error 4: "Unable to resolve module virtualization list"** (Session 2 — SDK 54 further debugging)
- Cause: The global `npx expo` CLI was SDK 56, but the installed packages were SDK 54. Metro configured module resolution paths for RN 0.81 (SDK 56), but the project had RN 0.76 (SDK 54). The module `@react-native/virtualized-lists` is bundled inside `react-native` itself, and its internal path layout differs between RN 0.76 and 0.81.
- **Diagnosis:** The Expo server showed "The following packages should be updated" warnings with expected versions like `react-native: 0.81.5`, `@expo/metro-runtime: ~6.1.2`. These are the versions the installed `expo@54.0.35` expects.
- Fix (path A — match CLI to packages): Use `./node_modules/.bin/expo start` instead of `npx expo start` to guarantee the CLI matches the installed packages. Verify CLI version with `./node_modules/.bin/expo --version`.
- Fix (path B — match packages to expected versions): Update package.json to the versions shown in the warnings:
  - react-native: 0.81.5
  - react: 19.1.0, react-dom: 19.1.0
  - @expo/metro-runtime: ~6.1.2
  - expo-constants: ~18.0.13, expo-linking: ~8.0.12
  - expo-router: ~6.0.24
  - expo-linear-gradient: ~15.0.8
  - react-native-reanimated: ~4.1.1
  - react-native-safe-area-context: ~5.6.0
  - react-native-screens: ~4.16.0 (compatible range)
  - react-native-svg: 15.12.1
  - react-native-web: ^0.21.0
  - typescript: ~5.9.2
  - @types/react: ~19.1.10

**Key Discovery: Expo Point Release Drift**
The package `expo@54.0.35` (the latest 54.x point release) expects React 19 and RN 0.81, NOT React 18 / RN 0.76. Earlier 54.x releases (like 54.0.0) used the older stack. The SDK major version number alone is NOT sufficient to determine which React/RN versions are needed — always check `npx expo start` output for "expected version" warnings.

**CLI Version Mismatch**
The global `npx expo` command resolved to the SDK 56 CLI, which then configured Metro with RN 0.81 paths. The project's `./node_modules/.bin/expo` was SDK 54.0.25 (matching the installed packages). Always verify with `./node_modules/.bin/expo --version` and use the local binary for `expo start`.

### Version Boundaries Discovered

| Package | Last compatible with RN 0.76 (SDK 54) | Requires RN >=0.82 (SDK 56) |
|---|---|---|
| react-native-screens | 4.24.0 | 4.25.0+ |
| react-native-reanimated | 3.19.x | 4.0.0+ |

### Package Dedup Verification

After a clean install, verify with `npm ls <pkg>` — no `invalid:` labels allowed:

```bash
# Clean indicator: single copy, all deduped
npm ls react-native-screens expo-constants expo-linking

# Expected (SDK 54):
# react-native-screens@4.24.0 deduped  ← no "invalid"
# expo-constants@17.0.8 deduped        ← project-level
# expo-linking@7.0.5 deduped
```

Note: `npm ls` may show a secondary `expo-constants@18.0.13` under `expo@54.0.35 → expo-asset` — this is a bundled internal copy, harmless.

### Server Restart

Always kill the old server process before restarting after dep changes. Metro serves stale bundles from `node_modules/.cache/` and `.expo/`. Clear both:

```bash
rm -rf node_modules/.cache .expo
npx expo start --lan --port 8083
```
