---
name: managed-agent-service
description: "Provision, configure, and manage Hermes Agent / OpenClaw instances as a managed service for customers."
version: 2.0.0
author: Matt Hogarth
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [managed-agent, provisioning, saas, hosting, devops, proxmox, zero-touch]
    related_skills: [hermes-agent, planning, writing-plans]
---

# Hermes Managed Agent Service — Operations Guide

## Overview

Full toolkit at `~/managed-agent/` for provisioning Hermes Agent instances as a managed service. **Your Proxmox is the primary platform** — LXC containers auto-created, bots pre-created from pools, zero customer input needed.

## Zero-Touch Provisioning Flow

The key insight: **You pre-create bots (Telegram @BotFather / Discord API) into pools, then provisioning is fully automated.**

### Pre-work (one-time setup)
```bash
cd ~/managed-agent

# 1. Set up your LLM key pool (so customers don't need one)
# Edit: configs/llm-key-pool.json → set your OpenRouter key

# 2. Create some Telegram bots (do this once, they sit in the pool)
./scripts/manage-agent.py bots telegram create
# Follow the interactive prompt — paste token from @BotFather

# 3. Authenticate Discord API (one time)
./scripts/manage-agent.py bots discord create test-bot "Test Bot"
# If first run, it'll guide you through auth

# 4. Create a few Discord bots for the pool
./scripts/manage-agent.py bots discord create acme-bot "Acme Corp Bot"
```

### Provision a customer (one command, zero touch)
```bash
# Solo tier — no bots needed, fully automated
./scripts/manage-agent.py oneshot dev-bob solo

# Starter — Telegram, on your Proxmox
./scripts/manage-agent.py oneshot acme-corp starter \
  --telegram

# Pro — Telegram + Discord, more resources
./scripts/manage-agent.py oneshot bigcorp pro \
  --telegram --discord \
  --proxmox-cores 2 --proxmox-memory 4096
```

### What happens automatically
1. Bot pulled from pool, assigned to customer
2. **Onboarding skill installed** — customer provides own LLM key via chat
3. LXC created on your Proxmox (CT ID auto-assigned)
4. Hermes Agent installed with free placeholder model
5. config.yaml + .env written with bot tokens (no LLM key from you)
6. Gateway installed as systemd service
7. Health monitoring set up (every 30 min)
8. Summary report generated

### Customer experience
The agent starts with a free placeholder model (DeepSeek).
When the customer messages their bot, the onboarding wizard guides them:

```                  
You: "Here's @AcmeSupportBot — message it to get started."

Customer: "Hey, I'm ready to set up."
Agent:    "👋 Welcome! I need an API key to process your requests.
           Paste your OpenRouter/Anthropic/OpenAI key here."
Customer: [pastes sk-or-v1-...]
Agent:    "✅ Key saved! Your agent is now fully operational."
```

**You never touch the customer's API key.**
To pre-configure a key, pass `--no-onboarding`:
```bash
./manage-agent.py oneshot acme-corp starter --telegram --no-onboarding
```

## Files

- `scripts/oneshot-provision.py` — 🚀 **Main entry: one command, zero touch**
- `scripts/provision-agent.sh` — Core provisioning (called by oneshot)
- `scripts/deprovision-agent.sh` — Cleanup
- `scripts/check-health.sh` — Health monitor
- `scripts/manage-agent.py` — Unified CLI
- `scripts/create-telegram-bot.py` — Telegram bot pool manager
- `scripts/create-discord-bot.py` — Discord bot pool manager
- `configs/telegram-bot-pool.json` — Pre-created Telegram bots
- `configs/discord-bot-pool.json` — Pre-created Discord bots
- `configs/llm-key-pool.json` — Your LLM API keys (shared or per-customer)
- `configs/solo.yaml` → `enterprise.yaml` — Config templates

## Hosting Models

| Mode | Flag | What happens | Best for |
|------|------|-------------|----------|
| **Your Proxmox** | (default) | LXC auto-created | Primary — full control, highest margin |
| **Customer hardware** | `--customer <host>` | SSH into their machine | Clients with data compliance |
| **DigitalOcean** | `--digitalocean` | Droplet created | Proxmox full |
| **Hetzner** | `--hetzner` | CX server created | EU data residency |

## Service Tiers

| Tier | Price | Bots | Platforms | Cron | Margin |
|------|-------|------|-----------|------|--------|
| Solo | £49/mo | None | Terminal only | 1 | 95%+ |
| Starter | £149/mo | 1 bot | Telegram + Email | 5 | 90%+ |
| Pro | £349/mo | 2 bots | 4 platforms | 20 | 85%+ |
| Enterprise | £999+/mo | Custom | All | Unlimited | TBD |

## Bot Pool Management

### Telegram
```bash
./scripts/manage-agent.py bots telegram list     # See available bots
./scripts/manage-agent.py bots telegram create    # Create one interactively (pastes token)
```

### Discord — FULLY AUTOMATED
```bash
# One-time auth (your Discord user token)
./scripts/manage-agent.py bots discord login

# Pre-create bots for pool (app + bot, no server)
./scripts/manage-agent.py bots discord create name "Display Name"

# Full setup: creates app + bot + SERVER + CHANNELS + INVITE
./scripts/manage-agent.py bots discord setup acme-corp
# → Creates: "Acme Corp Bot" app
# → Creates: "Acme Corp HQ" server
# → Creates: #welcome, #chat-with-agent, #agent-updates, voice-chat
# → Adds bot to server
# → Returns invite link
```

### What --discord does during `oneshot provision`

1. Creates a Discord application (e.g. "Acme Corp Bot")
2. Creates a bot user under that application
3. Creates a **Discord server** (e.g. "Acme Corp HQ")
4. Adds the bot to the server automatically
5. Creates channels: #welcome, #chat-with-agent, #agent-updates, voice-chat
6. Generates an invite link

**You hand the customer a server invite link — the bot is already in it.**
They just click to join.

### Deprovisioning

```bash
./scripts/manage-agent.py deprovision <name>
```
Releases all bots back to pools, destroys the LXC.
Note: Discord servers created via the API are owned by YOUR Discord account, so you can delete them manually after deprovision.

## Deprovisioning

```bash
./scripts/manage-agent.py deprovision <name>
```

This releases all bots back to pools and destroys the LXC.
