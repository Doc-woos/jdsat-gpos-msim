"""Test configuration for standalone MSim."""

from __future__ import annotations

import os
from pathlib import Path


REFERENCE_GAMEPLAN = Path(r"C:\dev\jdsat-gameplan-os")

try:
    import gameplan  # noqa: F401
except ImportError:
    if "GAMEPLAN_SRC" not in os.environ and REFERENCE_GAMEPLAN.exists():
        os.environ["GAMEPLAN_SRC"] = str(REFERENCE_GAMEPLAN)
