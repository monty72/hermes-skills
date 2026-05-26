# Astro + GitHub Actions + Vercel — Full Stack Setup

This reference documents the pattern for scaffolding a modern Astro project with CI/CD pipeline and Vercel deployment, as used for the hermes-dev project.

## When to use this

- User wants "modern CI/CD" + "a framework for web development"
- Project is content-heavy (resource hubs, dashboards, landing pages, review sites)
- Recommend Astro over Next.js/SvelteKit for content-first workloads

## Scaffold Sequence

### 1. Create the project directory and git repo

```bash
mkdir -p ~/project-name && cd ~/project-name && git init
git remote add origin https://github.com/username/project-name.git
```

### 2. Write package.json manually

Use `npx create-astro` if the environment supports interactive prompts. Otherwise write package.json manually with correct dependency versions:

```json
{
  "name": "project-name",
  "private": true,
  "type": "module",
  "version": "0.1.0",
  "scripts": {
    "dev": "astro dev",
    "build": "astro build",
    "preview": "astro preview",
    "astro": "astro",
    "lint": "eslint src/",
    "check": "astro check"
  },
  "dependencies": {
    "astro": "^5.0.0"
  },
  "devDependencies": {
    "@astrojs/check": "^0.9.0",
    "@astrojs/react": "^4.0.0",
    "@astrojs/tailwind": "^6.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "typescript": "^5.7.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "tailwindcss": "^4.0.0",
    "@tailwindcss/vite": "^4.0.0",
    "eslint": "^9.0.0",
    "prettier": "^3.0.0",
    "prettier-plugin-astro": "^0.14.0"
  }
}
```

### 3. Config files

**astro.config.mjs** — Tailwind v4 + React integration:
```js
import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";
import react from "@astrojs/react";

export default defineConfig({
  site: "https://montygroup.uk",
  output: "static",
  vite: {
    plugins: [tailwindcss()],
  },
  integrations: [react()],
});
```

**tsconfig.json** — strict mode with path aliases:
```json
{
  "extends": "astro/tsconfigs/strict",
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  }
}
```

### 4. Layout and styling

**src/layouts/Layout.astro** — dark theme, nav bar, footer:
```astro
---
export interface Props {
  title: string;
  description?: string;
}
const { title, description = "Dev hub" } = Astro.props;
---
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content={description} />
    <title>{title}</title>
  </head>
  <body class="bg-zinc-950 text-zinc-100 min-h-screen">
    <nav class="border-b border-zinc-800 ..."><!-- sticky nav --></nav>
    <main><slot /></main>
    <footer class="border-t border-zinc-800 ..."><!-- footer --></footer>
  </body>
</html>
```

**src/styles/global.css** — Tailwind v4 import:
```css
@import "tailwindcss";
@theme {
  --color-emerald-400: #34d399;
  --color-zinc-950: #09090b;
  /* etc */
}
```

### 5. Create pages

Flat structure under `src/pages/` — Astro uses file-based routing:

```
src/pages/
  index.astro           → /
  mission-control.astro → /mission-control
  energy.astro          → /energy
  childminding.astro    → /childminding
  bots.astro            → /bots
```

Each page imports Layout and passes metadata:
```astro
---
import Layout from "@/layouts/Layout.astro";
---
<Layout title="Page Title">
  <!-- content -->
</Layout>
```

### 6. GitHub Actions CI

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
      - run: npm ci
      - run: npm run build
```

### 7. Push and deploy

1. Create the GitHub repo (browser or API)
2. Push: `git push -u origin main`
3. Connect to Vercel: `vercel link` (interactive, browser-based auth)
4. Vercel auto-detects Astro and sets up preview/production deploys

## Package dependency notes

- `@astrojs/tailwind` v6 requires `tailwindcss` v4
- Tailwind v4 uses `@import "tailwindcss"` (NOT `@tailwind` directives)
- `@tailwindcss/vite` plugin goes in `vite.plugins` in astro.config.mjs
- `--legacy-peer-deps` may be needed for dependency resolution if using `@astrojs/tailwind` v6 with astro v5
- `npm install --legacy-peer-deps` is safe for resolving peer dep conflicts in this stack

## Known pitfalls

- **create-astro interactive prompts** — if the environment can't do interactive input, scaffold manually
- **`npm create astro@latest` generates random placeholder names** like `fumbling-field` in package.json. Always rename to match the project: `"name": "my-project"`. The name doesn't affect routing but affects Vercel project detection and npm package publishing.
- **Vercel CLI auth** — requires a Vercel access token for non-interactive usage. Without one, `vercel link` opens a browser. Generate tokens at https://vercel.com/account/tokens (Full scope). Usage: `vercel link --token $VERCEL_TOKEN` or `VERCEL_TOKEN=$token vercel --prod`.
- **GitHub repo must exist before push** — create via browser at github.com/new, or use gh API with a token
- **`git init` creates 'master' branch** on older git versions. If remote expects 'main', fix with `git branch -m master main` before pushing.
- **`git commit` fails with "Author identity unknown"** when no global `user.email`/`user.name` is set. Fix per-repo: `git config user.email "you@example.com"` and `git config user.name "Your Name"`. This avoids changing global config.
- **Token-embedded remote URL** — `git remote add origin https://$USER:$TOKEN@github.com/$USER/repo.git` embeds the PAT in git config. Use a fine-grained PAT scoped only to the repos you need.
- **`npm run dev` starts on :4321** (not :3000 like Next.js)
- **Astro builds to `dist/`** (not `.next/` like Next.js)
- **No API routes in static output** — for backend data (Tesla API, etc.), keep the Flask server running on :8000 and fetch from client-side JS
