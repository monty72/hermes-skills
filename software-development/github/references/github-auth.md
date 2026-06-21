# GitHub Authentication Setup

Full authentication setup for GitHub. Covers two paths:

- **`git` (always available)** — HTTPS personal access tokens or SSH keys
- **`gh` CLI (if installed)** — richer GitHub API access with a simpler auth flow

## Detection Flow

```bash
git --version
gh --version 2>/dev/null || echo "gh not installed"
gh auth status 2>/dev/null || echo "gh not authenticated"
git config --global credential.helper 2>/dev/null || echo "no git credential helper"
```

**Decision tree:**
1. `gh auth status` shows authenticated → good, use `gh` for everything
2. `gh` installed but not authenticated → use "gh auth" method
3. `gh` not installed → use "git-only" method

## Method 1: Git-Only (No gh, No sudo)

### Option A: HTTPS with Personal Access Token (Recommended)

1. Generate token at https://github.com/settings/tokens — scopes: `repo`, `workflow`, `read:org`
2. Configure and verify:
```bash
git config --global credential.helper store
git ls-remote https://github.com/<username>/<any-repo>.git
# Enter username + token (NOT GitHub password)
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

Alternative: Credential helper with timeout:
```bash
git config --global credential.helper 'cache --timeout=28800'
```

Per-repo embedded token (convenient but less secure):
```bash
git remote set-url origin https://<user>:<token>@github.com/<owner>/<repo>.git
```

### Option B: SSH Key Authentication

```bash
# Check for existing keys
ls -la ~/.ssh/id_*.pub 2>/dev/null || echo "No SSH keys found"

# Generate a key
ssh-keygen -t ed25519 -C "your@email.com" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub  # Add to https://github.com/settings/keys

# Test and configure
ssh -T git@github.com
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

## Method 2: gh CLI Authentication

```bash
# Interactive (desktop)
gh auth login

# Headless token login
echo "<TOKEN>" | gh auth login --with-token
gh auth setup-git

# Verify
gh auth status
```

## API Access Without gh

```bash
export GITHUB_TOKEN="<token>"
curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `git push` asks for password | Use personal access token, not password |
| `Permission denied` | Token lacks `repo` scope |
| `Authentication failed` | Stale credentials — run `git credential reject` then re-auth |
| SSH port 22 blocked | Add `Host github.com` with `Port 443` and `Hostname ssh.github.com` to `~/.ssh/config` |
| Multiple accounts | SSH keys with different host aliases in `~/.ssh/config` |
