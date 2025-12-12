"""Spotify OAuth Authentication Helper."""

import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
from backend.config import get_settings
from backend.providers import SpotifyProvider


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    authorization_code: str | None = None

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/callback":
            query = parse_qs(parsed.query)
            if "code" in query:
                OAuthCallbackHandler.authorization_code = query["code"][0]
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>Success! Return to terminal.</h1>")

    def log_message(self, format, *args):
        pass


def main():
    print("\n" + "=" * 50)
    print("Spotify OAuth Authentication Helper")
    print("=" * 50 + "\n")
    settings = get_settings()
    provider = SpotifyProvider(settings)
    auth_url = provider.get_auth_url()
    print(f"Open this URL:\n{auth_url}\n")
    try:
        webbrowser.open(auth_url)
    except Exception:
        pass
    redirect_uri = urlparse(settings.spotify_redirect_uri)
    port = redirect_uri.port or 8888
    print(f"Waiting for callback on port {port}...")
    server = HTTPServer(("localhost", port), OAuthCallbackHandler)
    server.timeout = 300
    server.handle_request()
    if OAuthCallbackHandler.authorization_code:
        token_info = provider.exchange_code_for_token(
            OAuthCallbackHandler.authorization_code
        )
        refresh_token = token_info.get("refresh_token")
        if refresh_token:
            print("\n" + "=" * 50)
            print("Add this to your .env file:")
            print("=" * 50)
            print(f"\nSPOTIFY_REFRESH_TOKEN={refresh_token}\n")


if __name__ == "__main__":
    main()
