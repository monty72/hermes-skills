---
name: sherlock
description: "OSINT username search across 400+ social networks via Sherlock project."
version: 1.0.0
---

# Sherlock — OSINT Username Search

## Overview

Search for a username across 400+ social networks using the Sherlock project.

## Requirements

```bash
pip install sherlock
# Or standalone:
git clone https://github.com/sherlock-project/sherlock.git
cd sherlock
pip install -r requirements.txt
```

## Usage

```bash
# Search a single username
python sherlock/sherlock USERNAME --output results.txt

# Search multiple usernames
python sherlock/sherlock USERNAME1 USERNAME2

# Output as JSON
python sherlock/sherlock USERNAME --output result.json --json

# Specific sites
python sherlock/sherlock USERNAME --sites "GitHub Twitter Reddit"

# Timeout
python sherlock/sherlock USERNAME --timeout 10
```

## Python API

```python
from sherlock_project.sherlock import Sherlock
from sherlock_project.result import QueryResult

sherlock = Sherlock()
results = sherlock.search("username")
for site, result in results.items():
    if result.status == QueryResult.STATUS_CLAIMED:
        print(f"[+] {site}: {result.url_user}")
    elif result.status == QueryResult.STATUS_AVAILABLE:
        print(f"[-] {site}: available")
```

## Common Use Cases

- **Identity verification**: Confirm a username across platforms
- **Account recovery**: Find where a username is registered
- **OSINT**: Profile a target from multiple angles
- **Brand monitoring**: Check if a username/brand is taken
