# Debugging Vercel Domain-to-Project Mismatch

## Symptoms

- GitHub Actions deploy succeeds (`Completed in 15s`), `montygroup-astro.vercel.app` shows latest content
- Custom domain `montygroup.uk` shows old/stale content (age: 1000+ seconds via `age:` header)
- Vercel project has `autoAssignCustomDomains: True`
- Deployments show `target=production` and `aliasAssigned=timestamp` but `aliases=[]`

## Root Cause

The CI workflow creates/links to one Vercel project (e.g. `montygroup-astro` with `prj_XdOIMg...`), but the custom domain was added to a DIFFERENT Vercel project (e.g. `dev-site` with `prj_zp4v7xk...`). The domain alias system only connects domains to deployments within the same project.

## Step-by-Step Diagnosis

### 1. List all Vercel projects

```bash
curl -sH "Authorization: Bearer $VTOKEN" \
  "https://api.vercel.com/v9/projects?teamId=$TEAM_ID" | \
  python3 -c "
import sys, json
for p in json.load(sys.stdin).get('projects', []):
    link = p.get('link', {}) or {}
    print(f\"{p['name']}: id={p['id'][:25]} git={link.get('type','none')} repo={link.get('repo','')}\")
"
```

### 2. Check which deployment aliases are set for each project

```bash
# For each project, check its aliases
for PID in <project-id-1> <project-id-2>; do
  echo "=== Project: $PID ==="
  curl -sH "Authorization: Bearer $VTOKEN" \
    "https://api.vercel.com/v4/aliases?projectId=$PID&teamId=$TEAM_ID&limit=20" | \
    python3 -c "
import sys, json
for a in json.load(sys.stdin).get('aliases', []):
    print(f\"  {a['alias']} -> {a['deploymentId']}\")
"
done
```

### 3. Read the CI deploy log

From the GitHub Actions run, check the `Deploy to Vercel` step output:
- `Linked monty72s-projects/<project-name>` tells you which project the CI deploys to
- `Aliased https://<something>.vercel.app` tells you the preview domain, **not** necessarily the custom domain

If the linked project name doesn't match the project that owns `montygroup.uk` in step 2, you've found the mismatch.

### 4. Check the project owning the domain

```bash
# Which project owns montygroup.uk?
curl -sH "Authorization: Bearer $VTOKEN" \
  "https://api.vercel.com/v9/projects/$PID/domains/montygroup.uk?teamId=$TEAM_ID" | \
  python3 -c "import sys, json; d=json.load(sys.stdin); print(f'Project: {d.get(\"projectId\",\"NOT FOUND\")}')"
```

## Fix

### Move domain to the CI project

```bash
# 1. Remove domain from wrong project
curl -sX DELETE -H "Authorization: Bearer $VTOKEN" \
  "https://api.vercel.com/v9/projects/prj_WRONG_PROJECT/domains/montygroup.uk?teamId=$TEAM_ID"

# 2. Add domain to correct project
curl -sX POST -H "Authorization: Bearer $VTOKEN" -H "Content-Type: application/json" \
  "https://api.vercel.com/v9/projects/prj_RIGHT_PROJECT/domains?teamId=$TEAM_ID" \
  -d '{"name":"montygroup.uk"}'

# 3. Push to trigger CI → new deploy aliases montygroup.uk
git commit --allow-empty -m "fix: move montygroup.uk to CI project"
git push origin main
```

### Verify the fix

```bash
# Check the alias chain
curl -sH "Authorization: Bearer $VTOKEN" \
  "https://api.vercel.com/v4/aliases?projectId=$RIGHT_PROJECT&teamId=$TEAM_ID&limit=5" | \
  python3 -c "import sys, json; [print(f\"{a['alias']} -> dep={a['deploymentId'][:20]}\") for a in json.load(sys.stdin).get('aliases',[])]"

# Verify fresh content via custom domain
curl -sI "https://montygroup.uk/?t=$(date +%s)" | grep -i 'age:'
# Should show 'age: 0' or a very small number
```
