"""App-local manpower policy helpers."""

from __future__ import annotations

from backend.domain.models import (
    AccessionOverride,
    AccessionTableEntry,
    CareerCell,
    PolicySummary,
    ProjectionScenario,
    RateOverride,
    RateTableEntry,
    Transition,
)


def build_policy_summary(scenario: ProjectionScenario) -> PolicySummary:
    return PolicySummary(
        rate_table_entries=len(scenario.rate_table),
        rate_overrides=len(scenario.rate_overrides),
        accession_table_entries=len(scenario.accession_table),
        accession_overrides=len(scenario.accession_overrides),
    )


def apply_policy_overrides(
    career_cells: list[CareerCell],
    transitions: list[Transition],
    rate_table: list[RateTableEntry],
    rate_overrides: list[RateOverride],
    accession_table: list[AccessionTableEntry],
    accession_overrides: list[AccessionOverride],
    projection_year: int,
) -> list[Transition]:
    if not any([rate_table, rate_overrides, accession_table, accession_overrides]):
        return transitions

    cells_by_id = {cell.cell_id: cell for cell in career_cells}
    effective: list[Transition] = []
    for transition in transitions:
        transition_data = transition.model_dump(mode="python")
        if transition.transition_type == "accession":
            target_cell = cells_by_id.get(transition.target_cell_id or "")
            amount = transition.amount or 0
            matched_table = _select_accession_table_entry(accession_table, target_cell, projection_year)
            if matched_table is not None:
                amount = matched_table.amount
            amount += sum(
                override.amount_delta
                for override in accession_overrides
                if _matches_accession_override(override, target_cell, projection_year)
            )
            transition_data["amount"] = max(0, amount)
        else:
            source_cell = cells_by_id.get(transition.source_cell_id or "")
            target_cell = cells_by_id.get(transition.target_cell_id or "") if transition.target_cell_id else None
            rate = transition.rate or 0.0
            matched_table = _select_rate_table_entry(rate_table, transition, source_cell, target_cell, projection_year)
            if matched_table is not None:
                rate = matched_table.rate
            for override in rate_overrides:
                if _matches_rate_override(override, transition, source_cell, target_cell, projection_year):
                    rate *= override.rate_multiplier
            transition_data["rate"] = max(0.0, rate)
        effective.append(Transition.model_validate(transition_data))
    return effective


def _select_rate_table_entry(
    entries: list[RateTableEntry],
    transition: Transition,
    source_cell: CareerCell | None,
    target_cell: CareerCell | None,
    projection_year: int,
) -> RateTableEntry | None:
    for entry in entries:
        if not _matches_rate_override(entry, transition, source_cell, target_cell, projection_year):
            continue
        return entry
    return None


def _matches_rate_override(
    override: RateTableEntry | RateOverride,
    transition: Transition,
    source_cell: CareerCell | None,
    target_cell: CareerCell | None,
    projection_year: int,
) -> bool:
    if override.transition_type != transition.transition_type:
        return False
    if projection_year < override.year_start or projection_year > override.year_end:
        return False
    if override.source_specialty and (source_cell is None or source_cell.specialty != override.source_specialty):
        return False
    if override.source_grade and (source_cell is None or source_cell.grade != override.source_grade):
        return False
    if override.target_specialty and (target_cell is None or target_cell.specialty != override.target_specialty):
        return False
    if override.target_grade and (target_cell is None or target_cell.grade != override.target_grade):
        return False
    return True


def _select_accession_table_entry(
    entries: list[AccessionTableEntry],
    target_cell: CareerCell | None,
    projection_year: int,
) -> AccessionTableEntry | None:
    for entry in entries:
        if _matches_accession_override(entry, target_cell, projection_year):
            return entry
    return None


def _matches_accession_override(
    override: AccessionTableEntry | AccessionOverride,
    target_cell: CareerCell | None,
    projection_year: int,
) -> bool:
    if projection_year < override.year_start or projection_year > override.year_end:
        return False
    if override.target_specialty and (target_cell is None or target_cell.specialty != override.target_specialty):
        return False
    if override.target_grade and (target_cell is None or target_cell.grade != override.target_grade):
        return False
    return True


__all__ = ["apply_policy_overrides", "build_policy_summary"]
