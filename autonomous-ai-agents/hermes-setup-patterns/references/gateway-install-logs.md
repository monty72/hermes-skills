# Gateway Install Reference: Session Logs

From a real install on Linux 6.12 (Debian), Hermes Agent with DeepSeek provider, user `matth`:

## Initial Run (no service)

```bash
hermes gateway run
```
- Gateway started in foreground, connected to Telegram immediately (Telegram was pre-configured in config.yaml)
- Discord attempted connection and failed with no token — harmless
- Output: INFO logs for telegram connected, discord failed, cron ticker started, kanban dispatcher started
- Timed out after 30s in terminal() test because it runs indefinitely waiting for messages

## Service Installation

```bash
hermes gateway install
```
Output:
```
Start the gateway now after installing the service? [Y/n]:
Start the gateway automatically on login/boot with systemd? [Y/n]:
```

Note: these are two separate `input()` calls, both requiring Enter. Single `echo "Y" | hermes gateway install` fails because it only answers the first prompt.

Fix used:
```bash
printf "Y\nY\n" | hermes gateway install
```

Success output:
```
Created symlink '.../default.target.wants/hermes-gateway.service' → '.../hermes-gateway.service'.
Installing user systemd service to: /home/matth/.config/systemd/user/hermes-gateway.service
✓ User service installed and enabled!
Next steps:
  hermes gateway start              # Start the service
  hermes gateway status             # Check status
  journalctl --user -u hermes-gateway -f  # View logs
Enabling linger so the gateway survives SSH logout...
✓ Linger enabled — gateway will persist after logout
✓ User service started
```

## Post-Install Verification

```bash
hermes gateway status
# → ✓ Gateway is running (PID: ...)
```

The gateway log showed Telegram connected successfully with 30 bot commands registered across all scopes.
