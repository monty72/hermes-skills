# GitHub Code Review

Review local changes (pre-push) or open PRs on GitHub.

## 1. Review Local Changes

```bash
# Get the diff
git diff --staged          # staged changes
git diff main...HEAD       # all changes vs main
git diff main...HEAD --stat --name-only

# Check for common issues
git diff main...HEAD | grep -n "print(\|console.log\|TODO\|FIXME\|debugger"
git diff main...HEAD | grep -in "password\|secret\|api_key\|token.*=\|private_key"
git diff main...HEAD | grep -n "<<<<<<\|>>>>>>\|======="
```

## 2. Review a PR

```bash
gh pr view 123
gh pr diff 123 --name-only
gh pr checkout 123

# With curl
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/files \
  | python3 -c "import sys,json; [print(f'{f[\"status\"]:10} +{f[\"additions\"]:-4} -{f[\"deletions\"]:-4}  {f[\"filename\"]}') for f in json.load(sys.stdin)]"
```

## 3. Leave Comments

```bash
# General comment
gh pr comment 123 --body "Overall looks good."

# Inline comment
HEAD_SHA=$(gh pr view 123 --json headRefOid --jq '.headRefOid')
gh api repos/$OWNER/$REPO/pulls/123/comments --method POST \
  -f body="Use parameterized queries." -f path="src/auth.py" -f commit_id="$HEAD_SHA" -f line=45 -f side="RIGHT"

# Formal review
gh pr review 123 --approve --body "LGTM!"
gh pr review 123 --request-changes --body "See inline comments."
```

## 4. Review Checklist

- **Correctness**: Edge cases, error paths, does what it claims
- **Security**: No hardcoded secrets, SQL injection, XSS, path traversal
- **Code Quality**: Clear naming, DRY, single responsibility
- **Testing**: New code tested, happy path and errors covered
- **Performance**: No N+1, appropriate caching, no blocking in async
- **Documentation**: Public APIs documented, non-obvious logic explained
