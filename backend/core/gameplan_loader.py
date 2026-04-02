"""Helpers for importing GamePlanOS packages in a standalone repo."""

from __future__ import annotations

import sys
from pathlib import Path

from backend.config.settings import Settings


def ensure_gameplan_importable() -> None:
    """Ensure `gameplan.*` imports resolve in a standalone app repo."""
    try:
        import gameplan  # noqa: F401
        return
    except ImportError:
        settings = Settings.from_env()
        if settings.gameplan_src:
            candidate = Path(settings.gameplan_src).resolve()
            if candidate.exists():
                candidate_str = str(candidate)
                if candidate_str not in sys.path:
                    sys.path.insert(0, candidate_str)

    try:
        import gameplan  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "GamePlanOS packages are not importable. Prefer an editable install of "
            "the reference repo, or set GAMEPLAN_SRC to the GamePlanOS source root "
            "as a local fallback."
        ) from exc
