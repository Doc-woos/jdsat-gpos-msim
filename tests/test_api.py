"""API tests for the standalone MSim MVP slice."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.server import app


SEQUENTIAL_RULE = "sequential_declared_order"
PHASED_RULE = "phased_standard_v1"
SEQUENTIAL_DECISION_REF = "ADR-0001"
PHASED_DECISION_REF = "ADR-0002"
SEQUENTIAL_CHECKPOINT_REF = "2026-03-25-sequential-rule-baseline"
PHASED_CHECKPOINT_REF = "2026-03-25-phased-rule-added"


def test_root_route_serves_analyst_workbench() -> None:
    """The app should expose a minimal analyst workbench at the root path."""
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "MSim Analyst Workbench" in response.text
    assert "Projection CSV exports include grouped fill and readiness sections" in response.text
    assert "Run a comparison to see which grouped sections comparison CSV export will include." in response.text
    assert "Export Summary CSV" in response.text
    assert "/static/app.js" in response.text


def test_health_route_returns_expected_payload() -> None:
    """The backend should expose a stable health route."""
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "app": "msim",
        "status": "ok",
        "slice": "projection-mvp",
    }


def test_named_scenario_listing_exposes_available_fixtures() -> None:
    """The API should list named scenario fixtures for discovery."""
    client = TestClient(app)

    response = client.get("/api/projection/scenarios")

    assert response.status_code == 200
    assert response.json() == {
        "scenario_names": [
            "baseline_accession_override",
            "baseline_accession_table",
            "baseline_boosted",
            "baseline_policy_override",
            "baseline_rate_table",
            "baseline_small",
            "baseline_year_phased_override",
            "medium_infantry_team",
            "medium_policy_team",
            "medium_unordered_phased",
            "medium_unordered_sequential",
            "synthetic_enlisted_baseline",
            "synthetic_enlisted_cyber_push",
            "unordered_phased",
            "unordered_sequential",
        ]
    }


def test_scenario_catalog_returns_labels_and_notes() -> None:
    """The workbench should be able to load analyst-facing catalog metadata."""
    client = TestClient(app)

    response = client.get("/api/projection/catalog")

    assert response.status_code == 200
    scenarios = response.json()["scenarios"]
    baseline = next(item for item in scenarios if item["scenario_name"] == "baseline_small")
    assert baseline == {
        "scenario_name": "baseline_small",
        "scenario_id": "baseline-small",
        "label": "Baseline Small Force",
        "processing_rule": SEQUENTIAL_RULE,
        "version": "0.1.0",
        "source": "reference-fixture",
        "notes": "Two-year baseline projection for the compact three-cell force.",
    }


def test_export_catalog_lists_supported_artifacts() -> None:
    client = TestClient(app)

    response = client.get("/api/projection/export-catalog")

    assert response.status_code == 200
    exports = response.json()["exports"]
    ids = {item["export_id"] for item in exports}
    assert {
        "projection_json",
        "projection_csv",
        "projection_summary_csv",
        "comparison_json",
        "comparison_csv",
        "comparison_summary_csv",
    } <= ids
    summary_entry = next(item for item in exports if item["export_id"] == "comparison_summary_csv")
    assert summary_entry["endpoint"] == "POST /api/projection/compare-named-export-summary"


def test_named_scenario_definition_returns_stable_payload() -> None:
    """The frontend should be able to load a named scenario definition through the API."""
    client = TestClient(app)

    response = client.get("/api/projection/scenarios/baseline_small/definition")

    assert response.status_code == 200
    body = response.json()
    assert body["scenario_name"] == "baseline_small"
    assert body["scenario"]["scenario_id"] == "baseline-small"
    assert body["scenario"]["metadata"] == {
        "version": "0.1.0",
        "label": "Baseline Small Force",
        "created_by": None,
        "source": "reference-fixture",
        "notes": "Two-year baseline projection for the compact three-cell force.",
    }


def test_projection_route_returns_stable_result_shape() -> None:
    """The projection route should return the first-slice response contract."""
    client = TestClient(app)
    payload = json.loads(Path("scenarios/baseline_small.json").read_text())

    response = client.post("/api/projection/run", json=payload)

    assert response.status_code == 200
    body = response.json()["result"]
    assert body["scenario_id"] == "baseline-small"
    assert body["horizon_years"] == 2
    assert len(body["projected_inventory"]) == 3
    assert body["metadata"]["engine"] == "gameplan.engine"
    assert body["metadata"]["deterministic"] is True
    assert body["metadata"]["processing_rule"] == SEQUENTIAL_RULE
    assert body["metadata"]["decision_ref"] == SEQUENTIAL_DECISION_REF
    assert body["metadata"]["checkpoint_ref"] == SEQUENTIAL_CHECKPOINT_REF
    assert body["metadata"]["run_timestamp"].endswith("Z")
    assert len(body["metadata"]["scenario_fingerprint"]) == 64
    assert body["metadata"]["scenario_metadata"] == {
        "version": "0.1.0",
        "label": "Baseline Small Force",
        "created_by": None,
        "source": "reference-fixture",
        "notes": "Two-year baseline projection for the compact three-cell force.",
    }
    assert body["metadata"]["policy_summary"] == {
        "rate_table_entries": 0,
        "rate_overrides": 0,
        "accession_table_entries": 0,
        "accession_overrides": 0,
    }
    assert body["metrics"]["total_inventory"] == 158
    assert body["metrics"]["transitions_applied"] == {
        "promotion": 33,
        "lateral_move": 0,
        "loss": 16,
        "accession": 24,
    }
    assert body["summary"]["by_grade"] == [
        {"key": "E3", "inventory": 92, "demand": 95, "gap": -3},
        {"key": "E4", "inventory": 47, "demand": 45, "gap": 2},
        {"key": "E5", "inventory": 19, "demand": 12, "gap": 7},
    ]
    assert body["summary"]["by_specialty"] == [
        {"key": "0311", "inventory": 139, "demand": 140, "gap": -1},
        {"key": "0369", "inventory": 19, "demand": 12, "gap": 7},
    ]
    assert body["summary"]["takeaways"][0] == "Grouped fill and readiness views are unavailable for scenarios without pack reference context."
    assert body["summary"]["watchlist"] == []
    assert body["summary"]["explanations"][0]["title"] == "Top cell shortage: 0311-E3"
    assert body["summary"]["largest_shortages"][0]["cell_id"] == "0311-E3"
    assert body["summary"]["largest_overages"][0]["cell_id"] == "0369-E5"


def test_projection_route_echoes_scenario_metadata_and_stable_fingerprint() -> None:
    """Inline runs should echo input metadata and fingerprint semantically identical scenarios the same way."""
    client = TestClient(app)
    payload = {
        "scenario": {
            "scenario_id": "metadata-check",
            "horizon_years": 1,
            "metadata": {
                "version": "1.0.1",
                "label": "Metadata Check",
                "created_by": "analyst-a",
                "source": "manual-entry",
                "notes": "checkpoint scenario"
            },
            "career_cells": [
                {
                    "cell_id": "0311-E3",
                    "specialty": "0311",
                    "grade": "E3",
                    "inventory": 10,
                    "demand": 10
                }
            ],
            "transitions": [
                {
                    "transition_id": "acc-0311-e3",
                    "transition_type": "accession",
                    "target_cell_id": "0311-E3",
                    "amount": 0
                }
            ]
        }
    }

    first = client.post("/api/projection/run", json=payload)
    second = client.post("/api/projection/run", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    first_metadata = first.json()["result"]["metadata"]
    second_metadata = second.json()["result"]["metadata"]
    assert first_metadata["scenario_metadata"] == {
        "version": "1.0.1",
        "label": "Metadata Check",
        "created_by": "analyst-a",
        "source": "manual-entry",
        "notes": "checkpoint scenario",
    }
    assert first_metadata["scenario_fingerprint"] == second_metadata["scenario_fingerprint"]
    assert first_metadata["scenario_fingerprint"] != ""


def test_projection_export_returns_portable_json_artifact() -> None:
    """Projection export should return a stable JSON artifact envelope and payload."""
    client = TestClient(app)
    payload = json.loads(Path("scenarios/baseline_small.json").read_text())
    payload["format"] = "json"

    response = client.post("/api/projection/export", json=payload)

    assert response.status_code == 200
    artifact = response.json()["artifact"]
    assert artifact["kind"] == "projection_export"
    assert artifact["format"] == "json"
    assert artifact["media_type"] == "application/json"
    assert artifact["filename"].startswith("baseline-small-")
    assert artifact["filename"].endswith(".json")
    content = json.loads(artifact["content"])
    assert content["artifact_kind"] == "projection_export"
    assert content["result"]["scenario_id"] == "baseline-small"
    assert content["result"]["metadata"]["decision_ref"] == SEQUENTIAL_DECISION_REF


def test_projection_summary_export_returns_compact_csv_artifact() -> None:
    client = TestClient(app)
    payload = json.loads(Path("scenarios/baseline_small.json").read_text())

    response = client.post("/api/projection/export-summary", json=payload)

    assert response.status_code == 200
    artifact = response.json()["artifact"]
    assert artifact["kind"] == "projection_summary_export"
    assert artifact["format"] == "csv"
    assert artifact["filename"].startswith("baseline-small-summary-")
    assert "# kind: projection_summary_export" in artifact["content"]
    assert "# section: explanations" in artifact["content"]
    assert "# section: by_grade" in artifact["content"]


def test_comparison_export_returns_portable_csv_artifact() -> None:
    """Comparison export should return CSV content with embedded provenance comments."""
    client = TestClient(app)
    payload = {
        "baseline": json.loads(Path("scenarios/baseline_small.json").read_text())["scenario"],
        "variant": json.loads(Path("scenarios/baseline_boosted.json").read_text())["scenario"],
        "format": "csv",
    }

    response = client.post("/api/projection/compare-export", json=payload)

    assert response.status_code == 200
    artifact = response.json()["artifact"]
    assert artifact["kind"] == "comparison_export"
    assert artifact["format"] == "csv"
    assert artifact["media_type"] == "text/csv"
    assert artifact["filename"].startswith("baseline-small-vs-baseline-boosted-")
    assert artifact["filename"].endswith(".csv")
    assert "# kind: comparison_export" in artifact["content"]
    assert "# baseline_scenario_id: baseline-small" in artifact["content"]
    assert "# variant_scenario_id: baseline-boosted" in artifact["content"]
    assert "cell_id,baseline_inventory,variant_inventory,baseline_gap,variant_gap,inventory_delta,gap_delta" in artifact["content"]


def test_named_projection_route_runs_fixture() -> None:
    """Named scenario execution should load and run a local fixture."""
    client = TestClient(app)

    response = client.get("/api/projection/scenarios/baseline_small")

    assert response.status_code == 200
    body = response.json()
    assert body["scenario_name"] == "baseline_small"
    assert body["result"]["scenario_id"] == "baseline-small"
    assert body["result"]["metadata"]["processing_rule"] == SEQUENTIAL_RULE
    assert body["result"]["metadata"]["decision_ref"] == SEQUENTIAL_DECISION_REF
    assert body["result"]["metadata"]["checkpoint_ref"] == SEQUENTIAL_CHECKPOINT_REF


def test_rate_table_variant_replaces_matching_rates_on_sequential_baseline() -> None:
    """Structured rate table entries should change outcomes without changing the baseline rule."""
    client = TestClient(app)

    response = client.post(
        "/api/projection/compare-named",
        json={
            "baseline_scenario_name": "baseline_small",
            "variant_scenario_name": "baseline_rate_table",
        },
    )

    assert response.status_code == 200
    comparison = response.json()["comparison"]
    assert comparison["baseline"]["metadata"]["processing_rule"] == SEQUENTIAL_RULE
    assert comparison["variant"]["metadata"]["processing_rule"] == SEQUENTIAL_RULE
    assert comparison["inventory_delta"] == 0
    assert comparison["gap_delta"] == 0
    assert comparison["summary"]["largest_inventory_gains"][0]["cell_id"] == "0311-E4"
    assert comparison["summary"]["largest_gap_improvements"][0]["cell_id"] == "0311-E4"
    assert comparison["summary"]["largest_inventory_losses"][0]["cell_id"] == "0311-E3"


def test_accession_table_variant_replaces_matching_accessions_on_sequential_baseline() -> None:
    """Structured accession table entries should change outcomes without changing the baseline rule."""
    client = TestClient(app)

    response = client.post(
        "/api/projection/compare-named",
        json={
            "baseline_scenario_name": "baseline_small",
            "variant_scenario_name": "baseline_accession_table",
        },
    )

    assert response.status_code == 200
    comparison = response.json()["comparison"]
    assert comparison["baseline"]["metadata"]["processing_rule"] == SEQUENTIAL_RULE
    assert comparison["variant"]["metadata"]["processing_rule"] == SEQUENTIAL_RULE
    assert comparison["inventory_delta"] == 8
    assert comparison["gap_delta"] == 8
    assert comparison["summary"]["largest_inventory_gains"][0]["cell_id"] == "0311-E3"
    assert comparison["summary"]["largest_gap_improvements"][0]["cell_id"] == "0311-E3"


def test_accession_override_variant_increases_inventory_on_sequential_baseline() -> None:
    """Accession overrides should raise inventory without changing the baseline rule."""
    client = TestClient(app)

    response = client.post(
        "/api/projection/compare-named",
        json={
            "baseline_scenario_name": "baseline_small",
            "variant_scenario_name": "baseline_accession_override",
        },
    )

    assert response.status_code == 200
    comparison = response.json()["comparison"]
    assert comparison["baseline"]["metadata"]["processing_rule"] == SEQUENTIAL_RULE
    assert comparison["variant"]["metadata"]["processing_rule"] == SEQUENTIAL_RULE
    assert comparison["inventory_delta"] == 8
    assert comparison["gap_delta"] == 8
    assert comparison["summary"]["largest_inventory_gains"][0]["cell_id"] == "0311-E3"
    assert comparison["summary"]["largest_gap_improvements"][0]["cell_id"] == "0311-E3"


def test_policy_override_variant_changes_outcome_without_changing_default_rule() -> None:
    """Always-on rate overrides should alter outcomes on the sequential baseline rule."""
    client = TestClient(app)

    response = client.post(
        "/api/projection/compare-named",
        json={
            "baseline_scenario_name": "baseline_small",
            "variant_scenario_name": "baseline_policy_override",
        },
    )

    assert response.status_code == 200
    comparison = response.json()["comparison"]
    assert comparison["baseline"]["metadata"]["processing_rule"] == SEQUENTIAL_RULE
    assert comparison["variant"]["metadata"]["processing_rule"] == SEQUENTIAL_RULE
    assert comparison["inventory_delta"] == 4
    assert comparison["gap_delta"] == 4
    assert comparison["summary"]["largest_inventory_gains"][0]["cell_id"] == "0311-E4"
    assert comparison["summary"]["largest_gap_improvements"][0]["cell_id"] == "0311-E4"


def test_year_phased_override_changes_only_later_years() -> None:
    """Year-windowed rate overrides should alter outcomes while staying on the sequential rule."""
    client = TestClient(app)

    response = client.post(
        "/api/projection/compare-named",
        json={
            "baseline_scenario_name": "baseline_small",
            "variant_scenario_name": "baseline_year_phased_override",
        },
    )

    assert response.status_code == 200
    comparison = response.json()["comparison"]
    assert comparison["baseline"]["metadata"]["processing_rule"] == SEQUENTIAL_RULE
    assert comparison["variant"]["metadata"]["processing_rule"] == SEQUENTIAL_RULE
    assert comparison["inventory_delta"] == -1
    assert comparison["gap_delta"] == -1
    assert comparison["summary"]["largest_inventory_gains"][0]["cell_id"] == "0311-E4"
    assert comparison["summary"]["largest_inventory_losses"][0]["cell_id"] == "0311-E3"


def test_phased_projection_uses_alternate_metadata_and_rule() -> None:
    """Phased fixtures should report the phased rule and decision provenance."""
    client = TestClient(app)

    response = client.get("/api/projection/scenarios/unordered_phased")

    assert response.status_code == 200
    body = response.json()["result"]
    assert body["scenario_id"] == "unordered-phased"
    assert body["metadata"]["processing_rule"] == PHASED_RULE
    assert body["metadata"]["decision_ref"] == PHASED_DECISION_REF
    assert body["metadata"]["checkpoint_ref"] == PHASED_CHECKPOINT_REF
    assert body["metrics"]["total_inventory"] == 158


def test_phased_processing_changes_outcome_for_unordered_transitions() -> None:
    """Phased mode should differ from sequential mode when transition order is scrambled."""
    client = TestClient(app)

    response = client.post(
        "/api/projection/compare-named",
        json={
            "baseline_scenario_name": "unordered_sequential",
            "variant_scenario_name": "unordered_phased",
        },
    )

    assert response.status_code == 200
    comparison = response.json()["comparison"]
    assert comparison["baseline"]["metadata"]["processing_rule"] == SEQUENTIAL_RULE
    assert comparison["variant"]["metadata"]["processing_rule"] == PHASED_RULE
    assert comparison["inventory_delta"] == -1
    assert comparison["gap_delta"] == -1
    assert comparison["summary"]["largest_inventory_losses"][0]["cell_id"] == "0311-E3"
    assert comparison["summary"]["largest_gap_improvements"][0]["cell_id"] == "0311-E4"


def test_named_projection_comparison_returns_positive_delta_for_boosted_accessions() -> None:
    """Boosted accession scenario should outperform the baseline inventory total."""
    client = TestClient(app)

    response = client.post(
        "/api/projection/compare-named",
        json={
            "baseline_scenario_name": "baseline_small",
            "variant_scenario_name": "baseline_boosted",
        },
    )

    assert response.status_code == 200
    comparison = response.json()["comparison"]
    assert comparison["baseline"]["scenario_id"] == "baseline-small"
    assert comparison["variant"]["scenario_id"] == "baseline-boosted"
    assert comparison["baseline"]["metadata"]["processing_rule"] == SEQUENTIAL_RULE
    assert comparison["variant"]["metadata"]["processing_rule"] == SEQUENTIAL_RULE
    assert comparison["baseline"]["metadata"]["decision_ref"] == SEQUENTIAL_DECISION_REF
    assert comparison["variant"]["metadata"]["decision_ref"] == SEQUENTIAL_DECISION_REF
    assert comparison["baseline"]["metadata"]["checkpoint_ref"] == SEQUENTIAL_CHECKPOINT_REF
    assert comparison["variant"]["metadata"]["checkpoint_ref"] == SEQUENTIAL_CHECKPOINT_REF
    assert comparison["inventory_delta"] > 0
    assert comparison["gap_delta"] > 0
    assert any(
        item["cell_id"] == "0311-E3" and item["inventory_delta"] > 0
        for item in comparison["cell_deltas"]
    )
    assert comparison["summary"]["largest_inventory_gains"][0]["cell_id"] == "0311-E3"
    assert comparison["summary"]["largest_gap_improvements"][0]["cell_id"] == "0311-E3"


def test_projection_route_rejects_global_rate_override_without_cohort_selector() -> None:
    """Policy overrides should target at least one cohort selector."""
    client = TestClient(app)
    payload = {
        "scenario": {
            "scenario_id": "bad-rate-override",
            "horizon_years": 1,
            "career_cells": [
                {
                    "cell_id": "0311-E3",
                    "specialty": "0311",
                    "grade": "E3",
                    "inventory": 10,
                    "demand": 10,
                },
                {
                    "cell_id": "0311-E4",
                    "specialty": "0311",
                    "grade": "E4",
                    "inventory": 5,
                    "demand": 5,
                }
            ],
            "transitions": [
                {
                    "transition_id": "prom-0311-e3-e4",
                    "transition_type": "promotion",
                    "source_cell_id": "0311-E3",
                    "target_cell_id": "0311-E4",
                    "rate": 0.1,
                }
            ],
            "rate_overrides": [
                {
                    "override_id": "global-rate-override",
                    "transition_type": "promotion",
                    "year_start": 1,
                    "year_end": 1,
                    "rate_multiplier": 1.1,
                }
            ],
        }
    }

    response = client.post("/api/projection/run", json=payload)

    assert response.status_code == 422
    assert "rate_overrides require at least one cohort selector" in response.text


def test_projection_route_rejects_unknown_cell_reference() -> None:
    """Invalid transition references should fail validation."""
    client = TestClient(app)
    payload = {
        "scenario": {
            "scenario_id": "bad-scenario",
            "horizon_years": 1,
            "career_cells": [
                {
                    "cell_id": "0311-E3",
                    "specialty": "0311",
                    "grade": "E3",
                    "inventory": 10,
                    "demand": 10,
                }
            ],
            "transitions": [
                {
                    "transition_id": "bad-prom",
                    "transition_type": "promotion",
                    "source_cell_id": "missing-cell",
                    "target_cell_id": "0311-E3",
                    "rate": 0.1,
                }
            ],
        }
    }

    response = client.post("/api/projection/run", json=payload)

    assert response.status_code == 422

def test_comparison_response_includes_policy_and_outcome_drivers() -> None:
    """Policy-driven comparisons should explain rule status, policy deltas, and top outcome drivers."""
    client = TestClient(app)

    response = client.post(
        "/api/projection/compare-named",
        json={
            "baseline_scenario_name": "baseline_small",
            "variant_scenario_name": "baseline_policy_override",
        },
    )

    assert response.status_code == 200
    summary = response.json()["comparison"]["summary"]
    assert summary["rule_change"] is False
    assert summary["rule_summary"] == f"Both scenarios used {SEQUENTIAL_RULE}."
    rate_override_delta = next(item for item in summary["policy_deltas"] if item["category"] == "Rate Overrides")
    assert rate_override_delta == {
        "category": "Rate Overrides",
        "baseline_count": 0,
        "variant_count": 2,
        "delta": 2,
    }
    assert any(driver["title"] == "Rate Overrides" for driver in summary["drivers"])
    assert any(driver["title"] == "Top Cell Driver: 0311-E4" for driver in summary["drivers"])


def test_comparison_response_flags_processing_rule_changes() -> None:
    """Rule-driven comparisons should explicitly call out processing-rule changes."""
    client = TestClient(app)

    response = client.post(
        "/api/projection/compare-named",
        json={
            "baseline_scenario_name": "unordered_sequential",
            "variant_scenario_name": "unordered_phased",
        },
    )

    assert response.status_code == 200
    summary = response.json()["comparison"]["summary"]
    assert summary["rule_change"] is True
    assert summary["rule_summary"] == (
        f"Processing rule changed from {SEQUENTIAL_RULE} to {PHASED_RULE}."
    )
    assert summary["drivers"][0]["kind"] == "rule"


def test_library_save_endpoints_persist_scenario_run_and_comparison_records() -> None:
    """The local workspace library should persist scenario snapshots, runs, and comparisons."""
    client = TestClient(app)
    scenario_payload = {
        "scenario": {
            "scenario_id": "library-save-check",
            "horizon_years": 1,
            "metadata": {
                "version": "1.0.0",
                "label": "Library Save Check",
                "source": "test-case",
                "notes": "Persistence smoke check"
            },
            "career_cells": [
                {
                    "cell_id": "0311-E3",
                    "specialty": "0311",
                    "grade": "E3",
                    "inventory": 10,
                    "demand": 10
                }
            ],
            "transitions": [
                {
                    "transition_id": "acc-0311-e3",
                    "transition_type": "accession",
                    "target_cell_id": "0311-E3",
                    "amount": 0
                }
            ]
        }
    }

    save_scenario = client.post("/api/library/scenarios/save", json=scenario_payload)
    assert save_scenario.status_code == 200
    scenario_record = save_scenario.json()["record"]
    assert scenario_record["kind"] == "scenario"
    assert Path(scenario_record["path"]).exists()

    run_payload = json.loads(Path("scenarios/baseline_small.json").read_text())
    save_run = client.post("/api/library/runs/save", json=run_payload)
    assert save_run.status_code == 200
    run_record = save_run.json()["record"]
    assert run_record["kind"] == "projection_run"
    assert Path(run_record["path"]).exists()

    compare_payload = {
        "baseline": json.loads(Path("scenarios/baseline_small.json").read_text())["scenario"],
        "variant": json.loads(Path("scenarios/baseline_boosted.json").read_text())["scenario"],
    }
    save_comparison = client.post("/api/library/comparisons/save", json=compare_payload)
    assert save_comparison.status_code == 200
    comparison_record = save_comparison.json()["record"]
    assert comparison_record["kind"] == "comparison_run"
    assert Path(comparison_record["path"]).exists()

    listing = client.get("/api/library/records")
    assert listing.status_code == 200
    records = listing.json()["records"]
    record_ids = {item["record_id"] for item in records}
    assert scenario_record["record_id"] in record_ids
    assert run_record["record_id"] in record_ids
    assert comparison_record["record_id"] in record_ids


def test_directory_backed_named_scenario_definition_returns_expanded_payload() -> None:
    """Directory-backed fixtures should expand into the stable named-scenario definition payload."""
    client = TestClient(app)

    response = client.get("/api/projection/scenarios/medium_infantry_team/definition")

    assert response.status_code == 200
    body = response.json()
    assert body["scenario_name"] == "medium_infantry_team"
    assert body["scenario"]["scenario_id"] == "medium-infantry-team"
    assert len(body["scenario"]["career_cells"]) == 4
    assert len(body["scenario"]["rate_overrides"]) == 1
    assert len(body["scenario"]["accession_overrides"]) == 1


def test_directory_backed_named_scenarios_preserve_processing_rule_difference() -> None:
    """Directory-backed fixtures should preserve rule differences through named comparison flows."""
    client = TestClient(app)

    response = client.post(
        "/api/projection/compare-named",
        json={
            "baseline_scenario_name": "medium_unordered_sequential",
            "variant_scenario_name": "medium_unordered_phased",
        },
    )

    assert response.status_code == 200
    comparison = response.json()["comparison"]
    assert comparison["baseline"]["metadata"]["processing_rule"] == SEQUENTIAL_RULE
    assert comparison["variant"]["metadata"]["processing_rule"] == PHASED_RULE
    assert comparison["inventory_delta"] == -1
    assert comparison["gap_delta"] == -1


def test_directory_backed_policy_fixture_changes_outcome_from_named_baseline() -> None:
    """Directory-backed policy fixtures should behave like other named policy variants."""
    client = TestClient(app)

    response = client.post(
        "/api/projection/compare-named",
        json={
            "baseline_scenario_name": "baseline_small",
            "variant_scenario_name": "medium_policy_team",
        },
    )

    assert response.status_code == 200
    comparison = response.json()["comparison"]
    assert comparison["baseline"]["metadata"]["processing_rule"] == SEQUENTIAL_RULE
    assert comparison["variant"]["metadata"]["processing_rule"] == SEQUENTIAL_RULE
    assert comparison["inventory_delta"] > 0
    assert comparison["summary"]["largest_inventory_gains"][0]["cell_id"] == "0311-E4"


def test_shared_force_pack_named_scenario_definition_returns_expanded_payload() -> None:
    """Pack-backed named scenarios should expand into the stable scenario definition payload."""
    client = TestClient(app)

    response = client.get("/api/projection/scenarios/synthetic_enlisted_baseline/definition")

    assert response.status_code == 200
    body = response.json()
    assert body["scenario"]["scenario_id"] == "synthetic-enlisted-baseline"
    assert len(body["scenario"]["career_cells"]) == 19
    assert len(body["scenario"]["transitions"]) == 38
    assert body["scenario"]["metadata"]["source"] == "synthetic-force-pack"


def test_shared_force_pack_variant_changes_cyber_outcome_without_new_topology() -> None:
    """Two named scenarios should be able to share one force pack and diverge through local adjustments and overrides."""
    client = TestClient(app)

    response = client.post(
        "/api/projection/compare-named",
        json={
            "baseline_scenario_name": "synthetic_enlisted_baseline",
            "variant_scenario_name": "synthetic_enlisted_cyber_push",
        },
    )

    assert response.status_code == 200
    comparison = response.json()["comparison"]
    assert comparison["baseline"]["metadata"]["processing_rule"] == PHASED_RULE
    assert comparison["variant"]["metadata"]["processing_rule"] == PHASED_RULE
    assert comparison["inventory_delta"] > 0
    assert any(item["cell_id"] == "1721-E4" and item["inventory_delta"] > 0 for item in comparison["cell_deltas"])
    assert any(item["cell_id"] == "1721-E5" and item["inventory_delta"] > 0 for item in comparison["cell_deltas"])



def test_named_pack_backed_projection_exposes_group_rollups() -> None:
    """Pack-backed named runs should expose app-local group summaries derived from reference context."""
    client = TestClient(app)

    response = client.get("/api/projection/scenarios/synthetic_enlisted_baseline")

    assert response.status_code == 200
    summary = response.json()["result"]["summary"]
    assert [item["key"] for item in summary["by_community"]] == [
        "aviation-maintenance",
        "communications",
        "cyber",
        "infantry",
        "infantry-leadership",
        "motor-transport",
    ]
    cyber = next(item for item in summary["by_community"] if item["key"] == "cyber")
    assert cyber["inventory"] == 95
    assert cyber["demand"] == 93
    assert cyber["gap"] == 2
    assert [item["key"] for item in summary["by_force_element"]] == ["ace", "ce", "gce", "lce", "mig"]
    mig = next(item for item in summary["by_force_element"] if item["key"] == "mig")
    assert mig["inventory"] == 95
    assert mig["demand"] == 93
    assert mig["gap"] == 2
    assert [item["key"] for item in summary["by_occfld"]] == ["03", "06", "17", "35", "61"]


def test_inline_projection_run_keeps_group_rollups_empty_without_reference_context() -> None:
    """Inline runs should not invent pack-group summaries when no reference context exists."""
    client = TestClient(app)
    payload = json.loads(Path("scenarios/baseline_small.json").read_text())

    response = client.post("/api/projection/run", json=payload)

    assert response.status_code == 200
    summary = response.json()["result"]["summary"]
    assert summary["by_occfld"] == []
    assert summary["by_community"] == []
    assert summary["by_force_element"] == []



def test_named_pack_backed_comparison_exposes_group_deltas_and_group_drivers() -> None:
    """Pack-backed named comparisons should expose app-local grouped deltas and narrative drivers."""
    client = TestClient(app)

    response = client.post(
        '/api/projection/compare-named',
        json={
            'baseline_scenario_name': 'synthetic_enlisted_baseline',
            'variant_scenario_name': 'synthetic_enlisted_cyber_push',
        },
    )

    assert response.status_code == 200
    summary = response.json()['comparison']['summary']
    assert [item['key'] for item in summary['by_community']] == [
        'aviation-maintenance',
        'communications',
        'cyber',
        'infantry',
        'infantry-leadership',
        'motor-transport',
    ]
    cyber = next(item for item in summary['by_community'] if item['key'] == 'cyber')
    assert cyber['inventory_delta'] > 0
    assert cyber['gap_delta'] > 0
    mig = next(item for item in summary['by_force_element'] if item['key'] == 'mig')
    assert mig['inventory_delta'] > 0
    assert mig['gap_delta'] > 0
    assert any(driver['title'] == 'Top Community Driver: cyber' for driver in summary['drivers'])
    assert any(driver['title'] == 'Top Force Element Driver: mig' for driver in summary['drivers'])
    assert summary['takeaways'][0] == f'Both scenarios used {PHASED_RULE}.'
    assert any('Strongest community shift is cyber' in item for item in summary['takeaways'])
    assert summary['watchlist'][0]['title'] == 'community watch: cyber'
    assert summary['watchlist'][0]['metric'] == 'gap_delta'
    assert summary['explanations'][0]['title'] == 'Top community shift: cyber'
    assert any('Linked force element: mig moved' in item for item in summary['explanations'][0]['reason_trail'])


def test_named_pack_backed_comparison_exposes_authorization_basis() -> None:
    client = TestClient(app)

    response = client.post(
        '/api/projection/compare-named',
        json={
            'baseline_scenario_name': 'synthetic_enlisted_baseline',
            'variant_scenario_name': 'synthetic_enlisted_cyber_push',
        },
    )

    assert response.status_code == 200
    basis = response.json()['comparison']['summary']['authorization_basis']
    assert basis['baseline']['source'] == 'authorization'
    assert basis['variant']['source'] == 'authorization'
    assert basis['baseline']['artifact_id'] == 'authorization_usmc_enlisted_fy2028_v1'
    assert basis['variant']['artifact_id'] == 'authorization_usmc_enlisted_fy2028_v1'
    assert 'use explicit authorization semantics on both sides' in basis['description']


def test_inline_comparison_keeps_group_deltas_empty_without_reference_context() -> None:
    """Inline comparisons should not invent grouped deltas when no pack reference context exists."""
    client = TestClient(app)

    response = client.post(
        '/api/projection/compare-named',
        json={
            'baseline_scenario_name': 'baseline_small',
            'variant_scenario_name': 'baseline_boosted',
        },
    )

    assert response.status_code == 200
    summary = response.json()['comparison']['summary']
    assert summary['by_occfld'] == []
    assert summary['by_community'] == []
    assert summary['by_force_element'] == []
    assert summary['authorization_basis']['baseline']['source'] == 'none'
    assert summary['authorization_basis']['variant']['source'] == 'none'



def test_named_comparison_export_preserves_grouped_deltas_in_json_artifact() -> None:
    client = TestClient(app)

    response = client.post(
        '/api/projection/compare-named-export',
        json={
            'baseline_scenario_name': 'synthetic_enlisted_baseline',
            'variant_scenario_name': 'synthetic_enlisted_cyber_push',
            'format': 'json',
        },
    )

    assert response.status_code == 200
    artifact = response.json()['artifact']
    assert artifact['kind'] == 'comparison_export'
    content = json.loads(artifact['content'])
    summary = content['comparison']['summary']
    assert any(item['key'] == 'cyber' and item['inventory_delta'] > 0 for item in summary['by_community'])
    assert any(item['key'] == 'mig' and item['inventory_delta'] > 0 for item in summary['by_force_element'])


def test_named_comparison_summary_export_returns_compact_csv_artifact() -> None:
    client = TestClient(app)

    response = client.post(
        '/api/projection/compare-named-export-summary',
        json={
            'baseline_scenario_name': 'synthetic_enlisted_baseline',
            'variant_scenario_name': 'synthetic_enlisted_cyber_push',
        },
    )

    assert response.status_code == 200
    artifact = response.json()['artifact']
    assert artifact['kind'] == 'comparison_summary_export'
    assert artifact['format'] == 'csv'
    assert artifact['filename'].startswith('synthetic-enlisted-baseline-vs-synthetic-enlisted-cyber-push-summary-')
    assert '# kind: comparison_summary_export' in artifact['content']
    assert '# section: watchlist' in artifact['content']
    assert '# section: explanations' in artifact['content']
    assert '# section: community_deltas' in artifact['content']
    assert '# section: baseline_fill_by_community' in artifact['content']
    assert '# section: variant_readiness_signals' in artifact['content']


def test_named_comparison_save_preserves_grouped_deltas_in_library_record() -> None:
    client = TestClient(app)

    response = client.post(
        '/api/library/comparisons/save-named',
        json={
            'baseline_scenario_name': 'synthetic_enlisted_baseline',
            'variant_scenario_name': 'synthetic_enlisted_cyber_push',
        },
    )

    assert response.status_code == 200
    record = response.json()['record']
    payload = json.loads(Path(record['path']).read_text())
    summary = payload['comparison']['summary']
    assert any(item['key'] == 'cyber' and item['inventory_delta'] > 0 for item in summary['by_community'])
    assert any(item['key'] == 'mig' and item['inventory_delta'] > 0 for item in summary['by_force_element'])


def test_named_pack_backed_projection_exposes_readiness_signals() -> None:
    """Pack-backed named runs should expose app-local readiness pressure signals."""
    client = TestClient(app)

    response = client.get('/api/projection/scenarios/synthetic_enlisted_baseline')

    assert response.status_code == 200
    signals = response.json()['result']['summary']['readiness_signals']
    assert len(signals) > 0
    assert any(item['group_type'] == 'community' and item['key'] == 'infantry' for item in signals)
    assert any(item['group_type'] == 'force_element' and item['key'] == 'gce' for item in signals)
    infantry = next(item for item in signals if item['group_type'] == 'community' and item['key'] == 'infantry')
    assert infantry['status'] == 'stressed'
    assert infantry['gap'] < 0
    assert infantry['fill_rate'] < 0.95
    gce = next(item for item in signals if item['group_type'] == 'force_element' and item['key'] == 'gce')
    assert gce['status'] == 'healthy'


def test_inline_projection_keeps_readiness_signals_empty_without_reference_context() -> None:
    """Inline runs should not invent readiness signals when no pack grouping context exists."""
    client = TestClient(app)
    payload = json.loads(Path('scenarios/baseline_small.json').read_text())

    response = client.post('/api/projection/run', json=payload)

    assert response.status_code == 200
    assert response.json()['result']['summary']['readiness_signals'] == []




def test_named_pack_backed_projection_exposes_fill_summaries() -> None:
    client = TestClient(app)

    response = client.get('/api/projection/scenarios/synthetic_enlisted_baseline')

    assert response.status_code == 200
    summary = response.json()['result']['summary']
    assert [item['key'] for item in summary['fill_by_community']] == [
        'aviation-maintenance',
        'communications',
        'cyber',
        'infantry',
        'infantry-leadership',
        'motor-transport',
    ]
    infantry = next(item for item in summary['fill_by_community'] if item['key'] == 'infantry')
    assert infantry['group_type'] == 'community'
    assert infantry['authorization'] == 900
    assert infantry['inventory'] == 781
    assert infantry['status'] == 'stressed'
    assert infantry['fill_rate'] < 0.95
    gce = next(item for item in summary['fill_by_force_element'] if item['key'] == 'gce')
    assert gce['group_type'] == 'force_element'
    assert gce['authorization'] == 1092
    assert gce['inventory'] == 1042
    assert gce['status'] == 'healthy'


def test_named_pack_backed_projection_exposes_authorization_basis() -> None:
    client = TestClient(app)

    response = client.get('/api/projection/scenarios/synthetic_enlisted_baseline')

    assert response.status_code == 200
    basis = response.json()['result']['summary']['authorization_basis']
    assert basis['source'] == 'authorization'
    assert basis['artifact_id'] == 'authorization_usmc_enlisted_fy2028_v1'
    assert 'explicit authorization data' in basis['description']
    assert 'explicit authorization data' in response.json()['result']['summary']['takeaways'][0]
    assert response.json()['result']['summary']['watchlist'][0]['group_type'] in {'community', 'force_element'}
    assert response.json()['result']['summary']['explanations'][0]['title'].startswith('Top readiness pressure:')


def test_inline_projection_keeps_fill_summaries_empty_without_reference_context() -> None:
    client = TestClient(app)
    payload = json.loads(Path('scenarios/baseline_small.json').read_text())

    response = client.post('/api/projection/run', json=payload)

    assert response.status_code == 200
    summary = response.json()['result']['summary']
    assert summary['fill_by_occfld'] == []
    assert summary['fill_by_community'] == []
    assert summary['fill_by_force_element'] == []
    assert summary['authorization_basis']['source'] == 'none'
