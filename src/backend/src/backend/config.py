"""Application configuration following 12-Factor App methodology."""

from functools import lru_cache
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="XM Spotify Sync")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    debug: bool = Field(default=False)
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=22112)

    spotify_client_id: str = Field(..., description="Spotify OAuth Client ID")
    spotify_client_secret: str = Field(..., description="Spotify OAuth Client Secret")
    spotify_redirect_uri: str = Field(default="http://localhost:8888/callback")
    spotify_refresh_token: str = Field(default="")
    spotify_playlist_id: str = Field(..., description="Target Spotify playlist ID")

    xm_station: str = Field(default="lifewithjohnmayer")
    xm_api_base_url: str = Field(default="https://xmplaylist.com/api")

    sync_interval: int = Field(default=7200)
    sync_enabled: bool = Field(default=True)
    max_tracks_per_sync: int = Field(default=50)

    cors_origins: list[str] = Field(default=["*"])

    @property
    def spotify_scopes(self) -> list[str]:
        return [
            "playlist-read-private",
            "playlist-modify-private",
            "playlist-modify-public",
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
