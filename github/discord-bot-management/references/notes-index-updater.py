#!/usr/bin/env python3
"""
notes-index-updater: Merges user-link drops into a pinned master link directory.
Designed for no-agent cron use (cronjob action=create, no_agent=true).

Expects ~/.hermes/.env to have DISCORD_BOT_TOKEN set.
"""
from dotenv import load_dotenv
import os, json, re, urllib.request, sys

load_dotenv(os.path.expanduser('~/.hermes/.env'))
TOKEN = os.environ.get('DISCORD_BOT_TOKEN', '')
NOTES_CHANNEL = '<CHANNEL_ID>'     # Replace with #notes channel ID
PINNED_MSG_ID = '<MESSAGE_ID>'     # Replace with pinned message ID

opener = urllib.request.build_opener()
opener.addheaders = [('User-Agent', 'DiscordBot (NotesIndexUpdater, 1.0)'), ('Authorization', f'Bot {TOKEN}')]
urllib.request.install_opener(opener)

def api(method, path, data=None):
    req = urllib.request.Request(
        f'https://discord.com/api/v10{path}',
        data=json.dumps(data).encode() if data else None,
        headers={'Content-Type': 'application/json'} if data else {},
        method=method
    )
    with urllib.request.urlopen(req) as r:
        body = r.read()
        return json.loads(body) if body else {}

# 1. Read current pinned message
current = api('GET', f'/channels/{NOTES_CHANNEL}/messages/{PINNED_MSG_ID}')
if not current or 'content' not in current:
    print("Cannot read pinned message", file=sys.stderr)
    sys.exit(1)
base_content = current['content']

# 2. Collect new user-dropped links
msgs = api('GET', f'/channels/{NOTES_CHANNEL}/messages?limit=100')
new_links = {}
for msg in msgs:
    if msg.get('id') == PINNED_MSG_ID or msg.get('author', {}).get('bot', False):
        continue
    c = msg.get('content', '')
    for url in re.findall(r'https?://\S+', c):
        idx = c.find(url)
        label = c[max(0, idx-50):idx].strip().rstrip('\u2022-*[]():, ')
        new_links[url] = label if label else url

# 3. Filter to URLs NOT already in the pinned message
missing = {u: l for u, l in new_links.items() if u not in base_content}
if not missing:
    sys.exit(0)

# 4. Categorize new links
EMOJI_MAP = {
    'GitHub Repositories': '\U0001F4E6',
    'Websites & Domains': '\U0001F310',
    'Self-Hosted Services': '\U0001F5A5',
    'Energy Stack': '\u26A1',
    'Tooling': '\U0001F527',
    'Other Links': '\U0001F517',
}

def categorize(url):
    if 'github.com' in url: return 'GitHub Repositories'
    if 'montygroup' in url: return 'Websites & Domains'
    if re.search(r'192\.168\.|homeassistant', url): return 'Self-Hosted Services'
    if re.search(r'netzero|octopus|energy|powerwall', url): return 'Energy Stack'
    return 'Other Links'

cats = {}
for url, label in missing.items():
    cat = categorize(url)
    entry = f"\u2022 {label}: {url}" if label != url else f"\u2022 {url}"
    cats.setdefault(cat, []).append(entry)

# 5. Append entries to the pinned message sections
lines = base_content.split('\n')
for section, entries in cats.items():
    marker = f"**{EMOJI_MAP.get(section, '\U0001F517')} {section}**"
    if marker in base_content:
        inserted = False
        new_lines = []
        for line in lines:
            new_lines.append(line)
            if marker in line and '**' in line:
                inserted = True
                for entry in sorted(set(entries)):
                    if entry not in base_content:
                        new_lines.append(entry)
        lines = new_lines
    else:
        lines.append(f"\n{marker}")
        for entry in sorted(entries):
            lines.append(entry)

# Update timestamp
lines = [l for l in lines if 'Auto-synced' not in l and 'Last updated' not in l]
lines.append("\n---\n*Auto-synced from #notes*")

# 6. Patch the pinned message
new_content = '\n'.join(lines)
result = api('PATCH', f'/channels/{NOTES_CHANNEL}/messages/{PINNED_MSG_ID}', {'content': new_content})
if result.get('id'):
    print(f"Merged {len(missing)} new links")
else:
    print("Update failed", file=sys.stderr)
