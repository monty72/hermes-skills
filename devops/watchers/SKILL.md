---
name: watchers
description: "Poll RSS, JSON APIs, and GitHub with watermark dedup."
version: 1.0.0
---

# Watchers

## Overview

Poll RSS feeds, JSON APIs, and GitHub events with watermark dedup to avoid re-processing.

## Watermark Pattern

```python
import json, os, time, requests

WATERMARK_FILE = ".watcher_watermark.json"

def load_watermark():
    if os.path.exists(WATERMARK_FILE):
        with open(WATERMARK_FILE) as f:
            return json.load(f)
    return {}

def save_watermark(wm):
    with open(WATERMARK_FILE, 'w') as f:
        json.dump(wm, f, indent=2)
```

## RSS Polling

```python
import feedparser

def poll_rss(url, watermark=None):
    feed = feedparser.parse(url)
    new_items = []
    for entry in feed.entries:
        if watermark and entry.id == watermark:
            break
        new_items.append(entry)
    new_items.reverse()  # oldest first
    if new_items:
        watermark = new_items[-1].id
    return new_items, watermark
```

## JSON API Polling

```python
def poll_json(url, watermark_key="id", watermark=None):
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    new_items = []
    for item in data:
        if watermark and item.get(watermark_key) == watermark:
            break
        new_items.append(item)
    new_items.reverse()
    if new_items:
        watermark = new_items[-1].get(watermark_key)
    return new_items, watermark
```

## GitHub Polling

```python
def poll_github_releases(owner, repo, watermark=None):
    url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    resp = requests.get(url)
    resp.raise_for_status()
    releases = resp.json()
    new_items = []
    for r in releases:
        if watermark and r['id'] == watermark:
            break
        new_items.append(r)
    new_items.reverse()
    if new_items:
        watermark = new_items[-1]['id']
    return new_items, watermark
```

## Flask API: RSS-Scraping Endpoint

To add a live-deals endpoint to an existing Flask server (e.g. for a hardware guide page), see `references/flask-rss-endpoint.md`. Pattern:

1. Add a `fetch_<topic>_deals()` function that parses RSS XML with keyword filter
2. Add a route handler in `do_GET()` that returns JSON
3. Frontend `<script>` fetches from `/api/<topic>-deals` — proxied through the backend to avoid CORS

## Cron Job Integration

```python
# In a cron job script:
watcher = load_watermark()
items, new_wm = poll_rss("https://example.com/feed.xml", watcher.get("rss_feed"))
if items:
    for item in items:
        # process item
        print(f"New: {item.title} - {item.link}")
    watcher["rss_feed"] = new_wm
    save_watermark(watcher)
```
