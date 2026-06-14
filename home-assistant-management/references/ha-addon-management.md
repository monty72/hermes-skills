# HA Add-on & HACS Frontend Card Management — Full Reference

*Absorbed from the consolidated `ha-addon-management` skill.*

## HA CLI Command Reference

```
ha store add <github_url>       # Add a new add-on repository
ha store reload                  # Reload stores after adding repos
ha store apps install <slug>     # Install an add-on
ha store apps info <slug>        # Check add-on details (version, state)
ha store apps update <slug>      # Update an add-on
ha store delete <slug_or_id>     # Remove a repository
ha supervisor update              # Update supervisor itself
ha supervisor info                # Check supervisor health and version
```

**NOTE:** `ha addons` subcommand is deprecated/limited. Use `ha store apps` for install/update.

## Common Add-on Slugs

| Add-on | Slug |
|--------|------|
| Studio Code Server | `a0d7b954_vscode` |
| Samba share | `core_samba` |
| Zigbee2MQTT | `45df7312_zigbee2mqtt` |
| Google Drive Backup | `cebe7a76_hassio_google_drive_backup` |
| Node-RED | `a0d7b954_nodered` |
| ESPHome | `5c53de3b_esphome` |
| Mosquitto broker | `core_mosquitto` |
| Terminal & SSH | `core_ssh` |
| File editor | `core_configurator` |
| Let's Encrypt | `core_letsencrypt` |
| MariaDB | `core_mariadb` |

## HACS Frontend Cards

Deploy via git clone:
```bash
ssh root@<ha-ip> "mkdir -p /config/www/community && cd /config/www/community && git clone --depth 1 https://github.com/{owner}/{repo}.git"
```

Common cards: `flixlix/power-flow-card-plus`, `RomRider/apexcharts-card`, `piitaya/lovelace-mushroom`, `kalkih/mini-graph-card`.

## Key Pitfalls

1. **Supervisor version blocks installs** — `ha supervisor update` first, then wait 5-30s for it to restart
2. **Store reload required** — after adding repos AND after supervisor updates
3. **Samba needs password** — configure in Settings → Add-ons → Samba share → Configuration (default username: `homeassistant`)
4. **No python3 on HAOS** — parse JSON with grep/sed, not python3
5. **`ha store apps list` shows ALL catalog items** (both installed and available), not just installed ones
