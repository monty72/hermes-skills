---
name: granola
title: Granola Meeting Notes
description: Query and retrieve meeting notes, transcripts, and AI summaries from Granola.ai via the Granola REST API.
version: 1.0.0
author: Hermes Agent
---

# Granola Skill

Query and retrieve meeting notes from Granola.ai using the Granola REST API. Requires a Granola API key (starts with `grn_`).

## Prerequisites

- A Granola account with meeting notes
- A Granola API key with appropriate access scopes (Personal and/or Public notes)

### Getting an API Key

1. Open the Granola desktop app
2. Settings → Connectors → API keys
3. Click **Create new key**, choose access scopes, click **Generate API Key**
4. Save the key (starts with `grn_...`)

Store in the vault:
```bash
hermes vault set GRANOLA_API_KEY "grn_..."
```

Or set in `.env`:
```
GRANOLA_API_KEY=grn_...
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/notes` | GET | List notes with pagination, date filters, folder filter |
| `/v1/notes/{note_id}` | GET | Get single note with optional transcript |
| `/v1/folders` | GET | List folders with hierarchy |

**Base URL:** `https://public-api.granola.ai`

**Auth:** Bearer token in `Authorization` header

## Usage

The agent can use the Granola API via the terminal tool with curl. All requests need the API key.

### List Recent Notes

```bash
curl -s -H "Authorization: Bearer $(hermes vault get GRANOLA_API_KEY)" \
  "https://public-api.granola.ai/v1/notes?created_after=$(date -u -v-7d +%Y-%m-%dT%H:%M:%SZ)&page_size=10"
```

### Get a Specific Note with Transcript

```bash
curl -s -H "Authorization: Bearer $(hermes vault get GRANOLA_API_KEY)" \
  "https://public-api.granola.ai/v1/notes/not_1d3tmYTlCICgjy?include=transcript"
```

### List Folders

```bash
curl -s -H "Authorization: Bearer $(hermes vault get GRANOLA_API_KEY)" \
  "https://public-api.granola.ai/v1/folders?page_size=30"
```

### Paginate Through Results

```bash
curl -s -H "Authorization: Bearer $(hermes vault get GRANOLA_API_KEY)" \
  "https://public-api.granola.ai/v1/notes?cursor=eyJjcmVkZW50aWFsfQ==&page_size=10"
```

## Example Prompts

- "What meetings did I have last week?" → calls `GET /v1/notes?created_after=<last_week>`
- "Find notes about the platform architecture review" → lists notes, searches titles/summaries
- "Get the action items from the quarterly review" → gets the note with transcript, reads summary
- "Show me notes from the Engineering folder" → lists folders, then notes filtered by `folder_id`
- "What did we decide about the API design in that meeting with Sarah?" → searches notes, gets transcript

## Rate Limits

- Burst: 25 requests
- Window: 5 seconds
- Sustained: 5 req/s (300/min)
- 429 Too Many Requests on exceed

## Note on Notes

- Only notes with **AI summary and transcript** are returned via the API
- Notes still processing or never summarized return 404 on Get Note
- Free plan: only your own notes from last 30 days
- Paid plan: shared notes + full transcripts + folder access

## Implementation Note

This skill uses direct curl calls via the terminal tool rather than a custom Python tool. The pattern is:

```bash
API_KEY="$(hermes vault get GRANOLA_API_KEY 2>/dev/null || echo "$GRANOLA_API_KEY")"
curl -s -H "Authorization: Bearer $API_KEY" "https://public-api.granola.ai/v1/notes?page_size=5"
```

The agent should use `execute_code` for multi-step workflows (list notes → pick one → get transcript → summarize).
