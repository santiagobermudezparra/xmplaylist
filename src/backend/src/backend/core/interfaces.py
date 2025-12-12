"""Core interfaces following SOLID principles."""

from abc import ABC, abstractmethod
from typing import Optional
from backend.models.track import Track


class TrackSourceInterface(ABC):
    @abstractmethod
    async def get_recent_tracks(self, station: str, limit: int = 50) -> list[Track]:
        pass


class TrackSearchInterface(ABC):
    @abstractmethod
    async def search_track(self, title: str, artist: str) -> Optional[str]:
        pass


class PlaylistManagerInterface(ABC):
    @abstractmethod
    async def get_playlist_tracks(self, playlist_id: str) -> list[str]:
        pass

    @abstractmethod
    async def add_tracks_to_playlist(
        self, playlist_id: str, track_ids: list[str]
    ) -> bool:
        pass

    @abstractmethod
    async def remove_tracks_from_playlist(
        self, playlist_id: str, track_ids: list[str]
    ) -> bool:
        pass


class MusicProviderInterface(TrackSearchInterface, PlaylistManagerInterface):
    @abstractmethod
    async def authenticate(self) -> bool:
        pass

    @abstractmethod
    def is_authenticated(self) -> bool:
        pass


class SyncServiceInterface(ABC):
    @abstractmethod
    async def sync(self) -> dict:
        pass

    @abstractmethod
    async def get_status(self) -> dict:
        pass
