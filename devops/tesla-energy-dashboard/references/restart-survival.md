# Gateway Restart Survival — Energy Dashboard

## The Problem

When `hermes gateway restart` is called (for config changes, HA token updates, or weekly maintenance), the agent session is killed. Background processes (energy API server, tunnel, combined proxy server) are all children of the gateway process and may or may not survive depending on how they were started.

## What Survives

- **`systemd --user` services** — these are independent of the gateway. The gateway itself runs this way, and any services registered via `systemd --user` will survive.
- **Standalone background processes** started with `terminal(command='... &', background=True)` from within an agent session — these are Python subprocesses of the gateway. They **may** survive a gateway restart depending on the `SIGTERM` propagation.
- **Tmux sessions** — fully independent.

## What Dies

- **Foreground processes** started via `terminal(background=false)` — these block until the command finishes and are gone when the session ends.
- **Python subprocesses** launched from `execute_code` or `terminal` with `nohup`/`background=true` — these are child processes of the gateway process tree. A `hermes gateway restart` sends `SIGTERM` to the gateway process group, which forwards to children.

## Restart Recovery Pattern

After a gateway restart, check and re-launch the energy stack:

```bash
# 1. Check what's still running
ps aux | grep -E 'energy_api|api.py.*8000|localhost.run' | grep -v grep

# 2. Restart backend API
cd ~/energy-dashboard && python3 src/energy_api.py &

# 3. Restart combined proxy/static server
cd ~/dev-site/src && python3 api.py 8000 &

# 4. Restart tunnel
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 \
  -R 80:localhost:8000 nokey@localhost.run
```

## Prevention

- **Schedule gateway restarts via cron** at 4 AM Sunday (low usage time) — `cronjob` action already set up
- **Never restart the gateway mid-conversation** — config changes that need a restart should be saved and applied during the next scheduled window, or explicitly approved by the user first
