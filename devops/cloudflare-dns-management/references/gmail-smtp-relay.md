# Gmail SMTP Relay for Custom Domains

Use Gmail's SMTP with an App Password to send emails **from** a Cloudflare-managed custom domain (e.g. `hermes@montygroup.uk`) **through** a Gmail account's outbound infrastructure. Gmail's SMTP allows setting a custom `MAIL FROM` envelope and `From:` header — the recipient sees the custom domain, not the Gmail address.

## Prerequisites

- Gmail account with **2-Step Verification** enabled
- **App Password** generated for that account (16 characters, no spaces)
- Custom domain with Cloudflare Email Routing / MX records set up (see `email-dns-records.md`)

## Generate an App Password

1. Go to https://myaccount.google.com/apppasswords
2. Select **Mail** + **Other** → name it (e.g. "Hermes Bot")
3. Copy the 16-character password (format: `xxxx xxxx xxxx xxxx` or `xxxxxxxxxxxxxxxx`)

## Install SMTP Client

```bash
sudo apt-get install -y msmtp msmtp-mta
```

## Configure msmtp

```toml
# ~/.msmtprc
defaults
auth on
tls on
tls_starttls on
tls_trust_file /etc/ssl/certs/ca-certificates.crt

account gmail
host smtp.gmail.com
port 587
from hermes@montygroup.uk              # ← custom domain in From header
user your-gmail@gmail.com              # ← Gmail address for auth
password xxxx xxxx xxxx xxxx            # ← App Password

account default : gmail
logfile ~/.hermes/logs/msmtp.log
```

```bash
chmod 600 ~/.msmtprc
```

## Python smtplib Script

Stdlib-only (no pip deps). The key trick: `server.sendmail(custom_domain, ...)` sets the SMTP envelope sender independently of the authenticated Gmail user.

```python
import smtplib, ssl, os
from email.mime.text import MIMEText

def send_email(to, subject, body, sender="hermes@montygroup.uk"):
    addr = os.environ.get("EMAIL_ADDRESS", "your-gmail@gmail.com")
    pwd = os.environ.get("EMAIL_PASSWORD", "")
    if not pwd:
        raise ValueError("EMAIL_PASSWORD not set")

    msg = MIMEText(body, _charset="utf-8")
    msg["From"] = f"Hermes Bot <{sender}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg["Reply-To"] = sender

    ctx = ssl.create_default_context()
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=60) as server:
        server.starttls(context=ctx)
        server.login(addr, pwd)
        server.sendmail(sender, [to], msg.as_string())
```

## Verify Delivery

```bash
# From terminal
echo "Test from msmtp" | msmtp recipient@example.com

# From Python
python3 -c "
import smtplib, ssl
from email.mime.text import MIMEText
msg = MIMEText('Test')
msg['From'] = 'Test <hermes@montygroup.uk>'
msg['To'] = 'recipient@example.com'
msg['Subject'] = 'Test'
ctx = ssl.create_default_context()
with smtplib.SMTP('smtp.gmail.com', 587, timeout=60) as s:
    s.starttls(context=ctx)
    s.login('your-gmail@gmail.com', 'xxxx xxxx xxxx xxxx')
    s.sendmail('hermes@montygroup.uk', ['recipient@example.com'], msg.as_string())
print('Sent!')
"
```

## Pitfalls

- **App Passwords require 2FA** enabled on the Gmail account. Without 2FA, you cannot generate App Passwords.
- **Custom MAIL FROM is NOT verified by Gmail** — Gmail relays whatever `MAIL FROM` you set. But the recipient's email provider may apply SPF/DKIM/DMARC checks. Gmail's SPF (`include:_spf.google.com`) is NOT covered by your domain's Cloudflare SPF record. For strict DMARC policies, either: (a) add Gmail's SPF include to your domain's TXT record, or (b) use Gmail's "Send mail as" verification flow in Gmail settings to verify domain ownership.
- **Rate limits** — Gmail SMTP: ~500 recipients/day, ~2,000 messages/day. For bulk, use a transactional email service.
- **msmtp uses literal values**, not shell env vars. Write the password directly in `.msmtprc` (with `chmod 600`), or use a `passwordeval` command to fetch from the vault.
- **Custom domain incoming email** requires Cloudflare Email Routing rules configured in the dashboard (see `email-dns-records.md`).
