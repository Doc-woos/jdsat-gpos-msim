"""Canonical provenance helpers for run, export, and persistence metadata."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone


def build_scenario_fingerprint(scenario: object) -> str:
    """Build a deterministic fingerprint for a normalized scenario payload."""
    canonical_payload = json.dumps(
        scenario.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def build_utc_timestamp() -> str:
    """Build a UTC timestamp string for run and persistence metadata."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_file_slug(value: str, *, fallback: str) -> str:
    """Build a stable filesystem-safe slug from a scenario or artifact identifier."""
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or fallback


def build_timestamp_slug(timestamp: str) -> str:
    """Convert an ISO timestamp into a filename-safe token."""
    return "".join(char for char in timestamp if char.isalnum())
