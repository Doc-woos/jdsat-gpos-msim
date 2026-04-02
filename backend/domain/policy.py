"""Thin app-local wrapper over shared manpower policy helpers."""

from __future__ import annotations

from backend.core.gameplan_loader import ensure_gameplan_importable

ensure_gameplan_importable()

from gameplan.domains.manpower.algorithms.policy import apply_policy_overrides, build_policy_summary

__all__ = ["apply_policy_overrides", "build_policy_summary"]
