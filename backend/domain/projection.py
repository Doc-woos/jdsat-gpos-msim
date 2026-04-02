"""Thin app-local wrapper over shared manpower projection helpers."""

from __future__ import annotations

from backend.core.gameplan_loader import ensure_gameplan_importable

ensure_gameplan_importable()

from gameplan.domains.manpower.algorithms.projection import YearStepOutcome, run_projection_year

__all__ = ["YearStepOutcome", "run_projection_year"]
