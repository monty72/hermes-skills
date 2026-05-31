#!/usr/bin/env python3
"""
Watchdog: Auto-maintain a pinned master index in a Discord #notes channel.

Pattern: Users drop links/references in the channel. This script periodically
fetches new messages, merges any new URLs into the pinned index, and patches
it. Designed for no-agent cron mode (no_agent: true).

Usage in cron:
  cronjob action=create name=notes-index-updater schedule="every 3h" \
    no_agent=true script=notes-index-watchdog.py
"""
from dotenv import load_dotenv
import os, json, re, urllib.request, sys

load_dotenv(os.path.expanduser('~/.hermes/.env'))
TOKEN = os.environ.get('DISCORD_BOT_TOKEN', '')

# ── CONFIGURE THESE ──────────────────────────────────────────
NOTES_CHANNEL = '0000000000000000000'  # Channel ID
PINNED_MSG_ID = '0000000000000000000'  # ID of the pinned master message
GUILD_ID      = '0000000000000000000'  # Server ID
# ─────────────────────────────────────────────────────────────

# Category labels → emoji
CATEGORIES = {
    'GitHub Repositories': '\U0001F4E6',
    'Websites & Domains': '\U0001F310',
    'Self-Hosted Services': '\U0001F5A5',
    'Energy Stack': '\u26A1',
    'Tooling': '\U0001F527',
    'Other Links': '\U0001F517',
}
CATEGORY_ORDER = list(CATEGORIES.keys())

def classify_url(url: str) -> str:
    if 'github.com' in url:       return 'GitHub Repositories'
    if 'montygroup' in url:       return 'Websites & Domains'
    if re.search(r'192\.168\.', url): return 'Self-Hosted Services'
    if re.search(r'netzero|octopus|energy|powerwall', url): return 'Energy Stack'
    return 'Other Links'

opener = urllib.request.build_opener()
opener.addheaders = [('User-Agent', 'DiscordBot (HermesAgent, 1.0)'),
                     ('Authorization', f'Bot {TOKEN}')]
urllib.request.install_opener(opener)

def api(method, path, data=None):
    req = urllib.request.Request(
        f'https://discord.com/api/v10{path}',
        data=json.dumps(data).encode() if data else None,
        headers={'Content-Type': 'application/json'} if data else {},
        method=method,
    )
    with urllib.request.urlopen(req) as resp:
        body = resp.read()
        return json.loads(body) if body else {}

# 1. Get current pinned message
current = api('GET', f'/channels/{NOTES_CHANNEL}/messages/{PINNED_MSG_ID}')
if not current or 'content' not in current:
    print("Cannot read pinned message — check PINNED_MSG_ID and permissions")
    sys.exit(1)

base = current['content']

# 2. Fetch recent user messages (non-bot, non-pinned)
msgs = api('GET', f'/channels/{NOTES_CHANNEL}/messages?limit=100')
new_links = {}
new_drops = 0
for msg in msgs:
    if msg.get('id') == PINNED_MSG_ID or msg.get('author', {}).get('bot'):
        continue
    new_drops += 1
    text = msg.get('content', '')
    for url in re.findall(r'https?://\S+', text):
        idx = text.find(url)
        label = text[max(0, idx - 50):idx].strip().rstrip('\u2022-*[]():, ')
        new_links[url] = label if label else url

if not new_links:
    sys.exit(0)  # silent — nothing new

# 3. Filter to genuinely missing links
missing = {u: l for u, l in new_links.items() if u not in base}
if not missing:
    sys.exit(0)

# 4. Group by category and append to each section
append = {}
for url, label in missing.items():
    cat = classify_url(url)
    entry = f"\u2022 {label}: {url}" if label != url else f"\u2022 {url}"
    append.setdefault(cat, []).append(entry)

lines = base.split('\n')
for cat, entries in sorted(append.items(), key=lambda x: CATEGORY_ORDER.index(x[0]) if x[0] in CATEGORY_ORDER else 99):
    # Find the section header
    marker = f'**{CATEGORIES.get(cat, "")} {cat}**' if cat in CATEGORIES else f'**{cat}**'
    found = None
    for i, line in enumerate(lines):
        if marker in line:
            found = i
            break
    if found is not None:
        # Insert entries after the section header, before the next section
        insert_at = found + 1
        for j in range(found + 1, len(lines)):
            if lines[j].startswith('**') and lines[j] != marker:
                insert_at = j
                break
            if j == len(lines) - 1:
                insert_at = j + 1
        for entry in sorted(set(entries)):
            if entry not in base:
                lines.insert(insert_at, entry)
                insert_at += 1
    else:
        # New section — append at end
        lines.append(f"\n**{CATEGORIES.get(cat, '')} {cat}**")
        for entry in sorted(set(entries)):
            lines.append(entry)

# 5. Refresh the timestamp line
for i, line in enumerate(lines):
    if 'Auto-synced' in line or 'Last updated' in line:
        lines[i] = f"Auto-synced from {new_drops} new drops in #notes"
        break

new_content = '\n'.join(lines)
result = api('PATCH', f'/channels/{NOTES_CHANNEL}/messages/{PINNED_MSG_ID}',
             {'content': new_content})
if isinstance(result, dict) and 'id' in result:
    print(f"Updated pinned index: +{len(missing)} link(s) from {new_drops} drop(s)")
    for cat, entries in append.items():
        print(f"  {cat}: +{len(entries)}")
