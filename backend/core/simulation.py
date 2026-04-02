"""Simulation orchestration for the first MSim backend slice."""

from __future__ import annotations

from backend.core.gameplan_loader import ensure_gameplan_importable
from backend.core.provenance import build_scenario_fingerprint, build_utc_timestamp
from backend.core.scenario_loader import ScenarioReferenceContext
from backend.core.summary import build_comparison_summary, build_projection_summary
from backend.domain.graph_builder import build_career_flow_graph
from backend.domain.models import (
    ComparisonCellDelta,
    ProcessingRule,
    ProjectionComparison,
    ProjectionMetrics,
    ProjectionResult,
    ProjectionRunMetadata,
    ProjectionScenario,
    ProjectedCell,
)
from backend.domain.policy import apply_policy_overrides, build_policy_summary
from backend.domain.projection import run_projection_year

ensure_gameplan_importable()

from gameplan.engine import Engine


RULE_METADATA: dict[ProcessingRule, tuple[str, str]] = {
    "sequential_declared_order": (
        "ADR-0001",
        "2026-03-25-sequential-rule-baseline",
    ),
    "phased_standard_v1": (
        "ADR-0002",
        "2026-03-25-phased-rule-added",
    ),
}


class ProjectionSimulationService:
    """App-specific orchestration for the deterministic projection slice."""

    def __init__(self) -> None:
        self._engine_name = "gameplan.engine"

    def run(
        self,
        scenario: ProjectionScenario,
        reference_context: ScenarioReferenceContext | None = None,
    ) -> ProjectionResult:
        graph = build_career_flow_graph(scenario)
        engine = Engine()
        engine.step(dt=0.0)

        inventory_by_cell = {cell.cell_id: cell.inventory for cell in scenario.career_cells}
        accumulated = {"promotion": 0, "lateral_move": 0, "loss": 0, "accession": 0}
        decision_ref, checkpoint_ref = RULE_METADATA[scenario.processing_rule]
        run_timestamp = build_utc_timestamp()
        scenario_fingerprint = build_scenario_fingerprint(scenario)
        policy_summary = build_policy_summary(scenario)

        for projection_year in range(1, scenario.horizon_years + 1):
            effective_transitions = apply_policy_overrides(
                career_cells=scenario.career_cells,
                transitions=scenario.transitions,
                rate_table=scenario.rate_table,
                rate_overrides=scenario.rate_overrides,
                accession_table=scenario.accession_table,
                accession_overrides=scenario.accession_overrides,
                projection_year=projection_year,
            )
            yearly = run_projection_year(
                career_cells=scenario.career_cells,
                transitions=effective_transitions,
                inventory_by_cell=inventory_by_cell,
                processing_rule=scenario.processing_rule,
            )
            inventory_by_cell = yearly.inventory_by_cell
            for key, value in yearly.transitions_applied.items():
                accumulated[key] += value

        projected_inventory = [
            ProjectedCell(
                cell_id=cell.cell_id,
                specialty=cell.specialty,
                grade=cell.grade,
                inventory=inventory_by_cell[cell.cell_id],
                demand=cell.demand,
                gap=inventory_by_cell[cell.cell_id] - cell.demand,
            )
            for cell in scenario.career_cells
        ]

        total_inventory = sum(item.inventory for item in projected_inventory)
        total_demand = sum(item.demand for item in projected_inventory)
        cell_groups = {} if reference_context is None else reference_context.cell_groups
        authorization_by_cell = {} if reference_context is None else reference_context.authorization_by_cell
        authorization_source = "none" if reference_context is None else reference_context.authorization_source
        authorization_artifact_id = None if reference_context is None else reference_context.authorization_artifact_id

        return ProjectionResult(
            scenario_id=scenario.scenario_id,
            horizon_years=scenario.horizon_years,
            projected_inventory=projected_inventory,
            metrics=ProjectionMetrics(
                total_inventory=total_inventory,
                total_demand=total_demand,
                total_gap=total_inventory - total_demand,
                transitions_applied=accumulated,
            ),
            summary=build_projection_summary(
                projected_inventory,
                cell_groups=cell_groups,
                authorization_by_cell=authorization_by_cell,
                authorization_source=authorization_source,
                authorization_artifact_id=authorization_artifact_id,
            ),
            metadata=ProjectionRunMetadata(
                engine=self._engine_name,
                graph_nodes=graph.node_count,
                graph_edges=graph.edge_count,
                years_simulated=scenario.horizon_years,
                deterministic=True,
                processing_rule=scenario.processing_rule,
                decision_ref=decision_ref,
                checkpoint_ref=checkpoint_ref,
                run_timestamp=run_timestamp,
                scenario_fingerprint=scenario_fingerprint,
                scenario_metadata=scenario.metadata,
                policy_summary=policy_summary,
            ),
        )

    def compare(
        self,
        baseline: ProjectionScenario,
        variant: ProjectionScenario,
        baseline_reference_context: ScenarioReferenceContext | None = None,
        variant_reference_context: ScenarioReferenceContext | None = None,
    ) -> ProjectionComparison:
        baseline_result = self.run(baseline, reference_context=baseline_reference_context)
        variant_result = self.run(variant, reference_context=variant_reference_context)

        baseline_by_cell = {cell.cell_id: cell for cell in baseline_result.projected_inventory}
        variant_by_cell = {cell.cell_id: cell for cell in variant_result.projected_inventory}
        cell_ids = sorted(set(baseline_by_cell) | set(variant_by_cell))
        cell_deltas: list[ComparisonCellDelta] = []
        for cell_id in cell_ids:
            base = baseline_by_cell.get(cell_id)
            var = variant_by_cell.get(cell_id)
            base_inventory = 0 if base is None else base.inventory
            var_inventory = 0 if var is None else var.inventory
            base_gap = 0 if base is None else base.gap
            var_gap = 0 if var is None else var.gap
            cell_deltas.append(
                ComparisonCellDelta(
                    cell_id=cell_id,
                    inventory_delta=var_inventory - base_inventory,
                    gap_delta=var_gap - base_gap,
                )
            )

        return ProjectionComparison(
            baseline=baseline_result,
            variant=variant_result,
            inventory_delta=variant_result.metrics.total_inventory - baseline_result.metrics.total_inventory,
            gap_delta=variant_result.metrics.total_gap - baseline_result.metrics.total_gap,
            cell_deltas=cell_deltas,
            summary=build_comparison_summary(baseline_result, variant_result, cell_deltas),
        )
