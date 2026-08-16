"""worldd configuration — all from env, validated once at startup."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Config:
    database_url: str = field(
        default_factory=lambda: os.environ.get("DATABASE_URL", ""))
    shared_secret: str = field(
        default_factory=lambda: os.environ.get("ASCENT_SHARED_SECRET", ""))
    admin_key: str = field(
        default_factory=lambda: os.environ.get("ASCENT_ADMIN_KEY", ""))
    # World day rolls at this UTC hour (economy: interest, lodge expiry,
    # PvP allotments, presents eligibility).
    world_day_utc_hour: int = field(
        default_factory=lambda: int(os.environ.get("ASCENT_WORLD_DAY_HOUR", "6")))
    # 010: Google OAuth — the Gmail door. Empty in dev/tests disables the
    # door (the button 503s rather than 500s). Set on Render + local .env.
    google_client_id: str = field(
        default_factory=lambda: os.environ.get("GOOGLE_CLIENT_ID", ""))
    google_client_secret: str = field(
        default_factory=lambda: os.environ.get("GOOGLE_CLIENT_SECRET", ""))
    google_redirect_uri: str = field(
        default_factory=lambda: os.environ.get("GOOGLE_REDIRECT_URI", ""))


_config: Config | None = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config


def reset_config() -> None:
    """Test hook — force re-read of env."""
    global _config
    _config = None
