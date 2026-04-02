"""Thin app-local wrapper over shared manpower graph helpers."""

from __future__ import annotations

from backend.core.gameplan_loader import ensure_gameplan_importable

ensure_gameplan_importable()

from gameplan.domains.manpower.algorithms.graph import (
    SOURCE_NODE_ID,
    SINK_NODE_ID,
    CareerNodeData,
    TransitionData,
    build_career_flow_graph,
)

__all__ = [
    "SOURCE_NODE_ID",
    "SINK_NODE_ID",
    "CareerNodeData",
    "TransitionData",
    "build_career_flow_graph",
]
