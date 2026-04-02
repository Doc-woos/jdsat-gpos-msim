from __future__ import annotations

from backend.domain.models import ProjectionScenario
from backend.domain.policy import apply_policy_overrides, build_policy_summary


def test_build_policy_summary_counts_each_policy_input_category() -> None:
    scenario = ProjectionScenario.model_validate(
        {
            "scenario_id": "policy-summary-check",
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
                    "transition_id": "acc-0311-e3",
                    "transition_type": "accession",
                    "target_cell_id": "0311-E3",
                    "amount": 1,
                }
            ],
            "rate_table": [
                {
                    "entry_id": "rate-entry",
                    "transition_type": "loss",
                    "source_specialty": "0311",
                    "source_grade": "E3",
                    "year_start": 1,
                    "year_end": 1,
                    "rate": 0.1,
                }
            ],
            "rate_overrides": [
                {
                    "override_id": "rate-override",
                    "transition_type": "loss",
                    "source_specialty": "0311",
                    "source_grade": "E3",
                    "year_start": 1,
                    "year_end": 1,
                    "rate_multiplier": 1.1,
                }
            ],
            "accession_table": [
                {
                    "entry_id": "acc-entry",
                    "target_specialty": "0311",
                    "target_grade": "E3",
                    "year_start": 1,
                    "year_end": 1,
                    "amount": 2,
                }
            ],
            "accession_overrides": [
                {
                    "override_id": "acc-override",
                    "target_specialty": "0311",
                    "target_grade": "E3",
                    "year_start": 1,
                    "year_end": 1,
                    "amount_delta": 1,
                }
            ],
        }
    )

    summary = build_policy_summary(scenario)

    assert summary.rate_table_entries == 1
    assert summary.rate_overrides == 1
    assert summary.accession_table_entries == 1
    assert summary.accession_overrides == 1


def test_apply_policy_overrides_returns_original_transitions_when_no_policy_inputs() -> None:
    scenario = ProjectionScenario.model_validate(
        {
            "scenario_id": "policy-no-op-check",
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
        }
    )

    effective = apply_policy_overrides(
        career_cells=scenario.career_cells,
        transitions=scenario.transitions,
        rate_table=scenario.rate_table,
        rate_overrides=scenario.rate_overrides,
        accession_table=scenario.accession_table,
        accession_overrides=scenario.accession_overrides,
        projection_year=1,
    )

    assert effective is scenario.transitions
