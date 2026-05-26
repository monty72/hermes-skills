#!/usr/bin/env python3
"""
Tesla OAuth PKCE flow — prints a URL, prompts for the callback code from the user.
Run this script when you need to get a Tesla refresh token manually.
"""
import base64, hashlib, secrets, urllib.parse, json, sys, requests, os

# Generate PKCE challenge
code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).rstrip(b"=").decode()
state = secrets.token_urlsafe(16)

# Build the auth URL (redirect_uri must match client_id's registered scheme)
CLIENT_ID = "ownerapi"
auth_url = ("https://auth.tesla.com/oauth2/v3/authorize?" + urllib.parse.urlencode({
    "client_id": CLIENT_ID,
    "code_challenge": code_challenge,
    "code_challenge_method": "S256",
    "redirect_uri": "tesla://auth/callback",
    "response_type": "code",
    "scope": "openid email offline_access",
    "state": state,
}))

print("=" * 60)
print("Tesla OAuth Token Generator")
print("=" * 60)
print()
print("1. Open this URL in your browser (phone works best):")
print()
print(auth_url)
print()
print("2. Log in with your Tesla account")
print()
print("3. After login, it will try to open the Tesla app")
print("   Look at the ADDRESS BAR before the redirect.")
print("   The URL starts with: tesla://auth/callback?code=...")
print()
print("4. Copy the CODE parameter (everything after 'code='")
print("   and before '&state=') — a long base64 string.")
print()

auth_code = input("Authorization code: ").strip()

if not auth_code:
    print("No code provided, exiting.")
    sys.exit(1)

print("\nExchanging code for refresh token...")

resp = requests.post(
    "https://auth.tesla.com/oauth2/v3/token",
    json={
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "code": auth_code,
        "code_verifier": code_verifier,
        "redirect_uri": "tesla://auth/callback",
    },
    timeout=30,
)

if resp.status_code == 200:
    data = resp.json()
    refresh_token = data.get("refresh_token")
    access_token = data.get("access_token")

    print(f"\n✅ SUCCESS!")
    print(f"Access Token:  {access_token[:50]}...")
    print(f"Refresh Token: {refresh_token}")

    # Save for pyPowerwall
    auth_dir = os.path.expanduser("~/.pypowerwall")
    os.makedirs(auth_dir, exist_ok=True)

    auth_data = {
        "refresh_token": refresh_token,
        "email": input("Tesla email (for pyPowerwall config): ").strip() or "",
        "region": "us",
        "access_token": access_token,
    }
    with open(f"{auth_dir}/.pypowerwall.auth", "w") as f:
        json.dump(auth_data, f)
    with open(f"{auth_dir}/.pypowerwall.site", "w") as f:
        json.dump({"email": auth_data["email"], "sites": []}, f)

    print(f"\nSaved pyPowerwall config to {auth_dir}/")
    print("Run: pypowerwall get -cloud")
else:
    print(f"\n❌ Token exchange failed (HTTP {resp.status_code})")
    print(resp.text)
    sys.exit(1)
