# GitHub Pull Request Workflow

Complete lifecycle: branch → commit → push → create PR → monitor CI → merge.

## Prerequisites

```bash
# Auth detection
if command -v gh &>/dev/null && gh auth status &>/dev/null; then AUTH="gh"; else AUTH="git"; fi
REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
```

## 1. Branch Creation

```bash
git fetch origin
git checkout main && git pull origin main
git checkout -b feat/description
```

Branch naming: `feat/`, `fix/`, `refactor/`, `docs/`, `ci/`

## 2. Commits

```bash
git add src/auth.py tests/test_auth.py
git commit -m "feat: add JWT authentication"
```

Format: `type(scope): short description` — types: feat, fix, refactor, docs, test, ci, chore, perf

## 3. Push & Create PR

```bash
git push -u origin HEAD

# With gh:
gh pr create --title "feat: description" --body "## Summary\nCloses #42"

# With curl:
BRANCH=$(git branch --show-current)
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls \
  -d "{\"title\":\"feat: description\",\"head\":\"$BRANCH\",\"base\":\"main\"}"
```

## 4. Monitor CI

```bash
# With gh
gh pr checks --watch

# With curl
SHA=$(git rev-parse HEAD)
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/status
```

## 5. Auto-Fix CI Failures

1. Get failure details: `gh run list --branch $(git branch --show-current)` then `gh run view <ID> --log-failed`
2. Fix code with file tools
3. `git add && git commit -m "fix: ..." && git push`
4. Re-check CI. Repeat up to 3 attempts.

## 6. Merge

```bash
# With gh
gh pr merge --squash --delete-branch
gh pr merge --auto --squash --delete-branch  # Auto-merge when CI passes

# With curl
curl -s -X PUT -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/merge \
  -d "{\"merge_method\":\"squash\"}"
```

## 7. Complete Example

```bash
git checkout main && git pull origin main
git checkout -b fix/login-redirect
# (make changes)
git add src/auth/login.py
git commit -m "fix: correct redirect URL after login"
git push -u origin HEAD
gh pr create --title "fix: login redirect" --body "Fixes #42"
gh pr checks --watch
gh pr merge --squash --delete-branch
```
