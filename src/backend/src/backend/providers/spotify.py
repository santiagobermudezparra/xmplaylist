"""Spotify music provider with proper token refresh handling."""

import logging
import time
from typing import Optional
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from backend.config import Settings, get_settings
from backend.core.interfaces import MusicProviderInterface

logger = logging.getLogger(__name__)


class SpotifyProvider(MusicProviderInterface):
    def __init__(self, settings: Settings | None = None):
        self._settings = settings or get_settings()
        self._client: spotipy.Spotify | None = None
        self._auth_manager: SpotifyOAuth | None = None
        self._token_info: dict | None = None
        self._token_expires_at: float = 0

    def _get_auth_manager(self) -> SpotifyOAuth:
        if self._auth_manager is None:
            self._auth_manager = SpotifyOAuth(
                client_id=self._settings.spotify_client_id,
                client_secret=self._settings.spotify_client_secret,
                redirect_uri=self._settings.spotify_redirect_uri,
                scope=" ".join(self._settings.spotify_scopes),
                open_browser=False,
                cache_handler=None,
            )
        return self._auth_manager

    def _is_token_expired(self) -> bool:
        """Check if the current token is expired or about to expire (within 60 seconds)."""
        if self._token_expires_at == 0:
            return True
        # Refresh if token expires within 60 seconds
        return time.time() > (self._token_expires_at - 60)

    def _refresh_token(self) -> str:
        """Refresh the access token using the refresh token."""
        auth_manager = self._get_auth_manager()

        if not self._settings.spotify_refresh_token:
            raise ValueError("No refresh token available. Run auth flow first.")

        logger.debug("Refreshing Spotify access token...")
        self._token_info = auth_manager.refresh_access_token(
            self._settings.spotify_refresh_token
        )

        # Calculate when this token expires
        expires_in = self._token_info.get("expires_in", 3600)
        self._token_expires_at = time.time() + expires_in

        logger.info(f"Token refreshed, expires in {expires_in} seconds")
        return self._token_info["access_token"]

    def _get_client(self) -> spotipy.Spotify:
        """Get Spotify client, refreshing token if needed."""
        # Check if we need to refresh the token
        if self._is_token_expired():
            access_token = self._refresh_token()
            # Create new client with fresh token
            self._client = spotipy.Spotify(auth=access_token)

        if self._client is None:
            # This shouldn't happen, but just in case
            access_token = self._refresh_token()
            self._client = spotipy.Spotify(auth=access_token)

        return self._client

    async def authenticate(self) -> bool:
        try:
            client = self._get_client()
            user = client.current_user()
            logger.info(f"Authenticated as: {user.get('display_name', user['id'])}")
            return True
        except Exception as e:
            logger.error(f"Spotify auth failed: {e}")
            return False

    def is_authenticated(self) -> bool:
        try:
            client = self._get_client()
            client.current_user()
            return True
        except Exception:
            return False

    async def search_track(self, title: str, artist: str) -> Optional[str]:
        client = self._get_client()
        query = f"track:{title} artist:{artist}"
        try:
            results = client.search(q=query, type="track", limit=5)
            tracks = results.get("tracks", {}).get("items", [])
            if not tracks:
                # Try a more lenient search
                query = f"{title} {artist}"
                results = client.search(q=query, type="track", limit=5)
                tracks = results.get("tracks", {}).get("items", [])
            if tracks:
                return tracks[0]["id"]
            return None
        except spotipy.SpotifyException as e:
            if e.http_status == 401:
                # Token expired, force refresh and retry
                logger.warning("Token expired during search, refreshing...")
                self._token_expires_at = 0  # Force refresh
                client = self._get_client()
                try:
                    results = client.search(q=query, type="track", limit=5)
                    tracks = results.get("tracks", {}).get("items", [])
                    if tracks:
                        return tracks[0]["id"]
                except Exception as retry_error:
                    logger.error(f"Retry failed: {retry_error}")
            else:
                logger.error(f"Error searching Spotify: {e}")
            return None
        except Exception as e:
            logger.error(f"Error searching Spotify: {e}")
            return None

    async def get_playlist_tracks(self, playlist_id: str) -> list[str]:
        client = self._get_client()
        track_ids = []
        try:
            offset = 0
            while True:
                results = client.playlist_items(
                    playlist_id,
                    offset=offset,
                    limit=100,
                    fields="items(track(id)),total",
                )
                items = results.get("items", [])
                for item in items:
                    if track := item.get("track"):
                        if track_id := track.get("id"):
                            track_ids.append(track_id)
                if len(items) < 100:
                    break
                offset += 100
            return track_ids
        except spotipy.SpotifyException as e:
            if e.http_status == 401:
                # Token expired, force refresh and retry
                logger.warning("Token expired during playlist fetch, refreshing...")
                self._token_expires_at = 0
                client = self._get_client()
                return await self.get_playlist_tracks(playlist_id)
            logger.error(f"Error getting playlist tracks: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting playlist tracks: {e}")
            raise

    async def add_tracks_to_playlist(
        self, playlist_id: str, track_ids: list[str]
    ) -> bool:
        if not track_ids:
            return True
        client = self._get_client()
        try:
            for i in range(0, len(track_ids), 100):
                batch = track_ids[i : i + 100]
                uris = [f"spotify:track:{tid}" for tid in batch]
                client.playlist_add_items(playlist_id, uris)
            logger.info(f"Added {len(track_ids)} tracks to playlist")
            return True
        except spotipy.SpotifyException as e:
            if e.http_status == 401:
                logger.warning("Token expired during add, refreshing...")
                self._token_expires_at = 0
                client = self._get_client()
                return await self.add_tracks_to_playlist(playlist_id, track_ids)
            logger.error(f"Error adding tracks: {e}")
            return False
        except Exception as e:
            logger.error(f"Error adding tracks: {e}")
            return False

    async def remove_tracks_from_playlist(
        self, playlist_id: str, track_ids: list[str]
    ) -> bool:
        if not track_ids:
            return True
        client = self._get_client()
        try:
            # Spotify API allows max 100 tracks per request
            for i in range(0, len(track_ids), 100):
                batch = track_ids[i : i + 100]
                uris = [f"spotify:track:{tid}" for tid in batch]
                client.playlist_remove_all_occurrences_of_items(playlist_id, uris)
            logger.info(f"Removed {len(track_ids)} tracks from playlist")
            return True
        except spotipy.SpotifyException as e:
            if e.http_status == 401:
                logger.warning("Token expired during remove, refreshing...")
                self._token_expires_at = 0
                client = self._get_client()
                return await self.remove_tracks_from_playlist(playlist_id, track_ids)
            logger.error(f"Error removing tracks: {e}")
            return False
        except Exception as e:
            logger.error(f"Error removing tracks: {e}")
            return False

    def get_auth_url(self) -> str:
        return self._get_auth_manager().get_authorize_url()

    def exchange_code_for_token(self, code: str) -> dict:
        return self._get_auth_manager().get_access_token(code, as_dict=True)
