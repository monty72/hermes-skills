# Expo-Router Import Path Debugging

## Symptom

Expo Go shows: `Unable to resolve module theme` (or any other local module)
Metro bundler throws a module resolution error with the module path shown.

## Root Cause

Relative import paths in expo-router's nested directory structure are one level deeper than they appear.

### The Directory Structure

```
project-root/
├── app/
│   ├── _layout.tsx          ← depth 1 from root
│   └── (tabs)/
│       ├── _layout.tsx      ← depth 2 from root
│       ├── index.tsx        ← depth 2 from root
│       ├── battery.tsx      ← depth 2 from root
│       └── settings.tsx     ← depth 2 from root
└── src/
    ├── theme.ts
    ├── api.ts
    ├── types.ts
    └── components/
        ├── EnergyFlow.tsx
        └── MetricCard.tsx
```

### Correct vs Wrong Imports

From `app/(tabs)/index.tsx` (depth 2):

| Target | Wrong | Correct |
|---|---|---|
| `src/theme` | `'../src/theme'` ❌ resolves to `app/src/theme` | `'../../src/theme'` ✅ |
| `src/api` | `'../src/api'` ❌ | `'../../src/api'` ✅ |
| `src/types` | `'../src/types'` ❌ | `'../../src/types'` ✅ |
| `src/components/EnergyFlow` | `'../src/components/EnergyFlow'` ❌ | `'../../src/components/EnergyFlow'` ✅ |

From `app/(tabs)/_layout.tsx` (depth 2):

| Target | Wrong | Correct |
|---|---|---|
| `src/theme` | `'../src/theme'` ❌ | `'../../src/theme'` ✅ |

From `src/components/EnergyFlow.tsx` (depth 1 inside `src/`):

| Target | Correct |
|---|---|
| `src/theme` | `'../theme'` ✅ (goes up to `src/` root) |

### Why It's Confusing

- In a flat Vite/CRA project, `../src/theme` from a file in `src/` subdirectory would be correct
- Expo-router adds `app/` as the first directory layer, and route groups like `(tabs)` add another
- The mental model: `app/` is NOT the project root — it's the route directory. `src/` is a sibling of `app/`, not a child

### Fixing Process

```bash
# 1. Find ALL bad imports
grep -rn "from '../src/" app/ --include='*.tsx' --include='*.ts'

# 2. Fix each file — replace '../src/' with '../../src/'
# (manual per-file with patch tool, or use sed for bulk)

# 3. Clear Metro cache
rm -rf node_modules/.cache .expo

# 4. Kill and restart Expo
# Kill existing server, then:
npx expo start --lan --port 8083

# 5. Test by reloading in Expo Go
```

## Session Context

This occurred during an Expo SDK 56→54 downgrade of a Powerwall monitoring app. The app was originally scaffolded with `../src/` import paths that worked at some point but broke after the dependency reset + cache clear. The imports had been wrong all along — they only appeared to work because Metro had cached the old module graph from before the SDK downgrade.
