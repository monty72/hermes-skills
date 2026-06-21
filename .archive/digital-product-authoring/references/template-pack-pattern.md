# Template Pack Pattern

Standard file structure for digital template packs (ADRs, scorecards, etc.)

## File Structure

```
public/products/{product-slug}-{descriptor}.md    # Human-readable (Markdown)
public/products/{product-slug}-{descriptor}.yaml   # Machine-readable (YAML)
public/products/{product-slug}-example-{topic}.md  # Worked example
public/products/{product-slug}-readme.md            # Usage instructions
public/products/{product-slug}.zip                  # Bundle of all files
```

## File Naming Convention

| File | Purpose |
|------|---------|
| `{slug}-template-markdown.md` | Main human-readable template |
| `{slug}-template-yaml.yaml` | Machine-parseable template |
| `{slug}-example-{description}.md` | Real worked example |
| `{slug}-pack-readme.md` | Bundle README |
| `{slug}.zip` | All files packaged |

## ZIP Packaging

```python
import zipfile, os
files = ['adr-template-markdown.md', 'adr-template-yaml.yaml',
         'adr-example-aks.md', 'adr-template-pack-readme.md']
with zipfile.ZipFile('adr-template-pack.zip', 'w') as z:
    for f in files:
        z.write(f, os.path.basename(f))  # Strip directory paths
```

## ADR Template Format

Architecture Decision Records follow a standard format:

1. **Title** — ADR-[NUMBER]: [Title]
2. **Status** — proposed | accepted | deprecated | superseded
3. **Context** — What issue motivates the decision? Forces at play?
4. **Decision** — What is the change being proposed?
5. **Consequences** — Positive + negative tradeoffs
6. **Compliance** — How adherence is enforced
7. **Notes** — Links, references, related ADRs
8. **Metadata** — Author, date, reviewers

The YAML version adds structured fields for CI/CD parsing: `superseded_by`, `tags`, `links`, `reviewers`.
