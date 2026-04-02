"""Environment-backed settings for the standalone MSim app."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings for standalone execution."""

    gameplan_src: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables."""
        return cls(gameplan_src=os.getenv("GAMEPLAN_SRC"))
