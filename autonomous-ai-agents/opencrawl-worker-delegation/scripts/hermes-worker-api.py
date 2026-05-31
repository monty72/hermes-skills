#!/usr/bin/env python3
"""Hermes Worker API — lightweight HTTP task runner for OpenCrawl.

Accepts POST /task with a JSON body {"task": "...description..."}
Runs hermes chat -q 'task' and returns the result.

Usage: python3 hermes-worker-api.py [--port 8081]
"""

import json
import os
import subprocess
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

HERMES_BIN = os.path.expanduser("~/.hermes-worker/bin/hermes")
HOST = "0.0.0.0"
PORT = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 8081


class TaskHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        sys.stderr.write("[HermesWorker] %s\n" % (format % args))
        sys.stderr.flush()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "worker": "opencrawl"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/task":
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b"{}"

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "invalid JSON"}).encode())
            return

        task = data.get("task", "")
        if not task:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "missing 'task' field"}).encode())
            return

        # Run hermes in single-query mode
        sys.stderr.write("[HermesWorker] Running task: %s\n" % task[:100])
        env = os.environ.copy()
        env["HERMES_HOME"] = os.path.expanduser("~/.hermes-worker")

        start = time.time()
        result = subprocess.run(
            [HERMES_BIN, "chat", "-q", task, "-Q"],
            capture_output=True, text=True, timeout=300, env=env
        )
        elapsed = time.time() - start

        output = result.stdout.strip()
        if result.stderr:
            # Filter out banner lines
            stderr_lines = [l for l in result.stderr.split("\n")
                          if not any(x in l for x in ["Hermes Agent", "Project:", "Python:", "OpenAI SDK:", "Update available"])]
            stderr_msg = "\n".join(stderr_lines[-5:]) if stderr_lines else ""
        else:
            stderr_msg = ""

        response = {
            "status": "completed" if result.returncode == 0 else "error",
            "task": task[:200],
            "output": output,
            "stderr": stderr_msg,
            "exit_code": result.returncode,
            "elapsed_seconds": round(elapsed, 2)
        }

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
        sys.stderr.write("[HermesWorker] Task completed in %.1fs (exit: %d)\n" % (elapsed, result.returncode))


def main():
    server = HTTPServer((HOST, PORT), TaskHandler)
    sys.stderr.write("[HermesWorker] Starting on %s:%d\n" % (HOST, PORT))
    sys.stderr.flush()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
