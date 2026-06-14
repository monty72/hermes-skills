# Systemd User Services — Full Reference

*Absorbed from the consolidated `systemd-user-services` skill.*

## Lifecycle

```bash
mkdir -p ~/.config/systemd/user
systemctl --user daemon-reload          # After editing any .service file
systemctl --user enable my-service      # auto-start on boot
systemctl --user start my-service       # start now
systemctl --user status my-service      # check state
systemctl --user restart my-service     # stop + start
journalctl --user -u my-service -n 50   # logs
```

## Unit File Template

```ini
[Unit]
Description=Service description
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=%h/path/to/project
ExecStart=%h/.local/bin/binary --args
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

## ExecStart Path Debugging

**Most common failure mode.** systemd can't find binaries the way your shell can:

1. Find binary: `which node` → `/home/user/.local/bin/node`
2. Follow symlinks: `file $(which node)` → symlink to `/home/user/.hermes/node/bin/node`
3. Use resolved absolute path in ExecStart: `%h/.hermes/node/bin/node`

**Rules:**
- ❌ Don't use: `~` (doesn't expand), `node` (PATH not set), or bare path
- ❌ Don't use: `~/.local/bin/binary`
- ✅ Use: `%h/.local/bin/litellm` or `%h/.hermes/node/bin/node`

## Exit Code Diagnosis

| Code | Meaning | Likely Cause |
|------|---------|-------------|
| 203 | Binary not found | Wrong path, broken symlink |
| 127 | Command not found | Shebang interpreter missing |
| 1 | General failure | App crashed — check journalctl |

## Production Examples

**LiteLLM proxy:**
```ini
ExecStart=%h/.local/bin/litellm --config %h/.litellm/config.yaml --port 4000 --host 0.0.0.0
```

**MC V4 dashboard:**
```ini
ExecStart=%h/.hermes/node/bin/node %h/mission-control-v4/node_modules/next/dist/bin/next start --port 3000 --hostname 0.0.0.0
```

## Pitfalls

- `~` doesn't work in ExecStart — use `%h`
- PATH is minimal — always use absolute paths
- `.bashrc`, `.profile`, `.bash_aliases` are NOT sourced — use `Environment=` directives
- `daemon-reload` required after every edit
- User services survive while user is logged in (logind keep-alive on modern distros)
- Old process on same port blocks systemd — kill it first (`process(action='kill')` or `kill $(lsof -ti:PORT)`)
