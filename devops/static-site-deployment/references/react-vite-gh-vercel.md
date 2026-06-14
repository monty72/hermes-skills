# Vite + React → GitHub → Vercel Workflow

End-to-end recipe for scaffolding a Vite+React SPA, pushing to GitHub, and deploying to Vercel — all without the `gh` CLI, using the hermes-vault credential helper for auth.

## Prerequisites

- `GITHUB_TOKEN` and `VERCEL_TOKEN` in hermes-vault
- Git credential helper configured: `git config --global credential.helper` returns `!~/.local/bin/git-credential-vault`
- Node.js + npm

## Step 1: Scaffold + Build

```bash
# Create the project
npm create vite@latest my-project -- --template react
cd my-project
npm install

# Develop locally, build for production
npm run build  # → dist/
```

## Step 2: Create GitHub Repo (via API)

```bash
source ~/.hermes/.env.local 2>/dev/null
export PATH="$HOME/.local/bin:$PATH"
TOKEN=$(hermes-vault get GITHUB_TOKEN)

# Get your username from the token
GH_USER=$(curl -s -H "Authorization: bearer $TOKEN" \
  https://api.github.com/user | python3 -c "import sys,json; print(json.load(sys.stdin)['login'])")

# Create repo (public, no auto-init)
curl -s -X POST -H "Authorization: bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/user/repos \
  -d "{\"name\":\"my-project\",\"description\":\"Project description\",\"private\":false,\"auto_init\":false}"
```

The repo is now at `https://github.com/$GH_USER/my-project`.

## Step 3: Git Init + Push

```bash
cd /path/to/my-project

# Set per-repo git identity (avoids changing global)
git config user.email "you@example.com"
git config user.name "Your Name"

# Init
git init && git branch -m main
git add -A && git commit -m "Initial commit"

# Add clean remote (no token in URL — vault credential helper supplies auth)
git remote add origin https://github.com/$GH_USER/my-project.git
git push -u origin main
```

## Step 4: Vercel Deploy

```bash
source ~/.hermes/.env.local 2>/dev/null
export PATH="$HOME/.local/bin:$PATH"
VERCEL_TOKEN=$(hermes-vault get VERCEL_TOKEN)

cd /path/to/my-project

# Link to Vercel (creates .vercel/project.json, connects to GitHub repo)
npx vercel link --token "$VERCEL_TOKEN" --yes --cwd .

# Deploy to production
npx vercel deploy --prod --token "$VERCEL_TOKEN" --yes

# Output:
#   Production  https://my-project.vercel.app
```

After the first deploy, Vercel auto-detects the GitHub repo and sets up auto-deploy on `git push` to `main`. No GitHub Actions workflow file needed.

## Step 5: Verify

```bash
curl -sI https://my-project.vercel.app | head -5
# Should return 200 OK
```

## Pitfalls

- **No `npx` version pinning**: Using `npx vercel` runs the locally installed version, not a global. If you get CLI errors, check `npm ls vercel` in the project dir.
- **Vercel link before git push**: `vercel link` will try to connect to the GitHub repo. The repo must already exist on GitHub (Step 2) and have at least one commit pushed (Step 3) for the integration to work. If the repo is empty, `vercel link` may appear to succeed but the auto-deploy hook won't trigger.
- **Token freshness**: `hermes-vault` stores the token, but if the token was rotated, `vercel link` fails with "The specified token is not valid". Re-store with `hermes-vault set VERCEL_TOKEN "new-token"`.
- **Build fails on Vercel**: Check the Vercel dashboard build logs at `https://vercel.com/$USER/my-project/deployments`. Common issues: missing build command detection (Vite should be auto-detected), or missing `npm install` (Vercel auto-installs).
- **`vercel link` output says "Connecting GitHub repository" then shows "Connected" even if the repo is empty** — the agent thinks it succeeded. Always verify by running `npx vercel deploy --prod` after link; the deploy will fail if the repo connection didn't actually establish.
