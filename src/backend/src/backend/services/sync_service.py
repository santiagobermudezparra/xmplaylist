"""Sync service for coordinating XM to Spotify synchronization."""

import logging
from datetime import datetime, timedelta
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from backend.config import Settings, get_settings
from backend.core.interfaces import (
    MusicProviderInterface,
    SyncServiceInterface,
    TrackSourceInterface,
)
from backend.models import SyncResult, SyncStatus

logger = logging.getLogger(__name__)


class SyncService(SyncServiceInterface):
    def __init__(
        self,
        track_source: TrackSourceInterface,
        music_provider: MusicProviderInterface,
        settings: Settings | None = None,
    ):
        self._track_source = track_source
        self._music_provider = music_provider
        self._settings = settings or get_settings()
        self._status = SyncStatus()
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._is_syncing = False

    async def start(self) -> None:
        if not self._settings.sync_enabled:
            logger.info("Automatic sync is disabled")
            return
        if not await self._music_provider.authenticate():
            raise RuntimeError("Failed to authenticate with music provider")
        self._scheduler = AsyncIOScheduler()
        self._scheduler.add_job(
            self._scheduled_sync,
            trigger=IntervalTrigger(seconds=self._settings.sync_interval),
            id="sync_job",
            replace_existing=True,
        )
        self._scheduler.start()
        self._status.next_sync = datetime.utcnow() + timedelta(
            seconds=self._settings.sync_interval
        )
        logger.info(f"Sync service started. Interval: {self._settings.sync_interval}s")
        await self.sync()

    async def stop(self) -> None:
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None

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
        if self._is_syncing:
            return {"error": "Sync already in progress"}
        self._is_syncing = True
        self._status.is_running = True
        result = SyncResult(success=False)
        try:
            xm_tracks = await self._track_source.get_recent_tracks(
                station=self._settings.xm_station,
                limit=self._settings.max_tracks_per_sync,
            )
            result.tracks_found = len(xm_tracks)
            if not xm_tracks:
                result.success = True
                return result.model_dump()
            existing_ids = set(
                await self._music_provider.get_playlist_tracks(
                    self._settings.spotify_playlist_id
                )
            )
            new_track_ids = []
            for track in xm_tracks:
                spotify_id = await self._music_provider.search_track(
                    track.title, track.primary_artist
                )
                if spotify_id:
                    result.tracks_matched += 1
                    if spotify_id not in existing_ids:
                        new_track_ids.append(spotify_id)
                    else:
                        result.tracks_skipped += 1
                else:
                    result.tracks_failed.append(str(track))
            if new_track_ids:
                if await self._music_provider.add_tracks_to_playlist(
                    self._settings.spotify_playlist_id, new_track_ids
                ):
                    result.tracks_added = len(new_track_ids)
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
