---
name: github
description: "Complete GitHub workflow: auth, PRs, issues, repo management, code review — via gh CLI or git+curl. Use this for any GitHub interaction; sub-skills are in references/ for deep detail."
metadata: {"openclaw":{"emoji":"🐙","requires":{"bins":["gh"]},"install":[{"id":"brew","kind":"brew","formula":"gh","bins":["gh"],"label":"Install GitHub CLI (brew)"},{"id":"apt","kind":"apt","package":"gh","bins":["gh"],"label":"Install GitHub CLI (apt)"}]}}
---

# GitHub — Complete Workflow Guide

Use this umbrella skill for any GitHub interaction. For deep detail on any sub-topic, load the corresponding reference file.

## Auth Detection (used by all sub-workflows)

```bash
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  echo "AUTH_METHOD=gh"
else
  echo "AUTH_METHOD=curl"
  # Extract token from common locations
  if [ -z "$GITHUB_TOKEN" ]; then
    _env="${HERMES_HOME:-$HOME/.hermes}/.env"
    [ -f "$_env" ] && grep -q "^GITHUB_TOKEN=" "$_env" && export GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" "$_env" | head -1 | cut -d= -f2 | tr -d '\n\r')
    [ -z "$GITHUB_TOKEN" ] && grep -q "github.com" ~/.git-credentials 2>/dev/null && \
      export GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
  fi
fi

# Extract owner/repo from git remote
REMOTE_URL=$(git remote get-url origin 2>/dev/null)
if [ -n "$REMOTE_URL" ]; then
  OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
  OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
  REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
fi

# Get current GitHub username
if [ "$AUTH" = "gh" ]; then
  GH_USER=$(gh api user --jq '.login' 2>/dev/null)
else
  GH_USER=$(curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user | python3 -c "import sys,json; print(json.load(sys.stdin)['login'])" 2>/dev/null)
fi
```

## 1. Authentication

See `references/github-auth.md` for details. Quick start:

```bash
# HTTPS with token (no gh needed)
git config --global credential.helper store
# Then git push — username=<user>, password=<PAT>

# SSH key
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub  # Add to https://github.com/settings/keys
```

## 2. Pull Request Workflow

See `references/github-pr-workflow.md` for full lifecycle. Summary:

```bash
# Create branch, commit, push
git checkout -b feat/my-feature
git add -A && git commit -m "feat: description"
git push -u origin HEAD

# Create PR
gh pr create --title "feat: description" --body "Closes #42"

# Monitor CI
gh pr checks 55 --watch
gh run view <RUN_ID> --log-failed

# Merge
gh pr merge --squash --delete-branch
```

## 3. Issues

See `references/github-issues.md` for full CRUD. Summary:

```bash
# Create
gh issue create --title "Bug: login redirect" --label "bug" --assignee @me

# List/search
gh issue list --state open --label "bug"
gh issue view 42

# Triage (add labels, assign, comment)
gh issue edit 42 --add-label "priority:high" --add-assignee username
gh issue close 42
```

## 4. Code Review

See `references/github-code-review.md` for full workflow.

```bash
# Review local changes
git diff main...HEAD --stat
git diff main...HEAD | grep -n "TODO\|FIXME\|console.log\|debugger"

# Review a PR
gh pr checkout 123
gh pr review 123 --approve --body "LGTM"
gh pr review 123 --request-changes --body "See inline."

# Inline comments via API
gh api repos/$OWNER/$REPO/pulls/123/comments --method POST \
  -f body="suggestion" -f path="src/auth.py" -f commit_id="$SHA" -f line=45 -f side="RIGHT"
```

## 5. Repository Management

See `references/github-repo-management.md` for full detail. Summary:

```bash
gh repo create my-project --public --clone
gh repo fork owner/repo --clone
gh repo edit --description "..." --visibility public
gh release create v1.0.0 --generate-notes
gh secret set API_KEY --body "value"
```

## 6. Pre-Commit Verification

See `references/requesting-code-review.md` for the independent reviewer pipeline.

## Quick Reference

| Action | gh | git + curl |
|--------|-----|-----------|
| Auth check | `gh auth status` | Check GITHUB_TOKEN + git-credentials |
| List PRs | `gh pr list` | `curl GET /repos/o/r/pulls` |
| Create issue | `gh issue create` | `curl POST /repos/o/r/issues` |
| Review PR | `gh pr review N` | `curl POST /repos/o/r/pulls/N/reviews` |
| Clone repo | `gh repo clone o/r` | `git clone https://github.com/o/r.git` |
| Create release | `gh release create v1.0` | `curl POST /repos/o/r/releases` |
| Set secrets | `gh secret set KEY` | `curl PUT .../actions/secrets/KEY` (+ encryption) |
| View repo | `gh repo view o/r` | `curl GET /repos/o/r` |
