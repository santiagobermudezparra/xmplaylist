"""
Quick connectivity test for XM and Spotify APIs.

Run with: mise run test:quick
"""

import asyncio
import os
import sys


def main():
    """Quick connectivity check."""
    print("\n" + "=" * 60)
    print("QUICK CONNECTIVITY TEST")
    print("=" * 60)

    from backend.config import get_settings
    from backend.providers.spotify import SpotifyProvider
    from backend.providers.xm_radio import XMRadioProvider

    async def test():
        settings = get_settings()
        results = {"xm": False, "spotify": False}

        # Test XM Radio API
        print("\n1. Testing XM Radio API...")
        try:
            xm = XMRadioProvider()
            tracks = await xm.get_recent_tracks(settings.xm_station, limit=5)
            print(f"   ✓ XM API working - fetched {len(tracks)} tracks")
            results["xm"] = True
            await xm.close()
        except Exception as e:
            print(f"   ❌ XM API error: {e}")

        # Test Spotify API
        print("\n2. Testing Spotify API...")
        try:
            spotify = SpotifyProvider(settings)
            auth_ok = await spotify.authenticate()
            if auth_ok:
                print("   ✓ Spotify API working - authenticated successfully")
                results["spotify"] = True
            else:
                print("   ❌ Spotify authentication failed")
        except Exception as e:
            print(f"   ❌ Spotify API error: {e}")

        return results

    results = asyncio.run(test())

    print("\n" + "=" * 60)
    if all(results.values()):
        print("✅ All APIs are reachable!")
    else:
        failed = [k for k, v in results.items() if not v]
        print(f"❌ Failed: {failed}")
    print("=" * 60 + "\n")

    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()
