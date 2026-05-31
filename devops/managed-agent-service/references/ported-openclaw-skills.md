# Ported OpenClaw Skills (2026-05-26)

31 skills imported from [seedprod/openclaw-prompts-and-skills](https://github.com/seedprod/openclaw-prompts-and-skills) (89 ⭐, 21 forks).

## Source Repo Structure

```
.claude/skills/
├── <skill-name>/
│   ├── SKILL.md          # Required — YAML frontmatter + markdown body
│   └── scripts/          # Optional — supporting scripts
```

Each SKILL.md has YAML frontmatter with `name`, `description`, and optionally `homepage` + `metadata.openclaw` (emoji, requires, install). Format is compatible with Hermes Agent's `~/.hermes/skills/` — no conversion needed.

## Ported Skills by Category

### utilities/ (12)
weather, summarize, model-usage, session-logs, skill-creator, gifgrep, clawhub, mcporter, local-places, goplaces, food-order, ordercli

### media/ (13)
video-frames, sag (ElevenLabs TTS), sherpa-onnx-tts, openai-image-gen, openai-whisper, camsnap (RTSP cameras), spotify-player, blucli (BluOS)

### social-media/ (7)
slack, discord, bird (Twitter/X), wacli (WhatsApp), voice-call, gemini

### software-development/ (3)
github, tmux

### productivity/ (1)
trello

### security/ (1)
1password

### creative/ (1)
nano-banana-pro

## Linux Compatibility Notes

The full source repo has 52 skills. These 31 were selected as Linux-compatible. Excluded skills were:
- **macOS-only:** imsg, bluebubbles, bear-notes, things-mac, peekaboo
- **Too environment-specific:** eightctl (Eight Sleep), oracle (DB), ordercli/food-order (Foodora — author-specific)
- **Already owned:** himalaya, nano-pdf, notion, obsidian, openhue, songsee, blogwatcher (we had equivalents)

## Skills Not Ported (Already Owned)

The following existed in `~/.hermes/skills/` already:
himalaya, nano-pdf, notion, obsidian, openhue, songsee, blogwatcher, apple-notes, apple-reminders

## Post-Port Stats

- Before: 127 SKILL.md files, ~16MB
- After: 158 SKILL.md files, ~17MB
- Backup: `~/skill-backup-20260526-230855/`

## Using Ported Skills

Skills trigger automatically when the relevant topic or request matches their `description` field in the YAML frontmatter. No manual activation needed. For example:
- "What's the weather in London?" → loads `weather` skill
- "Play some jazz on Spotify" → loads `spotify-player` skill
- "Send a message to #general on Slack" → loads `slack` skill
