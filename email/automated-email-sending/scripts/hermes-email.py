#!/usr/bin/env python3
"""Hermes Bot Email — send via Gmail SMTP with App Password.

Usage:
  python3 hermes-email.py "to@example.com" "Subject" body.txt
  echo "Body" | python3 hermes-email.py "to@example.com" "Subject"
"""
import os, smtplib, ssl, sys
from email.mime.text import MIMEText
CONFIG = {"smtp_host":"smtp.gmail.com","smtp_port":587,
  "address":os.environ.get("EMAIL_ADDRESS",""),
  "password":os.environ.get("EMAIL_PASSWORD",""),
  "default_to":os.environ.get("EMAIL_DEFAULT_TO","matthogarth@hotmail.com")}
def send_email(to,subject,body,from_addr=None):
  addr,pwd=CONFIG["address"],CONFIG["password"]
  if not addr or not pwd: return {"success":False,"error":"EMAIL_ADDRESS/PASSWORD not set"}
  sender=from_addr or addr
  msg=MIMEText(body,_charset="utf-8")
  msg["From"]=f"Hermes Bot <{sender}>"; msg["To"]=to; msg["Subject"]=subject; msg["Reply-To"]=sender
  try:
    ctx=ssl.create_default_context()
    with smtplib.SMTP(CONFIG["smtp_host"],CONFIG["smtp_port"],timeout=60) as s:
      s.starttls(context=ctx); s.login(addr,pwd); s.sendmail(sender,[to],msg.as_string())
    return {"success":True,"message":f"Sent to {to}"}
  except Exception as e: return {"success":False,"error":str(e)}
if __name__=="__main__":
  if len(sys.argv)<3: print(f"Usage: {sys.argv[0]} <to> <subject> [body_file]"); sys.exit(1)
  to,subject=sys.argv[1],sys.argv[2]
  body=open(sys.argv[3]).read() if len(sys.argv)>3 else sys.stdin.read()
  r=send_email(to,subject,body)
  if r["success"]: print(r["message"])
  else: print(f"Error: {r['error']}",file=sys.stderr); sys.exit(1)
