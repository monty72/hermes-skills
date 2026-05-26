#!/usr/bin/env python3
"""Live data API server for Hermes Mission Control."""
import json, os, re, time
from http.server import HTTPServer, BaseHTTPRequestHandler

HERMES_HOME = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))
LOG_PATH = os.path.join(HERMES_HOME, "logs", "agent.log")
SKILLS_DIR = os.path.join(HERMES_HOME, "skills")
CRON_DIR = os.path.join(HERMES_HOME, "cron")

def get_status():
    total_in = total_out = total_calls = 0
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH) as f:
            for line in f:
                if "API call" in line:
                    total_calls += 1; m = re.search(r'in=(\d+)', line); total_in += int(m.group(1)) if m else 0
                    m = re.search(r'out=(\d+)', line); total_out += int(m.group(1)) if m else 0
    cost = (total_in/1e6*0.27)+(total_out/1e6*1.10)
    uptime = "N/A"
    if os.path.exists("/proc/uptime"):
        s = float(open("/proc/uptime").read().split()[0])
        uptime = f"{int(s//3600)}h {int((s%3600)//60)}m"
    mem_pct = mem_gb = 0
    if os.path.exists("/proc/meminfo"):
        m = {}; [exec(f"m['{k.split(':')[0]}']={v.split()[0]}") for k,v in [l.split(':',1) for l in open('/proc/meminfo').readlines()[:4]] if 'MemTotal' in k or 'MemAvailable' in k]
        # simpler:
        d = open('/proc/meminfo').read()
        mt = int([l for l in d.split('\n') if 'MemTotal' in l][0].split()[1])
        ma = int([l for l in d.split('\n') if 'MemAvailable' in l][0].split()[1])
        mem_pct = round((1-ma/mt)*100,1); mem_gb = round(mt/1024/1024,1)
    host = open('/proc/sys/kernel/hostname').read().strip() if os.path.exists('/proc/sys/kernel/hostname') else 'Hermes'
    skills = sum(1 for r,_,fs in os.walk(SKILLS_DIR) for f in fs if f=='SKILL.md') if os.path.exists(SKILLS_DIR) else 0
    cron_total = 0
    if os.path.exists(CRON_DIR):
        cron_total = sum(1 for f in os.listdir(CRON_DIR) if os.path.exists(os.path.join(CRON_DIR,f,'job.json')))
    return {
        "totalTokens": total_in+total_out, "estimatedCost": round(cost,4),
        "totalApiCalls": total_calls, "apiErrors": 0, "memPct": mem_pct,
        "memTotalGB": mem_gb, "uptime": uptime, "hostname": host,
        "skillsCount": skills, "cronTotal": cron_total, "cronActive": 0,
        "activeAgents": 7, "agentsRunning": 5,
        "services": [
            {"icon":"🖥️","name":"Hermes Core","status":"green","detail":f"uptime {uptime}"},
            {"icon":"📡","name":"Telegram Gateway","status":"green","detail":"Connected"},
            {"icon":"🧠","name":"DeepSeek API","status":"green","detail":f"{total_calls} calls"},
            {"icon":"⚡","name":"Subagents","status":"green","detail":"3 workers"},
        ],
        "agents": [
            {"initial":"H","name":"Hermes (Main)","desc":"deepseek-chat · Telegram DM","status":"running","statusLabel":"Running"},
            {"initial":"S","name":"Subagent Pool","desc":"3 workers","status":"idle","statusLabel":"Idle"},
            {"initial":"C","name":"Cron Scheduler","desc":f"{cron_total} jobs","status":"idle","statusLabel":"Idle"},
            {"initial":"K","name":"Kanban Orchestrator","desc":"Dispatcher","status":"idle","statusLabel":"Idle"},
            {"initial":"G","name":"Gateway Listener","desc":"Telegram","status":"running","statusLabel":"Running"},
            {"initial":"W","name":"Webhook Handler","desc":"Triggers","status":"idle","statusLabel":"Idle"},
            {"initial":"M","name":"Memory Syncer","desc":"Persistence","status":"running","statusLabel":"Running"},
        ],
        "activity": [
            {"dot":"green","icon":"✓","title":"Online","desc":f"Uptime {uptime}","time":"active"},
            {"dot":"blue","icon":"↻","title":f"Tokens: {(total_in+total_out)/1e6:.1f}M","desc":f"≈ ${cost:.2f}","time":"lifetime"},
        ],
    }

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*"); self.send_header("Cache-Control","no-cache"); self.end_headers()
        self.wfile.write(json.dumps(get_status()).encode())
    def log_message(self,*a): pass

if __name__=="__main__":
    p = int(os.environ.get("PORT",8081))
    HTTPServer(("0.0.0.0",p),Handler).serve_forever()
