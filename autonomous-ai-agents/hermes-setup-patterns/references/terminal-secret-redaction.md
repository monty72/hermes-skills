# Terminal Secret Redaction Behaviour

## What Happens

Hermes' terminal environment (and some shell configurations) automatically masks strings that look like secrets in displayed output. This includes:

- `sk-...` patterns (API keys)
- `AIza...` patterns (Google API keys)
- `eyJ...` patterns (JWT tokens)
- `***` (placeholder markers)
- `BSA...` patterns (Brave API keys)

This masking happens at the **display layer only** — the actual file contents are unchanged.

## Observed Behaviour

| Action | Terminal Display | Actual File State |
|--------|-----------------|-------------------|
| `grep DEEPSEEK_API_KEY .env` | `DEEPSEEK_API_KEY=***` | `DEEPSEEK_API_KEY=sk-dc10...` (real key) |
| `cat -A .env` | `DEEPSEEK_API_KEY=***` | Real key in bytes |
| `sed -n '475p' .env \| od -c` | Shows real characters | Confirms file is correct |
| Python `print(val)` | `***` | Variable holds real value |
| Python `len(val)` | Returns 35 (for `sk-...`) | Confirms real key |
| Writing `GOOGLE_API_KEY=sk-test12345` to temp file | Read back shows `***` | File has correct content |

## How to Verify Truth

### Method 1: Check Value Length

```python
import os
with open(os.path.expanduser('~/.hermes/.env')) as f:
    for line in f:
        if line.startswith('DEEPSEEK_API_KEY='):
            val = line.split('=', 1)[1].strip()
            print(f'len={len(val)}, starts_with_sk={val.startswith("sk-")}')
# Real key: len > 30, starts with sk-/AIza/eyJ
# Placeholder: len == 3 (***)
```

### Method 2: Check File Size

If you modified `.env` and the file size changed, the modification took effect regardless of what `grep` shows.

### Method 3: Raw Byte Inspection

```bash
sed -n '<line_number>p' ~/.hermes/.env | od -c
```

This bypasses all terminal masking and shows the actual bytes.

## Impact

The redaction causes:

1. **False negatives in verification:** You think a `sed` replacement failed when it actually worked
2. **Apparent circular problems:** Vault seems to store `***` because the GET output is masked
3. **Confusing diffs:** Git diff shows the real key but terminal view shows `***`

## Workaround

When doing vault-to-env restoration, use Python to read and write — don't rely on `grep`, `cat`, or other terminal-displayed output to verify state. Always use programmatic length checks or byte inspection.
