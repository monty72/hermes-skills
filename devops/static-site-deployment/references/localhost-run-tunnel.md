# localhost.run Deployment Guide

## Quick Start

```bash
# In terminal 1: start a server
cd ./dist && python3 -m http.server 8080

# In terminal 2: create tunnel
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 \
  -R 80:localhost:8080 nokey@localhost.run
```

## Output

The tunnel prints:
```
<hash>.lhr.life tunneled with tls termination, https://<hash>.lhr.life
```

This is the public URL.

## Known Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Connection refused | Server not running yet | Start http.server first, then tunnel |
| Tunnel hangs | Network interruption | Kill (Ctrl+C) and restart |
| "Pseudo-terminal will not be allocated" | Background/pty mode | Normal warning, ignore — tunnel works |
| URL changed | New session, new hash | Read output URL each time |
| Slow first request | Cold start | Tunnel is warm but server process may need first hit |

## Background Mode

```bash
# Start in background (must use background=true in terminal tool)
terminal(command="cd /home/matth/mission-control/src && python3 -m http.server 8080", background=true)

# Then create tunnel
terminal(command="ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -R 80:localhost:8080 nokey@localhost.run", background=true)

# Wait a few seconds, then check tunnel output
process(action="poll", session_id="<tunnel-session>")
process(action="log", session_id="<tunnel-session>")  # parse URL from log
```

## Verification

```bash
curl -sI https://<url>/index.html | head -5
# Expected: HTTP/1.1 200 OK
```

## Alternative Tunnels

| Service | Command | Notes |
|---------|---------|-------|
| localhost.run | `ssh -R 80:localhost:8080 nokey@localhost.run` | Free, no signup |
| serveo.net | `ssh -R 80:localhost:8080 serveo.net` | Similar, may be down |
| bore | `bore local 8080 --to bore.pub` | Requires rust/bore binary |
