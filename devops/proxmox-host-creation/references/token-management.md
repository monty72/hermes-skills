# Proxmox API Token Management

## Token Creation (from Proxmox shell)

```bash
# Create user (one-time)
pveum user add hermes2@pve

# Grant full admin access
pveum acl modify / -user hermes2@pve -role Administrator

# Create a token
pveum user token add hermes2@pve api --privsep 0
```

Output:
```
┌──────────────┬──────────────────────────────────────────┐
│ key          │ value                                    │
╞══════════════╪══════════════════════════════════════════╡
│ full-tokenid │ hermes2@pve!api                          │
├──────────────┼──────────────────────────────────────────┤
│ info         │ {"privsep":"0"}                          │
├──────────────┼──────────────────────────────────────────┤
│ value        │ 19b5fd1b-9354-47fd-8847-4ebbe28a4abb     │
└──────────────┴──────────────────────────────────────────┘
```

## Authorization Header Format

```
PVEAPIToken=<full-tokenid>=<value>
```

Example:
```
PVEAPIToken=hermes2@pve!api=19b5fd1b-9354-47fd-8847-4ebbe28a4abb
```

## Realm Differences

| Realm | Characteristics | Use Case |
|-------|----------------|----------|
| `@pve` | Proxmox VE built-in auth | **PREFERRED** for API tokens — full ACL support |
| `@pam` | Linux PAM (system users) | Harder to grant API permissions; password logins to web UI |

**Always create API tokens under `@pve` realm**, not `@pam`.

## Token Permission Failure Modes

### Token authenticates but returns empty data

If `curl -sk "$HOST/api2/json/nodes/pve1/status"` returns `{"data":null,"message":"Permission check failed..."}`, the token exists but lacks the `Sys.Audit` privilege. Fix: ensure the user has `Administrator` role on `/` path via:
```
pveum acl modify / -user <userid> -role Administrator
```

### Token returns "401 invalid token value"

The token string format is wrong. Verify:
1. The `full-tokenid` and `value` are separated by `=` (not a space)
2. The header format is `PVEAPIToken=<full-tokenid>=<value>` (no extra quotes)
