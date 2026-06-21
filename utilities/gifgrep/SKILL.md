---
name: gifgrep
description: "Search GIF providers (Tenor/Giphy) with CLI/TUI — search, download, extract stills/sheets. Also covers Tenor API via curl as a light fallback."
homepage: https://gifgrep.com
metadata: {"openclaw":{"emoji":"🧲","requires":{"bins":["gifgrep"]},"install":[{"id":"brew","kind":"brew","formula":"steipete/tap/gifgrep","bins":["gifgrep"],"label":"Install gifgrep (brew)"},{"id":"go","kind":"go","module":"github.com/steipete/gifgrep/cmd/gifgrep@latest","bins":["gifgrep"],"label":"Install gifgrep (go)"}]}}
---

# GIF Search & Discovery

Search GIF providers (Tenor/Giphy), download results, extract stills/sheets. Two approaches:

1. **gifgrep CLI** — TUI/CLI for search, preview, download, still extraction (preferred)
2. **Tenor API via curl** — lightweight fallback (no extra tool needed)

## gifgrep (Preferred)

Use `gifgrep` to search GIF providers (Tenor/Giphy), browse in a TUI, download results, and extract stills or sheets.

GIF-Grab (gifgrep workflow)
- Search → preview → download → extract (still/sheet) for fast review and sharing.

Quick start
- `gifgrep cats --max 5`
- `gifgrep cats --format url | head -n 5`
- `gifgrep search --json cats | jq '.[0].url'`
- `gifgrep tui "office handshake"`
- `gifgrep cats --download --max 1 --format url`

TUI + previews
- TUI: `gifgrep tui "query"`
- CLI still previews: `--thumbs` (Kitty/Ghostty only; still frame)

Download + reveal
- `--download` saves to `~/Downloads`
- `--reveal` shows the last download in Finder

Stills + sheets
- `gifgrep still ./clip.gif --at 1.5s -o still.png`
- `gifgrep sheet ./clip.gif --frames 9 --cols 3 -o sheet.png`
- Sheets = single PNG grid of sampled frames (great for quick review, docs, PRs, chat).
- Tune: `--frames` (count), `--cols` (grid width), `--padding` (spacing).

Providers
- `--source auto|tenor|giphy`
- `GIPHY_API_KEY` required for `--source giphy`
- `TENOR_API_KEY` optional (Tenor demo key used if unset)

Output
- `--json` prints an array of results (`id`, `title`, `url`, `preview_url`, `tags`, `width`, `height`)
- `--format` for pipe-friendly fields (e.g., `url`)

Environment tweaks
- `GIFGREP_SOFTWARE_ANIM=1` to force software animation
- `GIFGREP_CELL_ASPECT=0.5` to tweak preview geometry

## Tenor API via curl (Lightweight Fallback)

No gifgrep? Use the Tenor API directly with curl:

```bash
# Requires TENOR_API_KEY in ~/.hermes/.env (free: https://developers.google.com/tenor/guides/quickstart)

# Search
curl -s "https://tenor.googleapis.com/v2/search?q=thumbs+up&limit=5&key=${TENOR_API_KEY}" | jq -r '.results[].media_formats.gif.url'

# Download top result
URL=$(curl -s "https://tenor.googleapis.com/v2/search?q=celebration&limit=1&key=${TENOR_API_KEY}" | jq -r '.results[0].media_formats.gif.url')
curl -sL "$URL" -o celebration.gif

# Get metadata
curl -s "https://tenor.googleapis.com/v2/search?q=cat&limit=3&key=${TENOR_API_KEY}" | jq '.results[] | {title, url: .media_formats.gif.url}'
```

Parameters: `q` (query), `limit` (1-50), `media_filter` (gif/tinygif/mp4), `contentfilter` (off/low/medium/high), `locale`

Media formats: `gif` (full), `tinygif` (preview), `mp4` (video), `webm`
