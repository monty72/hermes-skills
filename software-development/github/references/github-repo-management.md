# GitHub Repository Management

Create, clone, fork, configure, and manage repositories.

## 1. Cloning

```bash
git clone https://github.com/owner/repo-name.git
gh repo clone owner/repo-name
git clone --depth 1 https://github.com/owner/repo-name.git  # shallow
```

## 2. Creating Repositories

```bash
# With gh
gh repo create my-project --public --clone
gh repo create my-org/my-project --public --clone

# With curl
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user/repos \
  -d '{"name":"my-project","description":"...","private":false,"auto_init":true}'

# Template
gh repo create my-app --template owner/template-repo --public --clone
```

Push existing project:
```bash
cd /path/to/project
git init && git branch -m main
git add -A && git commit -m "Initial commit"
git remote add origin https://$GH_USER:$GITHUB_TOKEN@github.com/$GH_USER/my-project.git
git push -u origin main
```

## 3. Forking

```bash
gh repo fork owner/repo-name --clone

# Manual
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/repos/owner/repo-name/forks
git clone https://github.com/$GH_USER/repo-name.git
git remote add upstream https://github.com/owner/repo-name.git
```

Keep fork in sync:
```bash
git fetch upstream && git checkout main && git merge upstream/main && git push origin main
```

## 4. Repository Info

```bash
gh repo view owner/repo-name
gh repo list --limit 20

curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/repos/$OWNER/$REPO
```

## 5. Settings

```bash
gh repo edit --description "..." --visibility public --default-branch main
gh repo edit --enable-wiki=false --add-topic "python,automation"

curl -s -X PATCH -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO -d '{"private":false,"has_wiki":false}'
```

## 6. Secrets

```bash
gh secret set API_KEY --body "value"
gh secret list
gh secret delete API_KEY
```

## 7. Releases

```bash
# Create
gh release create v1.0.0 --title "v1.0.0" --generate-notes
gh release create v1.0.0 ./dist/binary --title "v1.0.0"

# List and download
gh release list
gh release download v1.0.0 --dir ./downloads

# With curl
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/releases \
  -d '{"tag_name":"v1.0.0","name":"v1.0.0","draft":false,"prerelease":false}'
```

## 8. Branch Protection

```bash
curl -s -X PUT -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/branches/main/protection \
  -d '{"required_status_checks":{"strict":true,"contexts":["ci/test"]},"required_pull_request_reviews":{"required_approving_review_count":1}}'
```

## 9. Gists

```bash
gh gist create script.py --public --desc "Useful script"
gh gist list

curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/gists -d '{"description":"...","public":true,"files":{"script.py":{"content":"hello"}}}'
```
