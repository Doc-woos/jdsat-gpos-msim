"""Shared analyst-facing export catalog definitions."""

from __future__ import annotations

from backend.api.models import ExportCatalogEntry


EXPORT_CATALOG: tuple[ExportCatalogEntry, ...] = (
    ExportCatalogEntry(
        export_id="projection_json",
        label="Projection JSON",
        scope="projection",
        format="json",
        endpoint="POST /api/projection/export",
        description="Full projection artifact with complete run payload and provenance.",
    ),
    ExportCatalogEntry(
        export_id="projection_csv",
        label="Projection CSV",
        scope="projection",
        format="csv",
        endpoint="POST /api/projection/export",
        description="Full projection rows plus grouped fill/readiness sections when pack-backed context exists.",
    ),
    ExportCatalogEntry(
        export_id="projection_summary_csv",
        label="Projection Summary CSV",
        scope="projection",
        format="csv",
        endpoint="GET /api/projection/scenarios/{scenario_name}/export-summary",
        description="Compact grouped projection summary artifact for analyst handoff.",
    ),
    ExportCatalogEntry(
        export_id="comparison_json",
        label="Comparison JSON",
        scope="comparison",
        format="json",
        endpoint="POST /api/projection/compare-named-export",
        description="Full comparison artifact with baseline, variant, deltas, and provenance.",
    ),
    ExportCatalogEntry(
        export_id="comparison_csv",
        label="Comparison CSV",
        scope="comparison",
        format="csv",
        endpoint="POST /api/projection/compare-named-export",
        description="Full comparison rows plus grouped deltas and baseline/variant fill/readiness sections when available.",
    ),
    ExportCatalogEntry(
        export_id="comparison_summary_csv",
        label="Comparison Summary CSV",
        scope="comparison",
        format="csv",
        endpoint="POST /api/projection/compare-named-export-summary",
        description="Compact grouped comparison summary artifact for analyst handoff.",
    ),
)
