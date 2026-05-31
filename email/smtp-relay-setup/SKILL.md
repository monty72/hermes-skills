---
name: smtp-relay-setup
description: "Set up programmatic email sending via SMTP relay — Gmail App Password + Python smtplib + msmtp for automated outbound email from Hermes."
version: 1.0.0
author: Agent
created_by: agent
metadata:
  hermes:
    tags: [email, smtp, gmail, relay, msmtp, python]
    related_skills: [cloudflare-dns-management, himalaya]
---

# SMTP Relay Setup — Hermes Bot Email

Set up Hermes to send emails programmatically using a Gmail App Password as the SMTP relay. This is the simplest approach for outbound email when you don't have a dedicated transactional email service.

## Architecture

```
Hermes → Python smtplib/msmtp → Gmail SMTP (smtp.gmail.com:587) → Recipient
                                                                       ↑
                                Cloudflare Email Routing (for incoming: hermes@domain → inbox)
```

Gmail SMTP is free and reliable. The App Password bypasses 2FA for automated access.

## Setup

### 1. Get a Gmail App Password

1. Enable **2-Step Verification** on the Gmail account at https://myaccount.google.com/security
2. Go to https://myaccount.google.com/apppasswords
3. Select **Mail** + **Other device** → name it "Hermes Bot"
4. Copy the 16-character password (format: `xxxx xxxx xxxx xxxx`)

### 2. Install msmtp (lightweight SMTP client)

```bash
sudo apt-get install -y msmtp msmtp-mta
```

### 3. Configure msmtp

Create `~/.msmtprc` with the actual credentials:

```
defaults
auth on
tls on
tls_starttls on
tls_trust_file /etc/ssl/certs/ca-certificates.crt

account gmail
host smtp.gmail.com
port 587
from your-email@gmail.com
user your-email@gmail.com
password xxxx xxxx xxxx xxxx

account default : gmail

logfile ~/.hermes/logs/msmtp.log
```

```bash
chmod 600 ~/.msmtprc
```

### 4. Python Email Script

Save as `~/scripts/hermes-email.py`:

```python
import smtplib, ssl
from email.mime.text import MIMEText

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDR = "your-email@gmail.com"
EMAIL_PASS = "xxxx xxxx xxxx xxxx"

def send_email(to, subject, body, sender=None):
    msg = MIMEText(body, _charset="utf-8")
    msg["From"] = sender or EMAIL_ADDR
    msg["To"] = to
    msg["Subject"] = subject
    envelope_from = EMAIL_ADDR  # Auth must match this

    ctx = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        server.starttls(context=ctx)
        server.login(EMAIL_ADDR, EMAIL_PASS)
        server.sendmail(envelope_from, [to], msg.as_string())
    return True
```

## Sending with Custom From Header

To send as `hermes@yourdomain.com` (from the Gmail account), set the `From` header and `Reply-To`:

```python
msg["From"] = "Hermes Bot <hermes@yourdomain.com>"
msg["Reply-To"] = "hermes@yourdomain.com"
```

**Note:** Gmail may rewrite the envelope From to the authenticated account. The `From` header in the email body will show your custom address, but some recipients' clients may show "sent via gmail.com". For full domain alignment (necessary for DKIM/SPF), use a dedicated SMTP relay service instead.

## Testing

```bash
python3 -c "
from email.mime.text import MIMEText
import smtplib, ssl

msg = MIMEText('Test from Hermes Bot')
msg['From'] = 'Hermes Bot <hermes@yourdomain.com>'
msg['To'] = 'recipient@example.com'
msg['Subject'] = 'Test'

ctx = ssl.create_default_context()
with smtplib.SMTP('smtp.gmail.com', 587, timeout=30) as s:
    s.starttls(context=ctx)
    s.login('your-email@gmail.com', 'xxxx xxxx xxxx xxxx')
    s.sendmail('your-email@gmail.com', ['recipient@example.com'], msg.as_string())
print('Sent!')
"
```

Also verify via msmtp:

```bash
echo "Test body" | msmtp --debug recipient@example.com
```

## Storing Credentials Securely

Store in the Hermes vault:

```bash
source ~/.hermes/.env.local 2>/dev/null
hermes-vault set EMAIL_ADDRESS "your-email@gmail.com"
hermes-vault set EMAIL_PASSWORD "xxxx xxxx xxxx xxxx"
```

For msmtp config, write the credentials directly (the file is 0600-protected). For Python scripts, read from vault at runtime:

```python
import subprocess
addr = subprocess.run(["hermes-vault","get","EMAIL_ADDRESS"], capture_output=True, text=True).stdout.strip()
pwd = subprocess.run(["hermes-vault","get","EMAIL_PASSWORD"], capture_output=True, text=True).stdout.strip()
```

## Custom Domain Integration (Cloudflare)

If using Cloudflare Email Routing with a custom domain:

1. Set up MX/SPF/DKIM records via Cloudflare dashboard (see `cloudflare-dns-management` skill)
2. Create a routing rule: `hermes@yourdomain.com` → forward to your Gmail
3. When sending, set the `From` header to `Hermes Bot <hermes@yourdomain.com>`
4. Recipients reply to `hermes@yourdomain.com` → Cloudflare routes to your Gmail

⚠️ **DNS setup order matters:** Do NOT add MX/SPF records manually via the DNS API before enabling Email Routing in the Cloudflare dashboard. The dashboard's "Add records and finish" button auto-creates them with the exact format Cloudflare expects. Manual records cause "DNS misconfigured" errors. If you added them manually, delete them, then use the dashboard button.

## Pitfalls

- **Gmail SMTP timeout:** The first connection can be slow. Use `timeout=60` for initial sends and debug mode (`server.set_debuglevel(1)`) to diagnose.
- **App Password format:** Include spaces as shown by Google (`xxxx xxxx xxxx xxxx`). Both spaced and unspaced forms work.
- **msmtp config vars:** msmtp does NOT expand shell environment variables (`${EMAIL_ADDRESS}`). Write the actual values.
- **300s terminal timeout:** If sending via the `terminal` tool, the default timeout may be exceeded. Use `timeout=120` or let Python handle the full send inside `execute_code`.
- **Gmail rewrites From:** For strict SPF/DKIM alignment, Gmail SMTP rewrites the envelope sender. The visible `From:` header is preserved but some mail filters may flag it.
- **Google signup blocks bots:** Creating a new Gmail account from a headless browser will be blocked by Google's anti-bot detection. Use an existing account with App Password instead.
