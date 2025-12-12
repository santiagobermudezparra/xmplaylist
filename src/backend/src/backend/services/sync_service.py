"""Sync service for XM to Spotify synchronization."""

import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.config import Settings
from backend.core.interfaces import MusicProviderInterface, TrackSourceInterface
from backend.models import SyncResult, SyncStatus

logger = logging.getLogger(__name__)


class SyncService:
    def __init__(
        self,
        track_source: TrackSourceInterface,
        music_provider: MusicProviderInterface,
        settings: Settings,
    ):
        self._track_source = track_source
        self._music_provider = music_provider
        self._settings = settings
        self._scheduler = AsyncIOScheduler()
        self._is_syncing = False
        self._status = SyncStatus()

    async def start(self) -> None:
        if self._settings.sync_enabled:
            await self._music_provider.authenticate()
            self._scheduler.add_job(
                self._scheduled_sync,
                "interval",
                seconds=self._settings.sync_interval,
                id="sync_job",
            )
            self._scheduler.start()
            logger.info(
                f"Sync service started. Interval: {self._settings.sync_interval}s"
            )
            # Run initial sync
            await self.sync()
        else:
            logger.info("Sync service disabled")

    async def stop(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown()
            logger.info("Sync service stopped")

    async def _scheduled_sync(self) -> None:
        try:
            await self.sync()
        except Exception as e:
            logger.error(f"Scheduled sync failed: {e}")
        finally:
            self._status.next_sync = datetime.utcnow() + timedelta(
                seconds=self._settings.sync_interval
            )

    async def sync(self) -> dict:
        """Sync XM tracks to Spotify playlist.

        This clears the playlist first, then adds the current XM tracks.
        This ensures the playlist always reflects the current XM station state.
        """
        if self._is_syncing:
            return {"error": "Sync already in progress"}

        self._is_syncing = True
        self._status.is_running = True
        result = SyncResult(success=False)

        try:
            # 1. Fetch tracks from XM
            xm_tracks = await self._track_source.get_recent_tracks(
                station=self._settings.xm_station,
                limit=self._settings.max_tracks_per_sync,
            )
            result.tracks_found = len(xm_tracks)

            if not xm_tracks:
                result.success = True
                return result.model_dump()

            # 2. Get existing playlist tracks and CLEAR them
            existing_ids = await self._music_provider.get_playlist_tracks(
                self._settings.spotify_playlist_id
            )

            if existing_ids:
                logger.info(
                    f"Clearing {len(existing_ids)} existing tracks from playlist"
                )
                await self._music_provider.remove_tracks_from_playlist(
                    self._settings.spotify_playlist_id, existing_ids
                )

            # 3. Search for XM tracks on Spotify
            new_track_ids = []
            for track in xm_tracks:
                spotify_id = await self._music_provider.search_track(
                    track.title, track.primary_artist
                )
                if spotify_id:
                    result.tracks_matched += 1
                    new_track_ids.append(spotify_id)
                else:
                    result.tracks_failed.append(str(track))

            # 4. Add all matched tracks to playlist
            if new_track_ids:
                if await self._music_provider.add_tracks_to_playlist(
                    self._settings.spotify_playlist_id, new_track_ids
                ):
                    result.tracks_added = len(new_track_ids)
                    logger.info(f"Added {len(new_track_ids)} tracks to playlist")

            result.success = True

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            result.error = str(e)
        finally:
            self._is_syncing = False
            self._status.is_running = False
            self._status.last_sync = datetime.utcnow()
            self._status.last_result = result
            self._status.total_syncs += 1

        return result.model_dump()

    async def get_status(self) -> dict:
        return self._status.model_dump()

    @property
    def is_running(self) -> bool:
        return self._is_syncing
