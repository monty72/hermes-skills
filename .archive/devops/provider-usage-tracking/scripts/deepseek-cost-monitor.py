#!/usr/bin/env python3
"""
DeepSeek cost monitor — checks balance, tracks daily spend, detects spend spikes.
Designed as a no-agent cron script: runs on schedule, outputs formatted report to stdout.
"""
import json, os, subprocess, sys, urllib.request
from datetime import datetime, timedelta
from pathlib import Path

HISTORY_FILE = Path.home() / ".hermes" / "data" / "deepseek-history.json"
CONFIG_FILE = Path.home() / ".hermes" / "config.yaml"
VAULT_BIN = Path.home() / ".local" / "bin" / "hermes-vault"
ENV_LOCAL = Path.home() / ".hermes" / ".env.local"


def get_api_key():
    """Retrieve DeepSeek API key from vault."""
    env = os.environ.copy()
    env["PATH"] = f"{env.get('PATH', '')}:{Path.home() / '.local' / 'bin'}"
    if ENV_LOCAL.exists():
        for line in ENV_LOCAL.read_text().splitlines():
            if line.startswith("export "):
                parts = line[7:].strip().split("=", 1)
                if len(parts) == 2:
                    k, v = parts
                    env[k] = v.strip().strip("'\"")
    r = subprocess.run([str(VAULT_BIN), "get", "DEEPSEEK_API_KEY"],
                       capture_output=True, text=True, env=env, timeout=10)
    if r.returncode != 0:
        print(f"⚠️  Failed to get API key: {r.stderr.strip()}")
        sys.exit(1)
    return r.stdout.strip()


def get_balance(api_key):
    try:
        req = urllib.request.Request(
            "https://api.deepseek.com/user/balance",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        bi = data.get("balance_infos", [{}])[0]
        return float(bi.get("total_balance", "0").split()[0])
    except Exception as e:
        print(f"⚠️  Balance check failed: {e}")
        return None


def load_history():
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text())
    return {"records": {}, "last_balance": None, "last_date": None}


def save_history(history):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(history, indent=2, sort_keys=True))
    os.chmod(str(HISTORY_FILE), 0o600)


def get_model():
    if not CONFIG_FILE.exists():
        return "unknown"
    import yaml
    with open(CONFIG_FILE) as f:
        c = yaml.safe_load(f)
    return c.get("model", {}).get("default", "unknown")


def set_fallback(val):
    import yaml
    with open(CONFIG_FILE) as f:
        c = yaml.safe_load(f)
    c["fallback_providers"] = val
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(c, f, default_flow_style=False)


def main():
    api_key = get_api_key()
    balance = get_balance(api_key)
    if balance is None:
        return

    today = datetime.now().strftime("%Y-%m-%d")
    history = load_history()

    daily_spend = 0.0
    last_bal = history.get("last_balance")
    last_date = history.get("last_date")

    if last_bal is not None and last_date and last_date != today:
        daily_spend = max(0.0, last_bal - balance)
        if last_date not in history["records"]:
            history["records"][last_date] = round(daily_spend, 4)

    history["last_balance"] = balance
    history["last_date"] = today
    if today not in history["records"]:
        history["records"][today] = 0.0

    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    history["records"] = {k: v for k, v in history["records"].items() if k >= cutoff}
    save_history(history)

    records = history["records"]
    all_vals = [records[d] for d in sorted(records.keys()) if d != today]
    recent_7 = all_vals[-7:] if len(all_vals) >= 7 else all_vals
    avg_7 = sum(recent_7) / max(len(recent_7), 1) if recent_7 else 0.0
    total_30 = sum(all_vals)

    spike = False
    spike_factor = 0.0
    if len(recent_7) >= 3 and daily_spend > avg_7 * 2 and avg_7 > 0.005:
        spike = True
        spike_factor = round(daily_spend / avg_7, 1)

    model = get_model()

    print(f"🤖 **DeepSeek Daily Report**")
    print(f"**Balance:** ${balance:.2f} USD")
    print(f"**Model:** {model}")
    if daily_spend > 0:
        print(f"📊 **Today's spend:** ${daily_spend:.4f}")
    else:
        print(f"📊 **Today's spend:** No activity yet")
    print(f"📈 **7-day avg:** ${avg_7:.4f}/day")
    print(f"📆 **30-day total:** ${total_30:.4f}")
    if avg_7 > 0:
        weeks_left = balance / (avg_7 * 7)
        print(f"💬 **Time remaining:** ~{weeks_left:.0f} weeks at current rate")

    if spike:
        print(f"🚨 **SPIKE DETECTED** — Today's spend is {spike_factor}x the 7-day average!")

    # Threshold actions
    if balance < 0.50:
        print(f"🚨 **CRITICAL** — Balance below $0.50! Removing Pro fallback.")
        set_fallback([])
        print(f"→ **Top up at** https://platform.deepseek.com/topup")
    elif balance < 1.00:
        print(f"⚠️  **WARNING** — Balance below $1.00.")
        if avg_7 > 0:
            print(f"→ ~{balance / avg_7:.0f} days remaining")
        print(f"→ **Top up at** https://platform.deepseek.com/topup")
    elif balance < 2.00:
        print(f"🟡 **Getting low** — Balance below $2.00.")
        if avg_7 > 0:
            print(f"→ ~{balance / avg_7:.0f} days remaining")
    else:
        if avg_7 > 0:
            print(f"🟢 **Healthy** — ~{balance / avg_7:.0f} days remaining")
        else:
            print(f"🟢 **Healthy** — $2.00+ remaining")

    print(f"💡 v4-flash: $0.14/M in · $0.28/M out")


if __name__ == "__main__":
    main()
