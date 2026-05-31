---
name: ha-addon-management
description: Install and configure Home Assistant add-ons (Docker-based supervisor apps) and HACS frontend cards (Lovelace plugins) on HAOS via CLI and SSH.
category: devops
---

# Home Assistant — Add-on & HACS Frontend Card Management

Manage HAOS add-ons (supervisor-managed Docker containers) and HACS Lovelace frontend cards from the CLI. Covers the full lifecycle: repository management, add-on installation, HACS card deployment, and supervisor troubleshooting.

## When to use

- User asks you to install or recommend HA add-ons (Studio Code Server, Samba, Node-RED, ESPHome, Zigbee2MQTT, Google Drive Backup, etc.)
- User needs HACS frontend cards installed (Power Flow Card, ApexCharts, Mushroom, Mini Graph Card, etc.)
- User wants to add a community add-on repository (Zigbee2MQTT, Google Drive Backup, etc.)
- You encounter supervisor/CLI errors during installation

## Prerequisites

- SSH access to HAOS as `root@<ha-ip>`
- HACS integration already configured in HA (for frontend cards)
- HA CLI (`ha`) available on the HAOS machine

## HA CLI Command Reference

Key commands for add-on management:

```
ha store add <github_url>       # Add a new add-on repository
ha store reload                  # Reload stores after adding repos
ha store apps install <slug>     # Install an add-on (NOT 'ha addons install')
ha store apps info <slug>        # Check add-on details (version, state)
ha store apps update <slug>      # Update an add-on
ha store delete <slug_or_id>     # Remove a repository
ha supervisor update              # Update supervisor itself
ha supervisor info                # Check supervisor health and version
```

> **NOTE:** The `ha addons` subcommand exists but is deprecated/limited. Use `ha store apps` for install/update operations.

## Step 1 — Install Add-ons

### 1a. Add Any Missing Repositories

Some add-ons live in repositories that aren't pre-configured. Add them first:

```bash
ssh root@<ha-ip> "ha store add https://github.com/zigbee2mqtt/hassio-zigbee2mqtt"
ssh root@<ha-ip> "ha store add https://github.com/sabeechen/hassio-google-drive-backup"
ssh root@<ha-ip> "ha store reload"
```

Then find the slug from the store listing:

```bash
ssh root@<ha-ip> "ha store apps list" | grep -i "<name>"
# e.g.: ssh root@<ha-ip> "ha store apps list" | grep -i "zigbee"
# Returns: slug: 45df7312_zigbee2mqtt
```

**Important:** `ha store reload` is needed after adding repos AND after updating the supervisor. Without a reload, newly added repos won't appear in `ha store apps list`.

### 1b. Resolve Supervisor Version Block

If `ha store apps install` fails with:

```
Error: 'AppManager.install' blocked from execution, supervisor needs to be updated first
```

Update the supervisor first, then retry:

```bash
ssh root@<ha-ip> "ha supervisor update"
```

**Important:** After `ha supervisor update`, the supervisor restarts. For 5-30 seconds, the API returns `connection refused`. Don't panic — wait and retry:

```bash
# Wait for supervisor to come back (try every 5s)
sleep 5 && ssh root@<ha-ip> "ha supervisor info" 2>/dev/null || sleep 10 && ssh root@<ha-ip> "ha supervisor info"
# Then reload the store and install
ssh root@<ha-ip> "ha store reload"
ssh root@<ha-ip> "ha store apps install <slug>"
```

### 1c. Install the Add-on

```bash
ssh root@<ha-ip> "ha store apps install <slug>"
```

Common add-on slugs:

| Add-on | Slug |
|---|---|
| Studio Code Server | `a0d7b954_vscode` |
| Samba share | `core_samba` |
| Node-RED | `a0d7b954_nodered` |
| ESPHome | `5c53de3b_esphome` |
| Zigbee2MQTT | `45df7312_zigbee2mqtt` |
| Google Drive Backup | `cebe7a76_hassio_google_drive_backup` |
| File editor | `core_configurator` |
| Mosquitto broker | `core_mosquitto` |
| Terminal & SSH | `core_ssh` |
| Let's Encrypt | `core_letsencrypt` |
| MariaDB | `core_mariadb` |

## Step 2 — Install HACS Frontend Cards

HACS frontend cards (Lovelace plugins) are JavaScript files that appear in the dashboard card picker. They're registered in HACS's internal storage (`/config/.storage/hacs.data`, `hacs.repositories`) and served from `/config/www/community/<repo-name>/`.

### Via HACS API (preferred but requires HA token)

If you have a HA long-lived access token, you can install cards via HACS's internal API endpoints. This is complex — prefer the git clone approach for automation.

### Via Git Clone (direct file deployment)

When you can't easily authenticate with the HA API, clone repos directly:

```bash
ssh root@<ha-ip> "mkdir -p /config/www/community"
ssh root@<ha-ip> "cd /config/www/community && git clone --depth 1 https://github.com/{owner}/{repo}.git"
```

After cloning, the card files are servable by HA's frontend. The user will need to:
1. Go to HA Settings → Dashboards → Resources → Add Resource
2. Add the path: `/community/<repo-name>/<entrypoint-file.js>`
3. Or add the card directly in dashboard edit mode (modern HACS cards are auto-discovered)

### Common HACS Frontend Cards & Their Repos

| Card | Repo | Entry File (for manual resource registration) |
|---|---|---|
| Power Flow Card Plus | `flixlix/power-flow-card-plus` | `power-flow-card-plus.js` |
| ApexCharts Card | `RomRider/apexcharts-card` | `apexcharts-card.js` |
| Mushroom | `piitaya/lovelace-mushroom` | `mushroom.js` |
| Mini Graph Card | `kalkih/mini-graph-card` | `mini-graph-card.js` |

> **Note:** Many of these cards are already registered in HACS data (showing as "installed") but may not have their JS files downloaded. Git clone fixes this — it puts the files where HA expects them.

> **Power Flow Card vs Plus:** `power-flow-card-plus` is the actively maintained fork and the one users should use. Skip the original `power-flow-card`.

### Listing All Installed Add-ons

`ha store apps list` returns the **full add-on catalog** (both installed and available), not just installed ones. To see only what's installed:

```bash
ssh root@<ha-ip> "ha store apps list" | grep -B5 "installed: true" | grep "name:"
```

### Finding an Add-on Slug

When you don't know the slug, search the store listing:

```bash
ssh root@<ha-ip> "ha store apps list" | grep -i "<partial-name>"
# Then check the slug + installed status:
ssh root@<ha-ip> "ha store apps list" | grep -B10 -i "<partial-name>" | grep -E "(name:|slug:|installed:)"
```

---

## Step 3 — Verify Installation

After installing, check that the add-on shows as `installed: true`:

```bash
ssh root@<ha-ip> "ha store apps info <slug>"
# Look for: "installed: true"
```

Check the full list of installed add-ons (those with `"installed": true`):

```bash
ssh root@<ha-ip> "ha store apps list" | grep -A2 "installed: true" | grep "name:"
```

For HACS cards, verify files exist:

```bash
ssh root@<ha-ip> "ls /config/www/community/<repo-name>/"
```

## Pitfalls

1. **Supervisor update blocks add-on installs.** The most common error. Always check and update the supervisor before trying to install add-ons.

2. **`ha supervisor addons add` doesn't exist.** Adding repos uses `ha store add <url>`, not a supervisor subcommand. The `ha supervisor` help lists no `addons` subcommand.

3. **Samba needs a password set.** After installing, the add-on runs but is not accessible until a password is configured in Settings → Add-ons → Samba share → Configuration. Default username is `homeassistant`.

4. **Zigbee2MQTT needs a coordinator.** The add-on installs fine but won't work until a Zigbee coordinator dongle (Conbee/Sonoff) is plugged in and configured.

5. **Google Drive Backup needs OAuth.** First launch opens a browser to link your Google account. No backup runs until this is done.

6. **Add-ons with ingress** (Studio Code Server, Node-RED, ESPHome) are accessible directly from the HA sidebar after install — no extra config needed.

7. **No python3 on HAOS.** HAOS is a minimal Linux. Parse JSON with tools available (grep, sed, simple shell) rather than python3 for remote inspection of `.storage` files.

8. **`ha store apps start` returns the full app list** not a confirmation message. The add-on may auto-start on install. Check `ha store apps info <slug>` for `state: started`.

## Cross-References

- **Custom components:** For installing HA integrations (not add-ons), see `ha-component-deployment`
- **Octopus Energy:** For Octopus-specific API and integration setup, see `octopus-energy`
- **Tesla/Powerwall:** For Powerwall monitoring integrations, see `tesla-powerwall-cloud` and `tesla-powerwall-local`
- **Energy dashboard:** For the live Powerwall data bridge in HA, see `tesla-energy-dashboard`
