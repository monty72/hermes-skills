#!/usr/bin/env python3
"""
Manual OAuth PKCE Token Extraction (Headless/CLI)

Usage:
  1. Set the constants below for your provider
  2. Run: python3 oauth_pkce_manual.py
  3. Open the printed URL in your browser, log in
  4. Paste the full callback URL (or just the ?code= value) back here
  5. The script exchanges the code for tokens

Supports two redirect modes:
  - `redirect_uri_file` mode: saves state+verifier to /tmp, tells user to bring back URL
  - `localhost_server` mode: opens a local server at :8888, user's browser redirects back
"""

import base64
import hashlib
import secrets
import urllib.parse
import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

# ===== CONFIGURE THESE =====
CLIENT_ID = "ownerapi"              # From your app registration
REDIRECT_URI = "https://auth.example.com/void/callback"  # Must match app reg exactly
SCOPES = "openid email offline_access"
AUTH_HOST = "https://auth.provider.com"
TOKEN_PATH = "/oauth2/v3/token"
AUTH_PATH = "/oauth2/v3/authorize"
# ===========================

def generate_auth_url():
    """Generate PKCE params and return (auth_url, code_verifier, state)."""
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b"=").decode()
    state = secrets.token_urlsafe(16)

    auth_url = (f"{AUTH_HOST}{AUTH_PATH}?" +
        urllib.parse.urlencode({
            "client_id": CLIENT_ID,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": SCOPES,
            "state": state,
        }))

    return auth_url, code_verifier, state


def exchange_code(code, code_verifier):
    """Exchange authorization code for tokens."""
    import requests
    resp = requests.post(f"{AUTH_HOST}{TOKEN_PATH}", json={
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "code": code,
        "code_verifier": code_verifier,
        "redirect_uri": REDIRECT_URI,
    }, timeout=30)
    return resp


def start_local_server():
    """Start a local HTTP server to catch the redirect callback."""
    received_code = None

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            nonlocal received_code
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            if "code" in params:
                received_code = params["code"][0]
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"<html><body><h1>Auth successful!</h1><p>You can close this tab.</p></body></html>")
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing code parameter")

        def log_message(self, format, *args):
            pass  # Suppress log output

    print(f"Starting callback server on http://localhost:8888{callback_path} ...")
    print("After login, your browser will redirect here automatically.\n")
    server = HTTPServer(("0.0.0.0", 8888), Handler)
    server.timeout = 300

    while received_code is None:
        server.handle_request()

    return received_code


def main():
    print("OAuth PKCE Token Extraction (Headless/CLI)")
    print("=" * 50)

    # Generate the auth URL
    auth_url, code_verifier, state = generate_auth_url()

    # Save verifier and state so we don't lose them
    state_file = "/tmp/oauth_pkce_state.json"
    with open(state_file, "w") as f:
        json.dump({"cv": code_verifier, "st": state}, f)
    print(f"\nVerifier saved to {state_file}")

    # Detect mode
    use_local = input("\nRedirect mode? [local/manual] (default: manual): ").strip().lower()

    if use_local == "local":
        # Use localhost callback
        # Requires REDIRECT_URI = "http://localhost:8888/callback" set above
        code = start_local_server()
    else:
        # Manual mode
        print(f"\n{'=' * 60}\nOPEN THIS URL IN YOUR BROWSER:\n{auth_url}\n{'=' * 60}")
        print("\nLog in with your credentials.")
        result_url = input("\nPaste the FULL callback URL (or just the ?code=... value): ").strip()

        # Extract code from URL or raw code
        if "code=" in result_url:
            parsed = urllib.parse.urlparse(result_url)
            params = urllib.parse.parse_qs(parsed.query)
            code = params.get("code", [""])[0]
        else:
            code = result_url

    if not code:
        print("No code received. Aborting.")
        sys.exit(1)

    print(f"\nExchanging code for tokens...")

    # Load verifier
    with open(state_file) as f:
        saved = json.load(f)
    code_verifier = saved["cv"]

    resp = exchange_code(code, code_verifier)

    if resp.status_code == 200:
        data = resp.json()
        print(f"\n✅ SUCCESS:")
        if "refresh_token" in data:
            print(f"  Refresh token: {data['refresh_token']}")
        if "access_token" in data:
            print(f"  Access token:  {data['access_token'][:50]}...")
        print(f"  Full response: {json.dumps(data, indent=2)}")
    else:
        print(f"\n❌ FAILED (HTTP {resp.status_code}):")
        print(resp.text)


if __name__ == "__main__":
    main()
