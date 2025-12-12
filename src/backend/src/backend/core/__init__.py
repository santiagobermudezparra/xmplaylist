"""Core interfaces and abstractions."""

from backend.core.interfaces import (
    MusicProviderInterface,
    PlaylistManagerInterface,
    SyncServiceInterface,
    TrackSearchInterface,
    TrackSourceInterface,
)

__all__ = [
    "TrackSourceInterface",
    "TrackSearchInterface",
    "PlaylistManagerInterface",
    "MusicProviderInterface",
    "SyncServiceInterface",
]
