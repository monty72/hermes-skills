# GitHub Issues Management

Create, search, triage, and manage GitHub issues. Each section shows `gh` first, then curl fallback.

## 1. Viewing Issues

```bash
# gh
gh issue list
gh issue list --state open --label "bug" --assignee @me
gh issue list --search "auth error" --state all
gh issue view 42

# curl
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/issues?state=open&per_page=20" \
  | python3 -c "import sys,json; [print(f'#{i[\"number\"]:5}  {i[\"state\"]:6}  {i[\"title\"]}') for i in json.load(sys.stdin)]"

# Search
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/search/issues?q=bug+repo:$OWNER/$REPO"
```

## 2. Creating Issues

```bash
gh issue create --title "Bug: login redirect" --body "## Description\n..." --label "bug,backend" --assignee username

# curl
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/issues \
  -d '{"title":"Bug: ...","body":"## Description","labels":["bug","backend"],"assignees":["username"]}'
```

## 3. Managing Issues

```bash
# Labels
gh issue edit 42 --add-label "priority:high,bug" --remove-label "needs-triage"
curl -s -X POST .../issues/42/labels -d '{"labels":["priority:high","bug"]}'

# Assignment
gh issue edit 42 --add-assignee @me
curl -s -X POST .../issues/42/assignees -d '{"assignees":["username"]}'

# Commenting
gh issue comment 42 --body "Investigating..."
curl -s -X POST .../issues/42/comments -d '{"body":"Investigating..."}'

# Close/Reopen
gh issue close 42 --reason "completed"
gh issue reopen 42
curl -s -X PATCH .../issues/42 -d '{"state":"closed","state_reason":"completed"}'
```

## 4. Issue Triage Workflow

1. List untriaged: `gh issue list --label "needs-triage" --state open`
2. Read and categorize each issue
3. Apply labels/priority
4. Assign if owner is clear
5. Comment with triage notes

## 5. Bulk Operations

```bash
gh issue list --label "wontfix" --json number --jq '.[].number' | xargs -I {} gh issue close {} --reason "not planned"
```

## Quick Reference

| Action | gh | curl |
|--------|-----|------|
| List | `gh issue list` | `GET /repos/o/r/issues` |
| View | `gh issue view N` | `GET /repos/o/r/issues/N` |
| Create | `gh issue create --title "..."` | `POST /repos/o/r/issues` |
| Labels | `gh issue edit N --add-label ...` | `POST .../issues/N/labels` |
| Assign | `gh issue edit N --add-assignee ...` | `POST .../issues/N/assignees` |
| Comment | `gh issue comment N --body ...` | `POST .../issues/N/comments` |
| Close | `gh issue close N` | `PATCH .../issues/N` |
