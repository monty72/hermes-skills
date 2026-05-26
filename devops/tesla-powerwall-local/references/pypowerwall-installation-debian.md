# pyPowerwall Installation on Debian 13+

## The Problem

Debian 13+ ships with PEP 668 enforced (`externally-managed-environment`). Running:
```bash
pip install pypowerwall
```
fails with:
```
error: externally-managed-environment
× This environment is externally managed
╰─> To install Python packages system-wide, try apt install python3-xyz
```

## Solutions

### Preferred: pipx (installs pypowerwall globally in isolated venv)
```bash
# pipx is usually pre-installed on Debian 13+
pipx install pypowerwall
# Binary is now available as `pypowerwall`
pypowerwall get -cloud
```

### Alternative: Dedicated venv
```bash
python3 -m venv ~/pw-venv
~/pw-venv/bin/pip install pypowerwall
# Use: ~/pw-venv/bin/pypowerwall get -cloud
```

### Blunt instrument: --break-system-packages
```bash
pip install pypowerwall --break-system-packages
# Works but bypasses Debian's safety mechanism
# The authtoken command still needs pywebview deps:
pip install pywebview --break-system-packages -q
```

## GUI Dependencies (for authtoken popup on Linux)

The `pypowerwall authtoken` command opens a native WebView window. On Linux this needs:

```bash
sudo apt install python3-gi gir1.2-webkit2-4.0
```

Without these, `authtoken` fails with:
```
RuntimeError: Missing system libraries required for the Linux login window.
```

On headless machines, `authtoken` auto-detects the remote session and switches to the two-machine flow (prints instructions to run `authtoken` on a desktop machine instead).
