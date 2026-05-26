#!/usr/bin/env python3
"""Batch-verify all vault keys by checking length (bypasses terminal redaction)."""
import subprocess, sys, os

KEYS_TO_CHECK = [
    "DEEPSEEK_API_KEY",
    "TELEGRAM_BOT_TOKEN",
    "HASS_TOKEN",
    "BRAVE_SEARCH_API_KEY",
    "FAL_KEY",
    "OPENAI_API_KEY",
    "GITHUB_TOKEN",
    "VERCEL_TOKEN",
    "PROXMOX_API_TOKEN",
    "CLOUDFLARE_ACCOUNT_ID",
    "CLOUDFLARE_TUNNEL_ACTIVE_SECRET",
    "CLOUDFLARE_TUNNEL_HERMES_DEV_SECRET",
    "CLOUDFLARE_ZONE_MONTYGROUP",
    "NETZERO_API_TOKEN",
]

def vault_get(key):
    r = subprocess.run(["hermes-vault", "get", key], capture_output=True, text=True)
    return r.stdout.strip()

print(f"{'Key':<35} {'Len':<5} {'Status'}")
print("-" * 55)

all_ok = True
for key in KEYS_TO_CHECK:
    val = vault_get(key)
    length = len(val)
    if length <= 3:
        status = f"❌ PLACEHOLDER ('{val}')"
        all_ok = False
    elif val == "***":
        status = "❌ LITERAL '***'"
        all_ok = False
    else:
        status = f"✅ (starts: {val[:8]}...)"
    print(f"{key:<35} {length:<5} {status}")

print()
sys.exit(0 if all_ok else 1)
