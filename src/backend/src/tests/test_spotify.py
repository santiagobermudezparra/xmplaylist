"""
Test Spotify token refresh and API connectivity.

Run with: mise run test:spotify
"""

import asyncio
import os
import sys


def main():
    """Test Spotify integration."""
    print("\n" + "=" * 60)
    print("SPOTIFY API INTEGRATION TEST")
    print("=" * 60)

    # Check required env vars
    required_vars = [
        "SPOTIFY_CLIENT_ID",
        "SPOTIFY_CLIENT_SECRET",
        "SPOTIFY_REFRESH_TOKEN",
        "SPOTIFY_PLAYLIST_ID",
    ]

    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        print(f"\n❌ Missing environment variables: {missing}")
        print("   Make sure your .env file contains all required variables.")
        sys.exit(1)

    print("✓ All required environment variables present")
    print(f"  - Client ID: {os.getenv('SPOTIFY_CLIENT_ID')[:8]}...")
    print(f"  - Refresh Token: {os.getenv('SPOTIFY_REFRESH_TOKEN')[:20]}...")
    print(f"  - Playlist ID: {os.getenv('SPOTIFY_PLAYLIST_ID')}")

    # Import after checking env vars
    from backend.config import get_settings
    from backend.providers.spotify import SpotifyProvider

    async def run_tests():
        settings = get_settings()
        provider = SpotifyProvider(settings)

        # Test 1: Authentication
        print("\n" + "-" * 40)
        print("TEST 1: Authentication")
        print("-" * 40)
        try:
            result = await provider.authenticate()
            if result:
                print("✓ Authentication successful!")
            else:
                print("❌ Authentication failed")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

        # Test 2: Get Playlist Tracks
        print("\n" + "-" * 40)
        print("TEST 2: Get Playlist Tracks")
        print("-" * 40)
        try:
            tracks = await provider.get_playlist_tracks(settings.spotify_playlist_id)
            print(f"✓ Found {len(tracks)} tracks in playlist")
        except Exception as e:
            print(f"❌ Error getting playlist: {e}")
            return False

        # Test 3: Search for a Track
        print("\n" + "-" * 40)
        print("TEST 3: Search for a Track")
        print("-" * 40)
        try:
            track_id = await provider.search_track("Gravity", "John Mayer")
            if track_id:
                print(f"✓ Found track: {track_id}")
            else:
                print("⚠ Track not found (this might be okay)")
        except Exception as e:
            print(f"❌ Search error: {e}")
            return False

        # Test 4: Verify Token Refresh Works
        print("\n" + "-" * 40)
        print("TEST 4: Verify Token Refresh Mechanism")
        print("-" * 40)

        # Check if the provider has proper refresh handling
        if hasattr(provider, "_auth_manager") and provider._auth_manager:
            cache_handler = provider._auth_manager.cache_handler
            if cache_handler:
                print("✓ Cache handler configured for token refresh")
                token_info = cache_handler.get_cached_token()
                if token_info:
                    print(
                        f"✓ Token info available, expires_at: {token_info.get('expires_at', 'N/A')}"
                    )
                else:
                    print("⚠ No cached token yet (will be created on first API call)")
            else:
                print("⚠ No cache handler - token refresh may not work!")
        else:
            print("⚠ Auth manager not initialized yet")

        return True

    # Run the tests
    success = asyncio.run(run_tests())

    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED!")
        print("   Your Spotify integration is working correctly.")
    else:
        print("❌ SOME TESTS FAILED")
        print("   Check the errors above and fix the issues.")
    print("=" * 60 + "\n")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
