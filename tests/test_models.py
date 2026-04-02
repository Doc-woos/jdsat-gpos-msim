from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.domain.models import ProjectionScenario, RateOverride, RateTableEntry, AccessionOverride


def test_projection_scenario_defaults_app_local_metadata() -> None:
    scenario = ProjectionScenario.model_validate(
        {
            "scenario_id": "metadata-default-check",
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
            "transitions": [],
        }
    )

    assert scenario.metadata.version == "0.1.0"
    assert scenario.metadata.label is None
    assert scenario.metadata.created_by is None
    assert scenario.metadata.source is None
    assert scenario.metadata.notes is None


def test_projection_scenario_rejects_duplicate_cell_ids() -> None:
    with pytest.raises(ValidationError, match="career_cells must use unique cell_id values"):
        ProjectionScenario.model_validate(
            {
                "scenario_id": "duplicate-cell-check",
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
                        "cell_id": "0311-E3",
                        "specialty": "0311",
                        "grade": "E4",
                        "inventory": 5,
                        "demand": 5,
                    },
                ],
                "transitions": [],
            }
        )


def test_projection_scenario_rejects_duplicate_transition_ids() -> None:
    with pytest.raises(ValidationError, match="transitions must use unique transition_id values"):
        ProjectionScenario.model_validate(
            {
                "scenario_id": "duplicate-transition-check",
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
                    },
                ],
                "transitions": [
                    {
                        "transition_id": "prom-dup",
                        "transition_type": "promotion",
                        "source_cell_id": "0311-E3",
                        "target_cell_id": "0311-E4",
                        "rate": 0.1,
                    },
                    {
                        "transition_id": "prom-dup",
                        "transition_type": "promotion",
                        "source_cell_id": "0311-E4",
                        "target_cell_id": "0311-E3",
                        "rate": 0.1,
                    },
                ],
            }
        )


def test_rate_table_entry_requires_at_least_one_cohort_selector() -> None:
    with pytest.raises(ValidationError, match="rate_table entries require at least one cohort selector"):
        RateTableEntry.model_validate(
            {
                "entry_id": "broad-rate-table",
                "transition_type": "promotion",
                "year_start": 1,
                "year_end": 2,
                "rate": 0.2,
            }
        )


def test_rate_override_requires_at_least_one_cohort_selector() -> None:
    with pytest.raises(ValidationError, match="rate_overrides require at least one cohort selector"):
        RateOverride.model_validate(
            {
                "override_id": "broad-rate-override",
                "transition_type": "loss",
                "year_start": 1,
                "year_end": 2,
                "rate_multiplier": 1.1,
            }
        )


def test_accession_override_requires_at_least_one_cohort_selector() -> None:
    with pytest.raises(ValidationError, match="accession_overrides require at least one cohort selector"):
        AccessionOverride.model_validate(
            {
                "override_id": "broad-accession-override",
                "year_start": 1,
                "year_end": 2,
                "amount_delta": 2,
            }
        )
