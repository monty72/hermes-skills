---
name: automated-email-sending
description: "Set up and use a custom-domain bot email via SMTP relay — Gmail App Passwords, msmtp, Python smtplib, Cloudflare Email Routing integration, and deliverability testing."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [email, smtp, gmail, msmtp, cloudflare, automation]
    related_skills: [cloudflare-dns-management, himalaya, hermes-email]
---

# Automated Email Sending

Set up a bot email address at a custom domain and send programmatic emails from Hermes. Covers the full stack: Cloudflare DNS/Email Routing for receiving, Gmail SMTP relay for sending, msmtp and Python smtplib for delivery.

## When to Use

- Sending emails on behalf of a user (notifications, digests, shared content)
- Setting up a bot email address at a custom domain (e.g. `hermes@montygroup.uk`)
- Configuring SMTP relay for programmatic email sending

## Prerequisites

- A domain on Cloudflare (DNS managed by Cloudflare)
- A Cloudflare API token with at least `Zone > DNS > Edit`
- A Gmail account (any) for the SMTP relay
- Python 3 + `smtplib` (stdlib, no install needed)

## End-to-End Workflow

### Phase 1: Cloudflare Email Routing (Receiving)

See `cloudflare-dns-management` skill for full DNS details. Key steps:

1. **Enable Email Routing in the Cloudflare dashboard** — `Zone → Email → Email Routing → Get started`
2. Click **"Add records and finish"** — this triggers Cloudflare to auto-create MX/SPF records
3. Add a **destination address** and **routing rule** (e.g. `hermes@domain → your@inbox.com`)

**⚠️ CRITICAL:** Do NOT manually add MX/SPF records via the API before dashboard enablement. The dashboard expects to create them itself. Manual records cause "dns not configured" errors. If you added them manually, delete them first, then use the dashboard button.

**⚠️ CNAME-at-apex conflict:** If the domain apex has a CNAME (common with Vercel `cname.vercel-dns.com`), it DNS-conflicts with MX records. Fix: delete the apex CNAME and add proxied A records to Vercel's IPs (`76.76.21.21`, `76.76.21.98`). See `cloudflare-dns-management/references/email-dns-records.md` for the exact API calls.

### Phase 2: Gmail App Password (Sending)

Gmail SMTP is the simplest free relay. You need an App Password (not your regular password):

1. Enable **2-Step Verification** on the Gmail account at https://myaccount.google.com/security
2. Go to https://myaccount.google.com/apppasswords
3. Select **Mail** → **Other** → name it "Hermes Bot"
4. Copy the 16-character App Password (format: `xxxx xxxx xxxx xxxx`)
5. Store in the vault: `hermes-vault set EMAIL_PASSWORD "xxxx xxxx xxxx xxxx"`

**Gmail SMTP settings:**
- Host: `smtp.gmail.com`
- Port: `587` (STARTTLS)
- User: the full Gmail address
- Password: the App Password

### Phase 3: msmtp (Lightweight SMTP Client)

```bash
sudo apt-get install -y msmtp msmtp-mta
```

Config at `~/.msmtprc` (chmod 600):

```toml
defaults
auth on
tls on
tls_starttls on
tls_trust_file /etc/ssl/certs/ca-certificates.crt

account gmail
host smtp.gmail.com
port 587
from hermes@montygroup.uk
user matthewhogarth@googlemail.com
password <app-password>

account default : gmail
logfile ~/.hermes/logs/msmtp.log
```

### Phase 4: Python Email Script

A reusable script at `~/scripts/hermes-email.py`:

```python
import smtplib, ssl, os
from email.mime.text import MIMEText

CONFIG = {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "address": os.environ.get("EMAIL_ADDRESS", ""),
    "password": os.environ.get("EMAIL_PASSWORD", ""),
    "default_to": os.environ.get("EMAIL_DEFAULT_TO", "user@example.com"),
}

def send_email(to, subject, body):
    msg = MIMEText(body, _charset="utf-8")
    msg["From"] = f"Hermes Bot <{CONFIG['address']}>"
    msg["To"] = to
    msg["Subject"] = subject
    ctx = ssl.create_default_context()
    with smtplib.SMTP(CONFIG["smtp_host"], CONFIG["smtp_port"], timeout=60) as s:
        s.starttls(context=ctx)
        s.login(CONFIG["address"], CONFIG["password"])
        s.sendmail(CONFIG["address"], [to], msg.as_string())
```

**⚠️ Timeout:** Gmail SMTP can be slow (5-30 seconds). Always use `timeout=60` or higher in `smtplib.SMTP()`.

### Phase 5: Using the Script

```bash
# Directly from Python
python3 -c "
import smtplib, ssl
from email.mime.text import MIMEText

msg = MIMEText('Hello from Hermes!')
msg['From'] = 'Hermes Bot <hermes@montygroup.uk>'
msg['To'] = 'recipient@example.com'
msg['Subject'] = 'Test'

with smtplib.SMTP('smtp.gmail.com', 587, timeout=60) as s:
    ctx = ssl.create_default_context()
    s.starttls(context=ctx)
    s.login('sender@gmail.com', '<app-password>')
    s.sendmail('sender@gmail.com', ['recipient@example.com'], msg.as_string())
"

# Or use the msmtp CLI
echo "Body text" | msmtp recipient@example.com
```

## Sending from a Custom From Address

Gmail SMTP allows you to set a custom `From` header (e.g. `hermes@montygroup.uk`) even though the envelope sender is the Gmail address. Gmail will show the custom From to recipients.

```python
msg["From"] = "Hermes Bot <hermes@montygroup.uk>"
msg["Reply-To"] = "hermes@montygroup.uk"
```

Set the envelope sender to the custom address too for cleaner headers:
```python
server.sendmail("hermes@montygroup.uk", [to], msg.as_string())
```

## Deliverability Testing

Test across email providers:

| Provider | Expected | Check |
|----------|----------|-------|
| Gmail | Inbox | Primary inbox |
| Hotmail/Outlook | Inbox (check junk) | May land in Junk on first send |
| Custom domain | Depends on SPF/DKIM | Verify SPF record includes relay |

**If emails land in spam:**
1. Check SPF record includes your SMTP relay's domain
2. Add DKIM signing (Cloudflare dashboard generates the key)
3. Add a DMARC policy record: `v=DMARC1; p=none`
4. Warm up the sending reputation by sending low volumes initially

## Configuration Storage

Store credentials in the vault, not in plaintext:

```bash
hermes-vault set EMAIL_ADDRESS "sender@gmail.com"
hermes-vault set EMAIL_PASSWORD "xxxx xxxx xxxx xxxx"
```

Set env vars in `~/.hermes/.env`:
```
EMAIL_ADDRESS=sender@gmail.com
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_DEFAULT_TO=matthogarth@hotmail.com
```

## Pitfalls

1. **msmtp timing out** — If `msmtp --debug` hangs, use Python `smtplib` directly with a timeout. msmtp lacks a `--timeout` flag.
2. **Gmail App Passwords require 2FA** — The account MUST have 2-Step Verification enabled. Without it, the App Passwords page doesn't appear.
3. **App Password has spaces** — The password `xxxx xxxx xxxx xxxx` includes spaces. Use it as-is (with spaces) in smtplib.login(). If extracting from vault, trim surrounding whitespace but keep internal spaces.
4. **SMTP timeout on first send** — Gmail's SMTP may take 10-30 seconds on the first connection. Always use `timeout=60`. Debug with `server.set_debuglevel(1)` to confirm it's just slow, not failing.
5. **Cloudflare Email Routing API scope** — DNS:Edit token CANNOT enable Email Routing. The dashboard is required. Error 10000 means the token lacks Zone > Email Routing > Edit.
6. **MX + CNAME cannot coexist at apex** — DNS RFC prohibits this. Always check for apex CNAME before adding MX records.
7. **Cloudflare dashboard bot detection** — dash.cloudflare.com uses JavaScript challenges that headless browsers cannot solve. Guide the user through dashboard steps rather than attempting browser automation.
