from __future__ import annotations

import pytest

from pathlib import Path

from backend.core.scenario_loader import ScenarioLoader


def test_scenario_loader_lists_directory_manifests() -> None:
    loader = ScenarioLoader(Path("scenarios"))

    names = loader.list_named()

    assert "baseline_small" in names
    assert "medium_infantry_team" in names
    assert "medium_policy_team" in names
    assert "medium_unordered_sequential" in names
    assert "medium_unordered_phased" in names
    assert "synthetic_enlisted_baseline" in names
    assert "synthetic_enlisted_cyber_push" in names


def test_scenario_loader_expands_manifest_refs_into_projection_scenario() -> None:
    loader = ScenarioLoader(Path("scenarios"))

    scenario = loader.load_named("medium_infantry_team")

    assert scenario.scenario_id == "medium-infantry-team"
    assert scenario.metadata.label == "Medium Infantry Team"
    assert len(scenario.career_cells) == 4
    assert len(scenario.transitions) == 8
    by_id = {cell.cell_id: cell for cell in scenario.career_cells}
    assert by_id["0311-E4"].inventory == 77
    assert by_id["0369-E5"].demand == 31
    assert len(scenario.rate_table) == 1
    assert len(scenario.rate_overrides) == 1
    assert len(scenario.accession_table) == 1
    assert len(scenario.accession_overrides) == 1


def test_scenario_loader_preserves_processing_rule_for_directory_manifests() -> None:
    loader = ScenarioLoader(Path("scenarios"))

    sequential = loader.load_named("medium_unordered_sequential")
    phased = loader.load_named("medium_unordered_phased")

    assert sequential.processing_rule == "sequential_declared_order"
    assert phased.processing_rule == "phased_standard_v1"
    assert sequential.transitions[0].transition_type == "loss"
    assert phased.transitions[0].transition_type == "loss"


def test_scenario_loader_expands_policy_overrides_from_directory_manifest() -> None:
    loader = ScenarioLoader(Path("scenarios"))

    scenario = loader.load_named("medium_policy_team")

    assert scenario.scenario_id == "medium-policy-team"
    assert len(scenario.rate_overrides) == 2
    assert len(scenario.accession_overrides) == 1
    assert scenario.metadata.source == "decomposed-policy-fixture"


def test_scenario_loader_rejects_manifest_with_missing_reference_key() -> None:
    scenarios_dir = Path("codex_pytest_tmp/test_scenario_loader_bad_manifest/scenarios")
    scenarios_dir.mkdir(parents=True, exist_ok=True)
    scenario_dir = scenarios_dir / "bad_manifest"
    scenario_dir.mkdir(parents=True, exist_ok=True)
    (scenario_dir / "scenario.json").write_text(
        """{
  "scenario": {
    "scenario_id": "bad-manifest",
    "horizon_years": 2,
    "scenario_refs": {
      "topology": "topology.json",
      "inventory": "inventory.json",
      "demand": "demand.json",
      "rates": "rate_tables.json"
    }
  }
}"""
    )

    loader = ScenarioLoader(scenarios_dir)

    with pytest.raises(Exception, match="accessions"):
        loader.load_named("bad_manifest")


def test_scenario_loader_rejects_unknown_inventory_cell_in_artifact() -> None:
    scenarios_dir = Path("codex_pytest_tmp/test_scenario_loader_bad_inventory/scenarios")
    scenarios_dir.mkdir(parents=True, exist_ok=True)
    scenario_dir = scenarios_dir / "bad_inventory_ref"
    scenario_dir.mkdir(parents=True, exist_ok=True)
    (scenario_dir / "scenario.json").write_text(
        """{
  "scenario": {
    "scenario_id": "bad-inventory-ref",
    "horizon_years": 2,
    "scenario_refs": {
      "topology": "topology.json",
      "inventory": "inventory.json",
      "demand": "demand.json",
      "rates": "rate_tables.json",
      "accessions": "accession_tables.json"
    }
  }
}"""
    )
    (scenario_dir / "topology.json").write_text(
        """{
  "career_cells": [{"cell_id": "0311-E3", "specialty": "0311", "grade": "E3"}],
  "transitions": []
}"""
    )
    (scenario_dir / "inventory.json").write_text(
        """{
  "inventory": [{"cell_id": "missing-cell", "inventory": 10}]
}"""
    )
    (scenario_dir / "demand.json").write_text(
        """{
  "demand": [{"cell_id": "0311-E3", "demand": 10}]
}"""
    )
    (scenario_dir / "rate_tables.json").write_text('{"rate_table": []}')
    (scenario_dir / "accession_tables.json").write_text('{"accession_table": []}')

    loader = ScenarioLoader(scenarios_dir)

    with pytest.raises(ValueError, match="inventory artifact references unknown cell_id 'missing-cell'"):
        loader.load_named("bad_inventory_ref")


def test_scenario_loader_supports_shared_force_pack_references() -> None:
    loader = ScenarioLoader(Path("scenarios"))

    baseline = loader.load_named("synthetic_enlisted_baseline")
    variant = loader.load_named("synthetic_enlisted_cyber_push")

    assert baseline.metadata.source == "synthetic-force-pack"
    assert variant.metadata.source == "synthetic-force-pack"
    assert len(baseline.career_cells) == 19
    assert len(variant.career_cells) == 19
    assert len(baseline.transitions) == 38
    assert len(variant.transitions) == 38
    by_id = {cell.cell_id: cell for cell in variant.career_cells}
    assert by_id["1721-E4"].inventory == 42
    assert by_id["0311-E3"].inventory == 614
    assert by_id["1721-E4"].demand == 48
    assert by_id["6174-E4"].inventory == 96
    assert by_id["0621-E5"].demand == 42
    assert len(variant.rate_overrides) == 2
    assert len(variant.accession_overrides) == 1
    assert by_id["1721-E6"].demand == 14
    assert by_id["6174-E6"].inventory == 22


def test_scenario_loader_exposes_reference_context_for_shared_pack() -> None:
    loader = ScenarioLoader(Path("scenarios"))

    context = loader.load_reference_context("synthetic_enlisted_baseline")

    assert context is not None
    assert context.pack_id == "force_pack_usmc_enlisted_v1"
    assert context.service == "USMC"
    assert context.topology_artifact_id == "topology_usmc_enlisted_v1"
    assert context.inventory_artifact_id == "inventory_usmc_enlisted_fy2028_v1"
    assert context.demand_artifact_id == "demand_usmc_enlisted_fy2028_v1"
    assert context.authorization_artifact_id == "authorization_usmc_enlisted_fy2028_v1"
    assert context.authorization_source == "authorization"
    assert context.authorization_by_cell["0311-E3"] == 600
    assert context.authorization_by_cell["1721-E7"] == 7
    assert context.rate_artifact_id == "rates_usmc_enlisted_v1"
    assert context.accession_artifact_id == "accessions_usmc_enlisted_v1"
    assert context.group_dimensions == ["occfld", "community", "force_element"]
    assert context.cell_groups["1721-E4"] == {
        "occfld": "17",
        "community": "cyber",
        "force_element": "mig",
    }
    assert context.cell_groups["6174-E4"] == {
        "occfld": "61",
        "community": "aviation-maintenance",
        "force_element": "ace",
    }
    assert context.cell_groups["0621-E6"] == {
        "occfld": "06",
        "community": "communications",
        "force_element": "ce",
    }


def test_scenario_loader_returns_no_reference_context_for_monolithic_fixture() -> None:
    loader = ScenarioLoader(Path("scenarios"))

    assert loader.load_reference_context("baseline_small") is None


def test_scenario_loader_falls_back_to_demand_proxy_when_authorization_ref_is_absent() -> None:
    scenarios_dir = Path("codex_pytest_tmp/test_scenario_loader_demand_proxy/scenarios")
    scenarios_dir.mkdir(parents=True, exist_ok=True)
    scenario_dir = scenarios_dir / "demand_proxy_pack"
    scenario_dir.mkdir(parents=True, exist_ok=True)
    (scenario_dir / "scenario.json").write_text(
        """{
  "scenario": {
    "scenario_id": "demand-proxy-pack",
    "horizon_years": 2,
    "scenario_refs": {
      "topology": "topology.json",
      "inventory": "inventory.json",
      "demand": "demand.json",
      "rates": "rate_tables.json",
      "accessions": "accession_tables.json"
    }
  }
}"""
    )
    (scenario_dir / "topology.json").write_text(
        """{
  "artifact_metadata": {"pack_id": "pack-a", "service": "USMC", "group_dimensions": ["occfld"]},
  "career_cells": [{"cell_id": "0311-E3", "specialty": "0311", "grade": "E3", "groups": {"occfld": "03"}}],
  "transitions": []
}"""
    )
    (scenario_dir / "inventory.json").write_text(
        """{
  "artifact_metadata": {"pack_id": "pack-a", "service": "USMC"},
  "inventory": [{"cell_id": "0311-E3", "inventory": 10}]
}"""
    )
    (scenario_dir / "demand.json").write_text(
        """{
  "artifact_metadata": {"pack_id": "pack-a", "service": "USMC"},
  "demand": [{"cell_id": "0311-E3", "demand": 12}]
}"""
    )
    (scenario_dir / "rate_tables.json").write_text(
        '{"artifact_metadata": {"pack_id": "pack-a", "service": "USMC"}, "rate_table": []}'
    )
    (scenario_dir / "accession_tables.json").write_text(
        '{"artifact_metadata": {"pack_id": "pack-a", "service": "USMC"}, "accession_table": []}'
    )

    loader = ScenarioLoader(scenarios_dir)

    context = loader.load_reference_context("demand_proxy_pack")

    assert context is not None
    assert context.authorization_artifact_id is None
    assert context.authorization_source == "demand_proxy"
    assert context.authorization_by_cell == {"0311-E3": 12}


def test_scenario_loader_rejects_authorization_artifact_with_incomplete_cell_coverage() -> None:
    scenarios_dir = Path("codex_pytest_tmp/test_scenario_loader_bad_authorization/scenarios")
    scenarios_dir.mkdir(parents=True, exist_ok=True)
    scenario_dir = scenarios_dir / "bad_authorization"
    scenario_dir.mkdir(parents=True, exist_ok=True)
    (scenario_dir / "scenario.json").write_text(
        """{
  "scenario": {
    "scenario_id": "bad-authorization",
    "horizon_years": 2,
    "scenario_refs": {
      "topology": "topology.json",
      "inventory": "inventory.json",
      "demand": "demand.json",
      "authorization": "authorization.json",
      "rates": "rate_tables.json",
      "accessions": "accession_tables.json"
    }
  }
}"""
    )
    (scenario_dir / "topology.json").write_text(
        """{
  "artifact_metadata": {"pack_id": "pack-a", "service": "USMC", "group_dimensions": ["occfld"]},
  "career_cells": [
    {"cell_id": "0311-E3", "specialty": "0311", "grade": "E3", "groups": {"occfld": "03"}},
    {"cell_id": "0311-E4", "specialty": "0311", "grade": "E4", "groups": {"occfld": "03"}}
  ],
  "transitions": []
}"""
    )
    (scenario_dir / "inventory.json").write_text(
        """{
  "artifact_metadata": {"pack_id": "pack-a", "service": "USMC"},
  "inventory": [
    {"cell_id": "0311-E3", "inventory": 10},
    {"cell_id": "0311-E4", "inventory": 8}
  ]
}"""
    )
    (scenario_dir / "demand.json").write_text(
        """{
  "artifact_metadata": {"pack_id": "pack-a", "service": "USMC"},
  "demand": [
    {"cell_id": "0311-E3", "demand": 12},
    {"cell_id": "0311-E4", "demand": 9}
  ]
}"""
    )
    (scenario_dir / "authorization.json").write_text(
        """{
  "artifact_metadata": {"pack_id": "pack-a", "service": "USMC"},
  "authorization": [{"cell_id": "0311-E3", "authorization": 14}]
}"""
    )
    (scenario_dir / "rate_tables.json").write_text(
        '{"artifact_metadata": {"pack_id": "pack-a", "service": "USMC"}, "rate_table": []}'
    )
    (scenario_dir / "accession_tables.json").write_text(
        '{"artifact_metadata": {"pack_id": "pack-a", "service": "USMC"}, "accession_table": []}'
    )

    loader = ScenarioLoader(scenarios_dir)

    with pytest.raises(ValueError, match="authorization artifact must cover all topology cell_id values"):
        loader.load_named("bad_authorization")


def test_scenario_loader_rejects_mismatched_pack_ids_across_artifacts() -> None:
    scenarios_dir = Path("codex_pytest_tmp/test_scenario_loader_mismatched_pack/scenarios")
    scenarios_dir.mkdir(parents=True, exist_ok=True)
    scenario_dir = scenarios_dir / "bad_pack_ids"
    scenario_dir.mkdir(parents=True, exist_ok=True)
    (scenario_dir / "scenario.json").write_text(
        """{
  "scenario": {
    "scenario_id": "bad-pack-ids",
    "horizon_years": 2,
    "scenario_refs": {
      "topology": "topology.json",
      "inventory": "inventory.json",
      "demand": "demand.json",
      "rates": "rate_tables.json",
      "accessions": "accession_tables.json"
    }
  }
}"""
    )
    (scenario_dir / "topology.json").write_text(
        """{
  "artifact_metadata": {"pack_id": "pack-a", "group_dimensions": []},
  "career_cells": [{"cell_id": "0311-E3", "specialty": "0311", "grade": "E3"}],
  "transitions": []
}"""
    )
    (scenario_dir / "inventory.json").write_text(
        """{
  "artifact_metadata": {"pack_id": "pack-b"},
  "inventory": [{"cell_id": "0311-E3", "inventory": 10}]
}"""
    )
    (scenario_dir / "demand.json").write_text(
        """{
  "artifact_metadata": {"pack_id": "pack-a"},
  "demand": [{"cell_id": "0311-E3", "demand": 10}]
}"""
    )
    (scenario_dir / "rate_tables.json").write_text('{"artifact_metadata": {"pack_id": "pack-a"}, "rate_table": []}')
    (scenario_dir / "accession_tables.json").write_text('{"artifact_metadata": {"pack_id": "pack-a"}, "accession_table": []}')

    loader = ScenarioLoader(scenarios_dir)

    with pytest.raises(ValueError, match="referenced artifacts must agree on pack_id values"):
        loader.load_named("bad_pack_ids")


def test_scenario_loader_rejects_incomplete_group_dimensions() -> None:
    scenarios_dir = Path("codex_pytest_tmp/test_scenario_loader_bad_groups/scenarios")
    scenarios_dir.mkdir(parents=True, exist_ok=True)
    scenario_dir = scenarios_dir / "bad_groups"
    scenario_dir.mkdir(parents=True, exist_ok=True)
    (scenario_dir / "scenario.json").write_text(
        """{
  "scenario": {
    "scenario_id": "bad-groups",
    "horizon_years": 2,
    "scenario_refs": {
      "topology": "topology.json",
      "inventory": "inventory.json",
      "demand": "demand.json",
      "rates": "rate_tables.json",
      "accessions": "accession_tables.json"
    }
  }
}"""
    )
    (scenario_dir / "topology.json").write_text(
        """{
  "artifact_metadata": {"pack_id": "pack-a", "group_dimensions": ["occfld", "community"]},
  "career_cells": [{"cell_id": "0311-E3", "specialty": "0311", "grade": "E3", "groups": {"occfld": "03"}}],
  "transitions": []
}"""
    )
    (scenario_dir / "inventory.json").write_text('{"artifact_metadata": {"pack_id": "pack-a"}, "inventory": [{"cell_id": "0311-E3", "inventory": 10}]}')
    (scenario_dir / "demand.json").write_text('{"artifact_metadata": {"pack_id": "pack-a"}, "demand": [{"cell_id": "0311-E3", "demand": 10}]}')
    (scenario_dir / "rate_tables.json").write_text('{"artifact_metadata": {"pack_id": "pack-a"}, "rate_table": []}')
    (scenario_dir / "accession_tables.json").write_text('{"artifact_metadata": {"pack_id": "pack-a"}, "accession_table": []}')

    loader = ScenarioLoader(scenarios_dir)

    with pytest.raises(ValueError, match="must define groups"):
        loader.load_named("bad_groups")


