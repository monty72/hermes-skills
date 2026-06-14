# Expo SDK Version Drift

## The Problem

Expo SDK version numbers are **not stable** — the underlying dependency chain can change significantly between point releases of the `expo` package within the same SDK major version.

## Concrete Example: SDK 54

| expo version | react-native | react | Notes |
|---|---|---|---|
| 54.0.0 (early) | 0.76.x | 18.x | "Traditional" SDK 54 |
| 54.0.35 (latest) | **0.81.5** | **19.1.0** | Same SDK number, completely different stack |

Both are published under `expo@^54.0.0`. If you `npm install expo@^54.0.0` today (June 2026), you get 54.0.35, which expects RN 0.81 / React 19 — exactly what SDK 56 used to be.

## Root Cause

After the Expo SDK 56 release, the project **renamed SDK 56 back to SDK 54** while bumping internal package versions. The SDK number 54 was reused for what was previously SDK 56's dependency chain. This means:
- "SDK 54" now means two different things depending on when you installed it
- The first stable SDK 54 (early 2025) = RN 0.76 / React 18
- The latest SDK 54 (mid 2026) = RN 0.81 / React 19

## How to Detect

When starting the Expo server, the output shows:
```
The following packages should be updated for best compatibility with the installed expo version:
  react@18.3.1 - expected version: 19.1.0
  react-native@0.76.7 - expected version: 0.81.5
```

These "expected version" strings are the **authoritative truth** for that specific `expo` version. **Trust them** — they tell you exactly what packages expo expects, regardless of what the SDK number "should" mean.

## How to Resolve

Two approaches:

### Approach A: Match CLI to Packages (when you want to keep the old stack)

Use the project's local `./node_modules/.bin/expo` instead of the global `npx expo`:
```bash
./node_modules/.bin/expo start --lan --port 8083
# Verify: should show ./node_modules/.bin/expo --version = 54.0.x 
```

This lets you keep React 18 / RN 0.76 while running the correct CLI version. The local `@expo/cli` is installed as a dependency of `expo` itself and matches the project's SDK version.

### Approach B: Align Packages to CLI expectations (when you want the latest stack)

Update package.json to match the "expected version" warnings:
```bash
# Install the versions expo@54.0.35 expects
npm install react@19.1.0 react-dom@19.1.0 react-native@0.81.5 \
  @expo/metro-runtime@~6.1.2 expo-constants@~18.0.13 expo-linking@~8.0.12 \
  expo-router@~6.0.24 react-native-reanimated@~4.1.1 \
  react-native-safe-area-context@~5.6.0 react-native-screens@~4.16.0 \
  react-native-svg@15.12.1 react-native-web@^0.21.0 \
  --legacy-peer-deps
```

## Key Lesson

**Never assume the SDK version number defines the React/RN baseline.** Always check the actual server output for the "expected version" warnings. Those are the single source of truth for what your installed `expo` package expects.
