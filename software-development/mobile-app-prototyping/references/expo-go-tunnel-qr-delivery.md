# Expo Go Tunnel + QR Code Delivery

## Problem

Newer Expo Go versions have **removed the "Enter URL manually"** text field from the homescreen. The only way to open a project is:
- Scan a QR code (via iPhone Camera app or in-app scanner)
- Receive a deep link (`exp://` protocol) from another app

In a headless environment (no display for QR rendering, Telegram-based delivery), this creates a challenge: how do you show a QR code to the user?

## Solution: API-Generated QR Code

### Step 1: Start in Tunnel Mode

```bash
./node_modules/.bin/expo start --tunnel --port 8084
```

Wait for output showing: `Metro waiting on exp://<tunnel-id>.exp.direct`

The `--tunnel` flag uses Expo's tunnel service (powered by ngrok) to create a public URL reachable from any device, even across different networks. This is essential because:
- `--lan` mode only works on the same WiFi
- Users scanning QR codes on mobile are likely on cellular or a different network

### Step 2: Generate the QR Code

Use the free [goqr.me](https://goqr.me) API:

```bash
TUNNEL_URL="exp://abc123-anonymous-8084.exp.direct"
curl -s "https://api.qrserver.com/v1/create-qr-code/?size=400x400&data=${TUNNEL_URL}" \
  -o /tmp/expo-qr.png
```

This returns a 400×400 PNG QR code.

### Step 3: Send to User via MEDIA

Include `MEDIA:/tmp/expo-qr.png` in the response. On Telegram, this sends the image natively. The user:

1. Saves or screenshots the image (or just points another device at it)
2. Opens the **iPhone Camera app** (not Expo Go, not Safari)
3. Points the camera at the QR code
4. Taps the **notification banner** that appears: "Open in Expo Go"
5. The app loads automatically

### Why This Works

- iPhone's built-in Camera app automatically detects `exp://` URLs in QR codes
- It presents a system-level notification banner to open Expo Go
- No Safari, no "Enter URL manually", no manual URL typing needed
- Works across networks (tunnel mode)

### Option B: Deep Link Redirect Page (Fallback)

If QR scanning doesn't work (rare edge case), serve an HTML redirect:

```bash
# 1. Create index.html
cat > /tmp/index.html << 'EOF'
<!DOCTYPE html>
<html><body style="background:#000;color:#0f0;font-family:system-ui;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  min-height:100vh">
<img src="https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=exp://tunnel-url.exp.direct"
  style="width:250px;height:250px;border-radius:12px;margin-bottom:20px">
<a href="exp://tunnel-url.exp.direct"
  style="background:#0f0;color:#000;padding:16px 40px;border-radius:12px;font-weight:700">
  Open in Expo Go
</a>
</body></html>
EOF

# 2. Serve it
cd /tmp && python3 -m http.server 8085 &

# 3. Tunnel it via lhr.life
ssh -R 80:localhost:8085 nokey@localhost.run
# Returns: https://<hash>.lhr.life
```

The user opens the `https://...` URL in Safari, sees the QR code + button, and taps "Open in Expo Go".

## Session Context

This was used for the Powerwall monitoring app during development. The `--lan` mode was used initially (user on same WiFi), but after half a dozen reloads and dependency fixes, switching to `--tunnel` + QR code was the most reliable delivery method.
