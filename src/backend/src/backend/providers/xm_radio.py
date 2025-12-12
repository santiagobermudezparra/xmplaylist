"""XM Radio track source provider."""

import logging
from datetime import datetime
from typing import Any
import httpx
from backend.config import get_settings
from backend.core.interfaces import TrackSourceInterface
from backend.models import Track

logger = logging.getLogger(__name__)


class XMRadioProvider(TrackSourceInterface):
    def __init__(self, base_url: str | None = None):
        settings = get_settings()
        self.base_url = base_url or settings.xm_api_base_url
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=30.0, headers={"Accept": "application/json"}
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def get_recent_tracks(self, station: str, limit: int = 50) -> list[Track]:
        client = await self._get_client()
        url = f"{self.base_url}/station/{station}"
        try:
            logger.info(f"Fetching tracks from XM station: {station}")
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            tracks = self._parse_tracks(data.get("results", []), limit)
            logger.info(f"Fetched {len(tracks)} tracks from XM")
            return tracks
        except Exception as e:
            logger.error(f"Error fetching XM tracks: {e}")
            raise

    def _parse_tracks(self, results: list[dict[str, Any]], limit: int) -> list[Track]:
        tracks = []
        for item in results[:limit]:
            try:
                track_data = item.get("track", {})
                timestamp = None
                if ts := item.get("timestamp"):
                    try:
                        timestamp = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    except ValueError:
                        pass
                track = Track(
                    title=track_data.get("title", "Unknown"),
                    artists=track_data.get("artists", ["Unknown Artist"]),
                    timestamp=timestamp,
                    source_id=track_data.get("id"),
                )
                tracks.append(track)
            except Exception as e:
                logger.warning(f"Error parsing track: {e}")
        return tracks
