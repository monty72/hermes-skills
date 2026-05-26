# montygroup.uk Cloudflare Tunnel Setup

Record of the named tunnel deployment on montygroup.uk (May 26, 2026).

## Domain

**montygroup.uk** — registered via FoundationDNS, nameservers set to Cloudflare. Zone ID: `fc8c38faae1484df4b9c241c877e2ec0`.

Cloudflare account ID: `a6f9315a00dae2ea1f45a82f75e43d44`

## API Token

Token ID: `03633343c5cd11d888bfd6bc0e645258`
Scopes: `Zone > DNS > Edit` (montygroup.uk) + `Account > Cloudflare Tunnel > Edit`
Expires: 2027-05-25

## Named Tunnel

| Property | Value |
|----------|-------|
| Name | hermes-dev |
| ID | `c27485f9-8d04-47ac-8ed2-325a591b0991` |
| Secret | `fe2845b61b697b53e26e9a2f99ec9d59144b89428e24b6f4435ce8d2c37a9295` |
| Config | `~/.cloudflared/config.yml` |
| Credentials | `~/.cloudflared/c27485f9-8d04-47ac-8ed2-325a591b0991.json` |

## DNS Records (all proxied CNAME)

All subdomains CNAME to `c27485f9-8d04-47ac-8ed2-325a591b0991.cfargotunnel.com`:

| Hostname | Tunnel Ingress |
|---|---|
| `montygroup.uk` | :8000 (Flask) |
| `mc.montygroup.uk` | :8000 (Flask) |
| `energy.montygroup.uk` | :8000 (Flask) |
| `dev.montygroup.uk` | :8000 (Flask) |
| `bots.montygroup.uk` | :8000 (Flask) |
| `childminding.montygroup.uk` | :8000 (Flask) |

## Apex CNAME Caveat

The root `montygroup.uk` CNAME resolves correctly via public DNS (Cloudflare returns 172.67.190.231 / 104.21.84.94) and serves content through the tunnel from the internet. However, **it cannot be tested from inside the local network** because the router DNS (192.168.1.254) does not forward for domains it doesn't natively know about. Subdomains like `mc.montygroup.uk` work from anywhere, including the local network, because Cloudflare edge DNS handles them differently. To test `montygroup.uk` locally, add an /etc/hosts entry or access it from a device on an external network (e.g., mobile data).

## Automation

**Watchdog:** Hermes cron job `8f332fbced4f` runs `tunnel-watchdog.sh` every 5 minutes (no_agent mode). Script checks if `cloudflared tunnel run hermes-dev` is running; starts it if not.

**Script:** `~/.hermes/scripts/tunnel-watchdog.sh`

## Restart Procedure

```bash
# Manual restart
pkill -f "cloudflared.*run hermes-dev" 2>/dev/null
sleep 2
~/.local/bin/cloudflared tunnel run hermes-dev &
```
