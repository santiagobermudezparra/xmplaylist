"""API routes for the sync service."""

import logging
from fastapi import APIRouter, Depends, HTTPException
from backend.config import Settings, get_settings
from backend.models import SyncResult, SyncStatus
from backend.providers import SpotifyProvider, XMRadioProvider
from backend.services import SyncService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["sync"])

_sync_service: SyncService | None = None
_xm_provider: XMRadioProvider | None = None
_spotify_provider: SpotifyProvider | None = None


def get_xm_provider() -> XMRadioProvider:
    global _xm_provider
    if _xm_provider is None:
        _xm_provider = XMRadioProvider()
    return _xm_provider


def get_spotify_provider(settings: Settings | None = None) -> SpotifyProvider:
    global _spotify_provider
    if _spotify_provider is None:
        if settings is None:
            settings = get_settings()
        _spotify_provider = SpotifyProvider(settings)
    return _spotify_provider


def get_sync_service(settings: Settings = Depends(get_settings)) -> SyncService:
    global _sync_service
    if _sync_service is None:
        _sync_service = SyncService(
            get_xm_provider(), get_spotify_provider(settings), settings
        )
    return _sync_service


async def initialize_sync_service() -> None:
    """Initialize sync service at startup (outside request context)."""
    global _sync_service
    try:
        # Call get_settings() directly instead of using Depends
        settings = get_settings()
        if _sync_service is None:
            _sync_service = SyncService(
                get_xm_provider(), get_spotify_provider(settings), settings
            )
        await _sync_service.start()
    except Exception as e:
        logger.error(f"Failed to initialize sync service: {e}")


async def shutdown_sync_service() -> None:
    global _sync_service, _xm_provider
    if _sync_service:
        await _sync_service.stop()
    if _xm_provider:
        await _xm_provider.close()


@router.get("/status", response_model=SyncStatus)
async def get_status(service: SyncService = Depends(get_sync_service)) -> SyncStatus:
    return SyncStatus(**await service.get_status())


@router.post("/sync", response_model=SyncResult)
async def trigger_sync(service: SyncService = Depends(get_sync_service)) -> SyncResult:
    if service.is_running:
        raise HTTPException(status_code=409, detail="Sync already in progress")
    return SyncResult(**await service.sync())


@router.get("/tracks")
async def get_xm_tracks(
    station: str | None = None,
    limit: int = 24,
    settings: Settings = Depends(get_settings),
):
    provider = get_xm_provider()
    tracks = await provider.get_recent_tracks(
        station or settings.xm_station, limit=limit
    )
    return {
        "station": station or settings.xm_station,
        "count": len(tracks),
        "tracks": [t.model_dump() for t in tracks],
    }
