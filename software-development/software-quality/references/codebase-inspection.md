# Codebase Inspection with pygount

Analyze repositories for lines of code, language breakdown, and code-vs-comment ratios.

## Install

```bash
pip install pygount
```

## Usage

```bash
cd /path/to/repo
pygount --format=summary --folders-to-skip=".git,node_modules,venv,__pycache__,.cache,dist,build,.next,.tox" .
```

**Always use `--folders-to-skip`** — without it, pygount crawls everything and may hang.

## Common Folder Exclusions

| Project Type | Folders to Skip |
|-------------|----------------|
| Python | `.git,venv,.venv,__pycache__,.cache,dist,build,.tox,.eggs,.mypy_cache` |
| JS/TS | `.git,node_modules,dist,build,.next,.cache,.turbo,coverage` |
| General | `.git,node_modules,venv,.venv,__pycache__,.cache,dist,build,.next,.tox,vendor,third_party` |

## Filter by Language

```bash
pygount --suffix=py --format=summary .          # Python only
pygount --suffix=py,yaml,yml --format=summary . # Python + YAML
```

## Output Formats

```bash
pygount --format=summary .  # Summary table (recommended)
pygount --format=json .     # JSON for programmatic use
```

## Interpreting Results

Columns: Language, Files, Code, Comment, %

Pseudo-languages: `__empty__`, `__binary__`, `__generated__`, `__duplicate__`, `__unknown__`

## Pitfalls

1. Markdown shows 0 code lines — classified as comments
2. JSON shows low counts — use `wc -l` for accurate JSON
3. For large monorepos, use `--suffix` to target specific languages
