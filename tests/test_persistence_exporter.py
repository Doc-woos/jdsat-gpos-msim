from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from backend.core.exporter import ProjectionExportService
from backend.core.persistence import WorkspaceLibraryService
from backend.core.provenance import build_file_slug, build_scenario_fingerprint, build_timestamp_slug
from backend.core.simulation import ProjectionSimulationService
from backend.domain.models import ProjectionScenario


def _load_named_scenario(path: str) -> ProjectionScenario:
    payload = json.loads(Path(path).read_text())
    return ProjectionScenario.model_validate(payload["scenario"])


def _make_workspace_root() -> Path:
    root = Path("codex_pytest_tmp") / f"persistence-{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_provenance_slug_helpers_build_stable_safe_tokens() -> None:
    assert build_file_slug("Baseline Small / Force", fallback="artifact") == "baseline-small-force"
    assert build_file_slug("!!!", fallback="artifact") == "artifact"
    assert build_timestamp_slug("2026-03-26T18:45:12.345678Z") == "20260326T184512345678Z"


def test_workspace_library_save_scenario_writes_stable_record_payload() -> None:
    workspace_root = _make_workspace_root()
    try:
        service = WorkspaceLibraryService(workspace_root / "workspace_data")
        scenario = _load_named_scenario("scenarios/baseline_small.json")
        fingerprint = build_scenario_fingerprint(scenario)
        saved_at = "2026-03-26T18:45:12Z"

        record = service.save_scenario(scenario, fingerprint, saved_at)

        saved_path = Path(record.path)
        assert saved_path.exists()
        assert saved_path.name == f"baseline-small-{fingerprint[:8]}-20260326T184512Z.json"
        payload = json.loads(saved_path.read_text())
        assert payload["record"] == record.model_dump(mode="json")
        assert payload["scenario"]["scenario_id"] == "baseline-small"
    finally:
        shutil.rmtree(workspace_root, ignore_errors=True)


def test_workspace_library_lists_records_in_reverse_saved_order() -> None:
    workspace_root = _make_workspace_root()
    try:
        service = WorkspaceLibraryService(workspace_root / "workspace_data")
        scenario = _load_named_scenario("scenarios/baseline_small.json")
        fingerprint = build_scenario_fingerprint(scenario)

        older = service.save_scenario(scenario, fingerprint, "2026-03-26T18:45:12Z")
        newer = service.save_scenario(scenario, fingerprint, "2026-03-26T18:45:13Z")

        records = service.list_records()

        assert [item.record_id for item in records[:2]] == [newer.record_id, older.record_id]
    finally:
        shutil.rmtree(workspace_root, ignore_errors=True)


def test_projection_export_uses_shared_naming_and_embeds_provenance_comments() -> None:
    scenario = _load_named_scenario("scenarios/baseline_small.json")
    result = ProjectionSimulationService().run(scenario)

    artifact = ProjectionExportService().export_projection(result, "csv")

    assert artifact.filename == (
        f"baseline-small-{result.metadata.scenario_fingerprint[:8]}-"
        f"{build_timestamp_slug(result.metadata.run_timestamp)}.csv"
    )
    assert "# scenario_id: baseline-small" in artifact.content
    assert f"# scenario_fingerprint: {result.metadata.scenario_fingerprint}" in artifact.content
    assert f"# checkpoint_ref: {result.metadata.checkpoint_ref}" in artifact.content
    assert "# authorization_basis: none" in artifact.content
    assert "0369-E5,0369,E5,19,12,7" in artifact.content


def test_named_projection_export_csv_includes_fill_and_readiness_sections() -> None:
    from backend.core.scenario_loader import ScenarioLoader

    loader = ScenarioLoader(Path('scenarios'))
    scenario = loader.load_named('synthetic_enlisted_baseline')
    result = ProjectionSimulationService().run(
        scenario,
        reference_context=loader.load_reference_context('synthetic_enlisted_baseline'),
    )

    artifact = ProjectionExportService().export_projection(result, 'csv')

    assert '# authorization_basis: authorization' in artifact.content
    assert '# section: watchlist' in artifact.content
    assert '# section: explanations' in artifact.content
    assert '# section: fill_by_community' in artifact.content
    assert '# section: fill_by_force_element' in artifact.content
    assert '# section: readiness_signals' in artifact.content
    assert 'community,infantry,781,900,-119,0.8678,stressed' in artifact.content
    assert 'force_element,gce,1042,1092,-50,0.9542,healthy' in artifact.content


def test_projection_summary_export_builds_compact_grouped_artifact() -> None:
    from backend.core.scenario_loader import ScenarioLoader

    loader = ScenarioLoader(Path('scenarios'))
    scenario = loader.load_named('synthetic_enlisted_baseline')
    result = ProjectionSimulationService().run(
        scenario,
        reference_context=loader.load_reference_context('synthetic_enlisted_baseline'),
    )

    artifact = ProjectionExportService().export_projection_summary(result)

    assert artifact.kind == 'projection_summary_export'
    assert artifact.format == 'csv'
    assert '-summary-' in artifact.filename
    assert '# kind: projection_summary_export' in artifact.content
    assert '# section: takeaways' in artifact.content
    assert '# section: watchlist' in artifact.content
    assert '# section: explanations' in artifact.content
    assert '# section: by_community' in artifact.content
    assert '# section: fill_by_community' in artifact.content
    assert '# section: readiness_signals' in artifact.content
    assert 'cyber,95,93,2' in artifact.content


def test_workspace_library_save_comparison_writes_variant_provenance() -> None:
    workspace_root = _make_workspace_root()
    try:
        service = WorkspaceLibraryService(workspace_root / "workspace_data")
        baseline = _load_named_scenario("scenarios/baseline_small.json")
        variant = _load_named_scenario("scenarios/baseline_boosted.json")
        comparison = ProjectionSimulationService().compare(baseline, variant)

        record = service.save_comparison_run(comparison)

        saved_path = Path(record.path)
        assert saved_path.exists()
        assert saved_path.name == (
            f"baseline-small-vs-baseline-boosted-"
            f"{comparison.variant.metadata.scenario_fingerprint[:8]}-"
            f"{build_timestamp_slug(comparison.variant.metadata.run_timestamp)}.json"
        )
        payload = json.loads(saved_path.read_text())
        assert payload["record"]["variant_scenario_id"] == "baseline-boosted"
        assert payload["record"]["variant_scenario_fingerprint"] == comparison.variant.metadata.scenario_fingerprint
        assert payload["comparison"]["variant"]["scenario_id"] == "baseline-boosted"
    finally:
        shutil.rmtree(workspace_root, ignore_errors=True)


def test_comparison_export_uses_shared_naming_and_embeds_variant_provenance() -> None:
    baseline = _load_named_scenario("scenarios/baseline_small.json")
    variant = _load_named_scenario("scenarios/baseline_boosted.json")
    comparison = ProjectionSimulationService().compare(baseline, variant)

    artifact = ProjectionExportService().export_comparison(comparison, "csv")

    assert artifact.filename == (
        f"baseline-small-vs-baseline-boosted-"
        f"{comparison.variant.metadata.scenario_fingerprint[:8]}-"
        f"{build_timestamp_slug(comparison.variant.metadata.run_timestamp)}.csv"
    )
    assert "# baseline_scenario_id: baseline-small" in artifact.content
    assert "# variant_scenario_id: baseline-boosted" in artifact.content
    assert f"# variant_fingerprint: {comparison.variant.metadata.scenario_fingerprint}" in artifact.content
    assert "0369-E5,19,19,7,7,0,0" in artifact.content


def test_named_comparison_export_csv_includes_grouped_delta_sections() -> None:
    from backend.core.scenario_loader import ScenarioLoader

    loader = ScenarioLoader(Path('scenarios'))
    baseline = loader.load_named('synthetic_enlisted_baseline')
    variant = loader.load_named('synthetic_enlisted_cyber_push')
    comparison = ProjectionSimulationService().compare(
        baseline,
        variant,
        baseline_reference_context=loader.load_reference_context('synthetic_enlisted_baseline'),
        variant_reference_context=loader.load_reference_context('synthetic_enlisted_cyber_push'),
    )

    artifact = ProjectionExportService().export_comparison(comparison, 'csv')

    assert '# baseline_authorization_basis: authorization' in artifact.content
    assert '# variant_authorization_basis: authorization' in artifact.content
    assert '# section: community_deltas' in artifact.content
    assert '# section: force_element_deltas' in artifact.content
    assert '# section: watchlist' in artifact.content
    assert '# section: explanations' in artifact.content
    assert '# section: baseline_fill_by_community' in artifact.content
    assert '# section: variant_fill_by_community' in artifact.content
    assert '# section: baseline_readiness_signals' in artifact.content
    assert '# section: variant_readiness_signals' in artifact.content
    assert 'community,infantry,781,900,-119,0.8678,stressed' in artifact.content
    assert 'community,cyber,106,93,13,1.1398,healthy' in artifact.content
    assert 'cyber,' in artifact.content
    assert 'mig,' in artifact.content


def test_comparison_summary_export_builds_compact_grouped_artifact() -> None:
    from backend.core.scenario_loader import ScenarioLoader

    loader = ScenarioLoader(Path('scenarios'))
    baseline = loader.load_named('synthetic_enlisted_baseline')
    variant = loader.load_named('synthetic_enlisted_cyber_push')
    comparison = ProjectionSimulationService().compare(
        baseline,
        variant,
        baseline_reference_context=loader.load_reference_context('synthetic_enlisted_baseline'),
        variant_reference_context=loader.load_reference_context('synthetic_enlisted_cyber_push'),
    )

    artifact = ProjectionExportService().export_comparison_summary(comparison)

    assert artifact.kind == 'comparison_summary_export'
    assert artifact.format == 'csv'
    assert '-summary-' in artifact.filename
    assert '# kind: comparison_summary_export' in artifact.content
    assert '# section: takeaways' in artifact.content
    assert '# section: watchlist' in artifact.content
    assert '# section: explanations' in artifact.content
    assert '# section: policy_deltas' in artifact.content
    assert '# section: drivers' in artifact.content
    assert '# section: community_deltas' in artifact.content
    assert '# section: baseline_fill_by_community' in artifact.content
    assert '# section: variant_readiness_signals' in artifact.content
    assert 'Top Community Driver: cyber' in artifact.content
