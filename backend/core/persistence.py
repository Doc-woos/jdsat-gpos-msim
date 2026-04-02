"""Local workspace persistence for scenarios and run records."""

from __future__ import annotations

import json
from pathlib import Path

from backend.core.provenance import build_file_slug, build_timestamp_slug
from backend.domain.models import LibraryRecord
from backend.domain.models import ProjectionComparison, ProjectionResult, ProjectionScenario


class WorkspaceLibraryService:
    """Save and list local workspace records without introducing a database."""

    def __init__(self, base_path: Path | None = None) -> None:
        self._base_path = base_path or Path("workspace_data")
        self._scenario_path = self._base_path / "scenarios"
        self._run_path = self._base_path / "runs"
        self._comparison_path = self._base_path / "comparisons"
        self._scenario_path.mkdir(parents=True, exist_ok=True)
        self._run_path.mkdir(parents=True, exist_ok=True)
        self._comparison_path.mkdir(parents=True, exist_ok=True)

    def list_records(self) -> list[LibraryRecord]:
        """List all saved library records sorted by most recent save time."""
        records: list[LibraryRecord] = []
        for folder in (self._scenario_path, self._run_path, self._comparison_path):
            for path in folder.glob("*.json"):
                payload = json.loads(path.read_text())
                records.append(LibraryRecord.model_validate(payload["record"]))
        return sorted(records, key=lambda item: item.saved_at, reverse=True)

    def save_scenario(self, scenario: ProjectionScenario, fingerprint: str, saved_at: str) -> LibraryRecord:
        """Save a scenario snapshot."""
        label = scenario.metadata.label or scenario.scenario_id
        timestamp = build_timestamp_slug(saved_at)
        path = self._scenario_path / f"{build_file_slug(scenario.scenario_id, fallback='record')}-{fingerprint[:8]}-{timestamp}.json"
        record = LibraryRecord(
            record_id=f"scenario-{fingerprint[:8]}-{timestamp}",
            kind="scenario",
            saved_at=saved_at,
            label=label,
            path=str(path),
            scenario_id=scenario.scenario_id,
            scenario_fingerprint=fingerprint,
        )
        self._write_json(
            path,
            {
                "record": record.model_dump(mode="json"),
                "scenario": scenario.model_dump(mode="json"),
            },
        )
        return record

    def save_projection_run(self, result: ProjectionResult) -> LibraryRecord:
        """Save a projection run record."""
        label = result.metadata.scenario_metadata.label or result.scenario_id
        fingerprint = result.metadata.scenario_fingerprint
        timestamp = build_timestamp_slug(result.metadata.run_timestamp)
        path = self._run_path / f"{build_file_slug(result.scenario_id, fallback='record')}-{fingerprint[:8]}-{timestamp}.json"
        record = LibraryRecord(
            record_id=f"projection-run-{fingerprint[:8]}-{timestamp}",
            kind="projection_run",
            saved_at=result.metadata.run_timestamp,
            label=label,
            path=str(path),
            scenario_id=result.scenario_id,
            scenario_fingerprint=fingerprint,
        )
        self._write_json(
            path,
            {
                "record": record.model_dump(mode="json"),
                "result": result.model_dump(mode="json"),
            },
        )
        return record

    def save_comparison_run(self, comparison: ProjectionComparison) -> LibraryRecord:
        """Save a comparison run record."""
        baseline_label = comparison.baseline.metadata.scenario_metadata.label or comparison.baseline.scenario_id
        variant_label = comparison.variant.metadata.scenario_metadata.label or comparison.variant.scenario_id
        variant_fingerprint = comparison.variant.metadata.scenario_fingerprint
        timestamp = build_timestamp_slug(comparison.variant.metadata.run_timestamp)
        path = self._comparison_path / (
            f"{build_file_slug(comparison.baseline.scenario_id, fallback='record')}-vs-"
            f"{build_file_slug(comparison.variant.scenario_id, fallback='record')}-{variant_fingerprint[:8]}-{timestamp}.json"
        )
        record = LibraryRecord(
            record_id=f"comparison-run-{variant_fingerprint[:8]}-{timestamp}",
            kind="comparison_run",
            saved_at=comparison.variant.metadata.run_timestamp,
            label=f"{baseline_label} vs {variant_label}",
            path=str(path),
            scenario_id=comparison.baseline.scenario_id,
            scenario_fingerprint=comparison.baseline.metadata.scenario_fingerprint,
            variant_scenario_id=comparison.variant.scenario_id,
            variant_scenario_fingerprint=variant_fingerprint,
        )
        self._write_json(
            path,
            {
                "record": record.model_dump(mode="json"),
                "comparison": comparison.model_dump(mode="json"),
            },
        )
        return record

    def _write_json(self, path: Path, payload: dict) -> None:
        """Write one canonical JSON record file."""
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
