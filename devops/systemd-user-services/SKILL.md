---
name: systemd-user-services
description: Run self-hosted tools (LiteLLM, Next.js dashboards, API proxies) as systemd user services with auto-restart and boot persistence.
tags: [systemd, user-service, auto-restart, daemon, linux, service-management, self-hosted]
---

# Systemd User Services — Self-Hosted Tool Pattern

Run self-hosted CLI tools, proxies, and dashboards as systemd **user** services (not system-level). This gives you auto-restart on crash, auto-start on boot, and journald logging — all without root.

## When to Use

- A long-lived process that should survive reboots (LiteLLM proxy, MC dashboard, API adapter)
- A process that crashes and needs auto-restart
- You want clean logs via `journalctl --user -u service-name`

## Lifecycle

```bash
# Create the unit file
mkdir -p ~/.config/systemd/user
vim ~/.config/systemd/user/my-service.service

# After editing any .service file
systemctl --user daemon-reload

# Control
systemctl --user enable my-service.service   # auto-start on boot
systemctl --user start my-service.service    # start now
systemctl --user status my-service.service   # check state
systemctl --user stop my-service.service     # stop
systemctl --user restart my-service.service  # stop + start

# Logs
journalctl --user -u my-service.service --no-pager -n 50
```

## Unit File Template

```ini
[Unit]
Description=My Service — what it does
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=%h/path/to/project
ExecStart=%h/path/to/binary --args
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

## Finding the Right ExecStart Path — Debug Flow

This is the **most common failure mode**. Systemd can't find binaries the way your shell can.

```bash
# Step 1: Find the actual binary
which node       # → /home/user/.local/bin/node
file $(which node)  # check if it's a symlink
# → /home/user/.local/bin/node: symbolic link to /home/user/.hermes/node/bin/node

# Step 2: Use the resolved absolute path in ExecStart
# ❌ Don't use: /usr/bin/node (it doesn't exist here)
# ❌ Don't use: node (PATH is restricted in systemd)
# ❌ Don't use: ~/.local/bin/node (~ expansion doesn't work, use %h)
# ✅ Use: %h/.hermes/node/bin/node

# Step 3: For Python tools installed via pip globally (~/.local/)
which litellm  → /home/user/.local/bin/litellm
file $(which litellm)  # → Python script, ASCII text executable
head -1 $(which litellm)  # → #!/usr/bin/python3
# ✅ Use: %h/.local/bin/litellm (systemd has its own python3)

# Step 4: For a Python module from a venv
# ✅ Use: %h/.hermes/hermes-agent/venv/bin/python -m litellm
```

## Exit Code Diagnosis

| Exit Code | Meaning | Most Likely Cause |
|-----------|---------|-------------------|
| 203 (EXEC) | Binary not found at path | Wrong path in ExecStart, path is a broken symlink |
| 127 | Command not found | Shebang interpreter missing (e.g. `#!/usr/bin/node` but node is at `%h/.hermes/node/bin/node`) |
| 1 | General failure | App started but crashed — check `journalctl --user -u name` for app-level error |
| 0 | OK (but auto-restart will restart it) | Normal exit, but `Restart=always` will bring it back |

## Pitfalls

- **`~` doesn't work in ExecStart** — use `%h` instead (systemd expansion for home directory)
- **PATH is minimal** — systemd user services inherit almost no PATH. Always use absolute paths.
- **Environment variables** — `.bashrc`, `.profile`, `.bash_aliases` are NOT sourced. Use `Environment=` directives in the unit file or point directly to the binary.
- **Symlinks** — `node_modules/.bin/next` is a symlink. systemd can follow it, but if the underlying path is a relative link and WorkingDirectory is set, it depends on that. When in doubt, resolve to the real path.
- **`daemon-reload` required** — every time you edit the unit file, run `systemctl --user daemon-reload` or changes are ignored.
- **User services vs system services** — user services run under `systemctl --user` and survive only while the user is logged in. With `logind keep-alive` (default on most modern distros), this means they survive reboots. If you need root-level isolation, use system services with sudo.
- **Old process on the port** — if a background process (from terminal background=true) is still running on the port, systemd will fail to bind. Kill the old process first.

## Examples in Production

- **LiteLLM proxy** (`litellm-proxy.service`) — `%h/.local/bin/litellm --config %h/.litellm/config.yaml --port 4000 --host 0.0.0.0`
- **MC V4 dashboard** (`mc-v4.service`) — `%h/.hermes/node/bin/node %h/mission-control-v4/node_modules/next/dist/bin/next start --port 3000 --hostname 0.0.0.0`

## Verification

```bash
# After start, wait a few seconds then check
systemctl --user status my-service.service --no-pager | head -8
curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:PORT/
```

## Related

- `docker-management` skill — for containerized services (alternative to bare systemd)
