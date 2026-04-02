"""Tests for deterministic first-slice projection logic."""

from __future__ import annotations

from backend.core.simulation import ProjectionSimulationService
from backend.domain.models import CareerCell, ProjectionScenario, Transition
from backend.domain.projection import run_projection_year


def test_run_projection_year_applies_accessions_promotions_and_losses() -> None:
    """One deterministic step should conserve and move inventory as expected."""
    cells = [
        CareerCell(cell_id="0311-E3", specialty="0311", grade="E3", inventory=100),
        CareerCell(cell_id="0311-E4", specialty="0311", grade="E4", inventory=40),
        CareerCell(cell_id="0369-E5", specialty="0369", grade="E5", inventory=10),
    ]
    transitions = [
        Transition(
            transition_id="acc-0311-e3",
            transition_type="accession",
            target_cell_id="0311-E3",
            amount=12,
        ),
        Transition(
            transition_id="prom-0311-e3-e4",
            transition_type="promotion",
            source_cell_id="0311-E3",
            target_cell_id="0311-E4",
            rate=0.1,
        ),
        Transition(
            transition_id="prom-0311-e4-0369-e5",
            transition_type="promotion",
            source_cell_id="0311-E4",
            target_cell_id="0369-E5",
            rate=0.1,
        ),
        Transition(
            transition_id="loss-0311-e3",
            transition_type="loss",
            source_cell_id="0311-E3",
            rate=0.05,
        ),
        Transition(
            transition_id="loss-0311-e4",
            transition_type="loss",
            source_cell_id="0311-E4",
            rate=0.05,
        ),
        Transition(
            transition_id="loss-0369-e5",
            transition_type="loss",
            source_cell_id="0369-E5",
            rate=0.05,
        ),
    ]

    result = run_projection_year(
        career_cells=cells,
        transitions=transitions,
        inventory_by_cell={
            "0311-E3": 100,
            "0311-E4": 40,
            "0369-E5": 10,
        },
        processing_rule="sequential_declared_order",
    )

    assert result.inventory_by_cell == {
        "0311-E3": 96,
        "0311-E4": 44,
        "0369-E5": 14,
    }
    assert result.transitions_applied == {
        "promotion": 16,
        "lateral_move": 0,
        "loss": 8,
        "accession": 12,
    }


def test_phased_rule_reorders_scrambled_transitions() -> None:
    """Phased execution should differ from sequential execution when order is scrambled."""
    cells = [
        CareerCell(cell_id="0311-E3", specialty="0311", grade="E3", inventory=100),
        CareerCell(cell_id="0311-E4", specialty="0311", grade="E4", inventory=40),
        CareerCell(cell_id="0369-E5", specialty="0369", grade="E5", inventory=10),
    ]
    transitions = [
        Transition(
            transition_id="loss-0311-e3",
            transition_type="loss",
            source_cell_id="0311-E3",
            rate=0.05,
        ),
        Transition(
            transition_id="loss-0311-e4",
            transition_type="loss",
            source_cell_id="0311-E4",
            rate=0.05,
        ),
        Transition(
            transition_id="loss-0369-e5",
            transition_type="loss",
            source_cell_id="0369-E5",
            rate=0.05,
        ),
        Transition(
            transition_id="prom-0311-e3-e4",
            transition_type="promotion",
            source_cell_id="0311-E3",
            target_cell_id="0311-E4",
            rate=0.1,
        ),
        Transition(
            transition_id="prom-0311-e4-0369-e5",
            transition_type="promotion",
            source_cell_id="0311-E4",
            target_cell_id="0369-E5",
            rate=0.1,
        ),
        Transition(
            transition_id="acc-0311-e3",
            transition_type="accession",
            target_cell_id="0311-E3",
            amount=12,
        ),
    ]

    sequential = run_projection_year(
        career_cells=cells,
        transitions=transitions,
        inventory_by_cell={
            "0311-E3": 100,
            "0311-E4": 40,
            "0369-E5": 10,
        },
        processing_rule="sequential_declared_order",
    )
    phased = run_projection_year(
        career_cells=cells,
        transitions=transitions,
        inventory_by_cell={
            "0311-E3": 100,
            "0311-E4": 40,
            "0369-E5": 10,
        },
        processing_rule="phased_standard_v1",
    )

    assert sequential.inventory_by_cell != phased.inventory_by_cell
    assert sequential.inventory_by_cell == {
        "0311-E3": 97,
        "0311-E4": 43,
        "0369-E5": 15,
    }
    assert phased.inventory_by_cell == {
        "0311-E3": 96,
        "0311-E4": 44,
        "0369-E5": 14,
    }


def test_scenario_fingerprint_is_deterministic_for_same_payload() -> None:
    """Scenario fingerprints should be stable for semantically identical normalized payloads."""
    service = ProjectionSimulationService()
    scenario = ProjectionScenario.model_validate(
        {
            "scenario_id": "fingerprint-check",
            "horizon_years": 1,
            "metadata": {
                "version": "1.2.3",
                "created_by": "tester",
                "source": "unit-test",
            },
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
                    "transition_id": "acc-0311-e3",
                    "transition_type": "accession",
                    "target_cell_id": "0311-E3",
                    "amount": 0,
                }
            ],
        }
    )

    first = service.run(scenario)
    second = service.run(scenario)

    assert first.metadata.scenario_fingerprint == second.metadata.scenario_fingerprint
    assert len(first.metadata.scenario_fingerprint) == 64
    assert first.metadata.scenario_metadata.version == "1.2.3"
    assert first.metadata.scenario_metadata.created_by == "tester"


def test_rate_table_replaces_base_rate_for_matching_years() -> None:
    """Structured rate table entries should replace matching transition rates."""
    service = ProjectionSimulationService()
    scenario = ProjectionScenario.model_validate(
        {
            "scenario_id": "rate-table-check",
            "horizon_years": 2,
            "career_cells": [
                {
                    "cell_id": "0311-E3",
                    "specialty": "0311",
                    "grade": "E3",
                    "inventory": 100,
                    "demand": 95,
                },
                {
                    "cell_id": "0311-E4",
                    "specialty": "0311",
                    "grade": "E4",
                    "inventory": 40,
                    "demand": 45,
                },
                {
                    "cell_id": "0369-E5",
                    "specialty": "0369",
                    "grade": "E5",
                    "inventory": 10,
                    "demand": 12,
                },
            ],
            "transitions": [
                {
                    "transition_id": "acc-0311-e3",
                    "transition_type": "accession",
                    "target_cell_id": "0311-E3",
                    "amount": 12,
                },
                {
                    "transition_id": "prom-0311-e3-e4",
                    "transition_type": "promotion",
                    "source_cell_id": "0311-E3",
                    "target_cell_id": "0311-E4",
                    "rate": 0.1,
                },
                {
                    "transition_id": "prom-0311-e4-0369-e5",
                    "transition_type": "promotion",
                    "source_cell_id": "0311-E4",
                    "target_cell_id": "0369-E5",
                    "rate": 0.1,
                },
                {
                    "transition_id": "loss-0311-e3",
                    "transition_type": "loss",
                    "source_cell_id": "0311-E3",
                    "rate": 0.05,
                },
                {
                    "transition_id": "loss-0311-e4",
                    "transition_type": "loss",
                    "source_cell_id": "0311-E4",
                    "rate": 0.05,
                },
                {
                    "transition_id": "loss-0369-e5",
                    "transition_type": "loss",
                    "source_cell_id": "0369-E5",
                    "rate": 0.05,
                },
            ],
            "rate_table": [
                {
                    "entry_id": "replace-year-2-e3-promotion",
                    "transition_type": "promotion",
                    "source_specialty": "0311",
                    "source_grade": "E3",
                    "target_specialty": "0311",
                    "target_grade": "E4",
                    "year_start": 2,
                    "year_end": 2,
                    "rate": 0.2,
                }
            ],
        }
    )

    result = service.run(scenario)

    assert result.metrics.total_inventory == 158
    assert result.metrics.transitions_applied["promotion"] == 45
    assert result.projected_inventory[0].inventory == 82
    assert result.projected_inventory[1].inventory == 56
    assert result.projected_inventory[2].inventory == 20
    assert result.metadata.policy_summary.rate_table_entries == 1
    assert result.metadata.policy_summary.rate_overrides == 0


def test_rate_override_stacks_after_rate_table() -> None:
    """Rate overrides should multiply after table replacement rates are selected."""
    service = ProjectionSimulationService()
    scenario = ProjectionScenario.model_validate(
        {
            "scenario_id": "rate-table-plus-override-check",
            "horizon_years": 2,
            "career_cells": [
                {
                    "cell_id": "0311-E3",
                    "specialty": "0311",
                    "grade": "E3",
                    "inventory": 100,
                    "demand": 95,
                },
                {
                    "cell_id": "0311-E4",
                    "specialty": "0311",
                    "grade": "E4",
                    "inventory": 40,
                    "demand": 45,
                },
                {
                    "cell_id": "0369-E5",
                    "specialty": "0369",
                    "grade": "E5",
                    "inventory": 10,
                    "demand": 12,
                },
            ],
            "transitions": [
                {
                    "transition_id": "acc-0311-e3",
                    "transition_type": "accession",
                    "target_cell_id": "0311-E3",
                    "amount": 12,
                },
                {
                    "transition_id": "prom-0311-e3-e4",
                    "transition_type": "promotion",
                    "source_cell_id": "0311-E3",
                    "target_cell_id": "0311-E4",
                    "rate": 0.1,
                },
                {
                    "transition_id": "prom-0311-e4-0369-e5",
                    "transition_type": "promotion",
                    "source_cell_id": "0311-E4",
                    "target_cell_id": "0369-E5",
                    "rate": 0.1,
                },
                {
                    "transition_id": "loss-0311-e3",
                    "transition_type": "loss",
                    "source_cell_id": "0311-E3",
                    "rate": 0.05,
                },
                {
                    "transition_id": "loss-0311-e4",
                    "transition_type": "loss",
                    "source_cell_id": "0311-E4",
                    "rate": 0.05,
                },
                {
                    "transition_id": "loss-0369-e5",
                    "transition_type": "loss",
                    "source_cell_id": "0369-E5",
                    "rate": 0.05,
                },
            ],
            "rate_table": [
                {
                    "entry_id": "replace-year-2-e3-promotion",
                    "transition_type": "promotion",
                    "source_specialty": "0311",
                    "source_grade": "E3",
                    "target_specialty": "0311",
                    "target_grade": "E4",
                    "year_start": 2,
                    "year_end": 2,
                    "rate": 0.2,
                }
            ],
            "rate_overrides": [
                {
                    "override_id": "multiply-year-2-e3-promotion",
                    "transition_type": "promotion",
                    "source_specialty": "0311",
                    "source_grade": "E3",
                    "year_start": 2,
                    "year_end": 2,
                    "rate_multiplier": 1.5,
                }
            ],
        }
    )

    result = service.run(scenario)

    assert result.metrics.total_inventory == 158
    assert result.metrics.transitions_applied["promotion"] == 56
    assert result.projected_inventory[0].inventory == 72
    assert result.projected_inventory[1].inventory == 65
    assert result.projected_inventory[2].inventory == 21


def test_accession_table_replaces_base_amount_for_matching_years() -> None:
    """Structured accession table entries should replace matching accession amounts."""
    service = ProjectionSimulationService()
    scenario = ProjectionScenario.model_validate(
        {
            "scenario_id": "table-replacement-check",
            "horizon_years": 2,
            "career_cells": [
                {
                    "cell_id": "0311-E3",
                    "specialty": "0311",
                    "grade": "E3",
                    "inventory": 100,
                    "demand": 95,
                },
                {
                    "cell_id": "0311-E4",
                    "specialty": "0311",
                    "grade": "E4",
                    "inventory": 40,
                    "demand": 45,
                },
                {
                    "cell_id": "0369-E5",
                    "specialty": "0369",
                    "grade": "E5",
                    "inventory": 10,
                    "demand": 12,
                },
            ],
            "transitions": [
                {
                    "transition_id": "acc-0311-e3",
                    "transition_type": "accession",
                    "target_cell_id": "0311-E3",
                    "amount": 12,
                },
                {
                    "transition_id": "prom-0311-e3-e4",
                    "transition_type": "promotion",
                    "source_cell_id": "0311-E3",
                    "target_cell_id": "0311-E4",
                    "rate": 0.1,
                },
                {
                    "transition_id": "prom-0311-e4-0369-e5",
                    "transition_type": "promotion",
                    "source_cell_id": "0311-E4",
                    "target_cell_id": "0369-E5",
                    "rate": 0.1,
                },
                {
                    "transition_id": "loss-0311-e3",
                    "transition_type": "loss",
                    "source_cell_id": "0311-E3",
                    "rate": 0.05,
                },
                {
                    "transition_id": "loss-0311-e4",
                    "transition_type": "loss",
                    "source_cell_id": "0311-E4",
                    "rate": 0.05,
                },
                {
                    "transition_id": "loss-0369-e5",
                    "transition_type": "loss",
                    "source_cell_id": "0369-E5",
                    "rate": 0.05,
                },
            ],
            "accession_table": [
                {
                    "entry_id": "replace-year-2-e3",
                    "target_specialty": "0311",
                    "target_grade": "E3",
                    "year_start": 2,
                    "year_end": 2,
                    "amount": 20,
                }
            ],
        }
    )

    result = service.run(scenario)

    assert result.metrics.total_inventory == 166
    assert result.metrics.transitions_applied["accession"] == 32
    assert result.projected_inventory[0].cell_id == "0311-E3"
    assert result.projected_inventory[0].inventory == 99


def test_accession_override_stacks_after_accession_table() -> None:
    """Additive accession overrides should apply after table replacement amounts."""
    service = ProjectionSimulationService()
    scenario = ProjectionScenario.model_validate(
        {
            "scenario_id": "table-plus-override-check",
            "horizon_years": 2,
            "career_cells": [
                {
                    "cell_id": "0311-E3",
                    "specialty": "0311",
                    "grade": "E3",
                    "inventory": 100,
                    "demand": 95,
                },
                {
                    "cell_id": "0311-E4",
                    "specialty": "0311",
                    "grade": "E4",
                    "inventory": 40,
                    "demand": 45,
                },
                {
                    "cell_id": "0369-E5",
                    "specialty": "0369",
                    "grade": "E5",
                    "inventory": 10,
                    "demand": 12,
                },
            ],
            "transitions": [
                {
                    "transition_id": "acc-0311-e3",
                    "transition_type": "accession",
                    "target_cell_id": "0311-E3",
                    "amount": 12,
                },
                {
                    "transition_id": "prom-0311-e3-e4",
                    "transition_type": "promotion",
                    "source_cell_id": "0311-E3",
                    "target_cell_id": "0311-E4",
                    "rate": 0.1,
                },
                {
                    "transition_id": "prom-0311-e4-0369-e5",
                    "transition_type": "promotion",
                    "source_cell_id": "0311-E4",
                    "target_cell_id": "0369-E5",
                    "rate": 0.1,
                },
                {
                    "transition_id": "loss-0311-e3",
                    "transition_type": "loss",
                    "source_cell_id": "0311-E3",
                    "rate": 0.05,
                },
                {
                    "transition_id": "loss-0311-e4",
                    "transition_type": "loss",
                    "source_cell_id": "0311-E4",
                    "rate": 0.05,
                },
                {
                    "transition_id": "loss-0369-e5",
                    "transition_type": "loss",
                    "source_cell_id": "0369-E5",
                    "rate": 0.05,
                },
            ],
            "accession_table": [
                {
                    "entry_id": "replace-year-2-e3",
                    "target_specialty": "0311",
                    "target_grade": "E3",
                    "year_start": 2,
                    "year_end": 2,
                    "amount": 20,
                }
            ],
            "accession_overrides": [
                {
                    "override_id": "plus-two-year-2-e3",
                    "target_specialty": "0311",
                    "target_grade": "E3",
                    "year_start": 2,
                    "year_end": 2,
                    "amount_delta": 2,
                }
            ],
        }
    )

    result = service.run(scenario)

    assert result.metrics.total_inventory == 168
    assert result.metrics.transitions_applied["accession"] == 34
    assert result.projected_inventory[0].inventory == 101
