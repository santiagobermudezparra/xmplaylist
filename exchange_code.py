#!/usr/bin/env python3
"""Exchange OAuth code for refresh token.

Usage:
    python exchange_code.py <authorization_code>

Or run without arguments to be prompted for the code.
"""

import sys
import requests
import base64
from pathlib import Path


# Load from .env or use defaults
def get_env_value(key: str, default: str = "") -> str:
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return default


def main():
    client_id = get_env_value("SPOTIFY_CLIENT_ID")
    client_secret = get_env_value("SPOTIFY_CLIENT_SECRET")
    redirect_uri = get_env_value(
        "SPOTIFY_REDIRECT_URI", "https://homepage.watarystack.org/"
    )

    if not client_id or not client_secret:
        print("Error: SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set in .env")
        sys.exit(1)

    # Get code from argument or prompt
    if len(sys.argv) > 1:
        code = sys.argv[1]
    else:
        print("Paste the 'code' parameter from the callback URL:")
        code = input("> ").strip()

    if not code:
        print("Error: No code provided")
        sys.exit(1)

    # Exchange code for tokens
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        },
    )

    if response.status_code == 200:
        data = response.json()
        refresh_token = data.get("refresh_token")
        print("\n" + "=" * 60)
        print("SUCCESS! Add this to your .env file:")
        print("=" * 60)
        print(f"\nSPOTIFY_REFRESH_TOKEN={refresh_token}\n")

        # Optionally append to .env
        answer = input("Would you like to append this to .env automatically? [y/N] ")
        if answer.lower() == "y":
            env_file = Path(__file__).parent / ".env"
            with env_file.open("a") as f:
                f.write(f"\nSPOTIFY_REFRESH_TOKEN={refresh_token}\n")
            print("✓ Added to .env")
    else:
        print(f"Error: {response.status_code}")
        print(response.json())
        sys.exit(1)


if __name__ == "__main__":
    main()
