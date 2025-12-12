"""Track data models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Track(BaseModel):
    title: str = Field(..., description="Track title")
    artists: list[str] = Field(..., description="List of artist names")
    timestamp: Optional[datetime] = Field(None)
    source_id: Optional[str] = Field(None)
    album: Optional[str] = None

    @property
    def primary_artist(self) -> str:
        return self.artists[0] if self.artists else "Unknown Artist"

    @property
    def artist_string(self) -> str:
        return ", ".join(self.artists)

    def __str__(self) -> str:
        return f"{self.title} - {self.artist_string}"


class SpotifyTrack(BaseModel):
    track: Track
    spotify_id: str
    spotify_uri: str


class SyncResult(BaseModel):
    success: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tracks_found: int = 0
    tracks_matched: int = 0
    tracks_added: int = 0
    tracks_skipped: int = 0
    tracks_failed: list[str] = Field(default_factory=list)
    error: Optional[str] = None


class SyncStatus(BaseModel):
    is_running: bool = False
    last_sync: Optional[datetime] = None
    last_result: Optional[SyncResult] = None
    next_sync: Optional[datetime] = None
    total_syncs: int = 0
