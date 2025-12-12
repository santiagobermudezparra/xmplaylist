"""Music providers."""

from backend.providers.spotify import SpotifyProvider
from backend.providers.xm_radio import XMRadioProvider

__all__ = ["XMRadioProvider", "SpotifyProvider"]
