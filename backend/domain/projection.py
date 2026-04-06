"""App-local deterministic projection helpers."""

from __future__ import annotations

from pydantic import BaseModel

from backend.domain.models import CareerCell, ProcessingRule, Transition


class YearStepOutcome(BaseModel):
    inventory_by_cell: dict[str, int]
    transitions_applied: dict[str, int]


PHASE_ORDER: tuple[str, ...] = ("accession", "promotion", "lateral_move", "loss")


def run_projection_year(
    career_cells: list[CareerCell],
    transitions: list[Transition],
    inventory_by_cell: dict[str, int],
    processing_rule: ProcessingRule,
) -> YearStepOutcome:
    inventory = dict(inventory_by_cell)
    transitions_applied = {"promotion": 0, "lateral_move": 0, "loss": 0, "accession": 0}

    ordered_transitions = list(transitions)
    if processing_rule == "phased_standard_v1":
        ordered_transitions = sorted(
            transitions,
            key=lambda item: (PHASE_ORDER.index(item.transition_type), transitions.index(item)),
        )

    for transition in ordered_transitions:
        if transition.transition_type == "accession":
            amount = transition.amount or 0
            inventory[transition.target_cell_id or ""] = inventory.get(transition.target_cell_id or "", 0) + amount
            transitions_applied["accession"] += amount
            continue

        if transition.transition_type in {"promotion", "lateral_move"}:
            source_id = transition.source_cell_id or ""
            target_id = transition.target_cell_id or ""
            moved = round(inventory.get(source_id, 0) * (transition.rate or 0.0))
            moved = min(moved, inventory.get(source_id, 0))
            inventory[source_id] = inventory.get(source_id, 0) - moved
            inventory[target_id] = inventory.get(target_id, 0) + moved
            transitions_applied[transition.transition_type] += moved
            continue

        source_id = transition.source_cell_id or ""
        lost = round(inventory.get(source_id, 0) * (transition.rate or 0.0))
        lost = min(lost, inventory.get(source_id, 0))
        inventory[source_id] = inventory.get(source_id, 0) - lost
        transitions_applied["loss"] += lost

    return YearStepOutcome(inventory_by_cell=inventory, transitions_applied=transitions_applied)


__all__ = ["YearStepOutcome", "run_projection_year"]
