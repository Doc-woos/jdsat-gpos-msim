"""Analyst-facing summary builders for projection and comparison outputs."""

from __future__ import annotations

from collections import defaultdict

from backend.domain.models import (
    AuthorizationBasis,
    ComparisonAuthorizationBasis,
    ComparisonAggregateDelta,
    ComparisonCellDelta,
    ComparisonDriver,
    FillSummary,
    PolicyDelta,
    PolicySummary,
    ProjectionAggregate,
    ProjectionComparisonSummary,
    ProjectionResult,
    ProjectionSummary,
    ProjectedCell,
    ReadinessSignal,
)


def build_projection_summary(
    projected_inventory: list[ProjectedCell],
    cell_groups: dict[str, dict[str, str]] | None = None,
    authorization_by_cell: dict[str, int] | None = None,
    authorization_source: str = "none",
    authorization_artifact_id: str | None = None,
) -> ProjectionSummary:
    cell_groups = cell_groups or {}
    authorization_by_cell = authorization_by_cell or {}
    by_grade = _aggregate_projected_cells(projected_inventory, "grade")
    by_specialty = _aggregate_projected_cells(projected_inventory, "specialty")
    by_occfld = _aggregate_projected_cells_by_group(projected_inventory, cell_groups, "occfld")
    by_community = _aggregate_projected_cells_by_group(projected_inventory, cell_groups, "community")
    by_force_element = _aggregate_projected_cells_by_group(projected_inventory, cell_groups, "force_element")
    fill_by_occfld = _build_fill_summaries(projected_inventory, cell_groups, authorization_by_cell, "occfld")
    fill_by_community = _build_fill_summaries(projected_inventory, cell_groups, authorization_by_cell, "community")
    fill_by_force_element = _build_fill_summaries(projected_inventory, cell_groups, authorization_by_cell, "force_element")
    readiness_signals = _build_readiness_signals(fill_by_community, fill_by_force_element)
    largest_shortages = sorted(projected_inventory, key=lambda item: item.gap)[:3]
    largest_overages = sorted(projected_inventory, key=lambda item: item.gap, reverse=True)[:3]
    authorization_basis = _build_authorization_basis(
        fill_by_community=fill_by_community,
        authorization_source=authorization_source,
        authorization_artifact_id=authorization_artifact_id,
    )
    return ProjectionSummary(
        by_grade=by_grade,
        by_specialty=by_specialty,
        by_occfld=by_occfld,
        by_community=by_community,
        by_force_element=by_force_element,
        fill_by_occfld=fill_by_occfld,
        fill_by_community=fill_by_community,
        fill_by_force_element=fill_by_force_element,
        authorization_basis=authorization_basis,
        readiness_signals=readiness_signals,
        largest_shortages=largest_shortages,
        largest_overages=largest_overages,
    )


def build_comparison_summary(
    baseline_result: ProjectionResult,
    variant_result: ProjectionResult,
    cell_deltas: list[ComparisonCellDelta],
) -> ProjectionComparisonSummary:
    policy_deltas = _build_policy_deltas(
        baseline_result.metadata.policy_summary,
        variant_result.metadata.policy_summary,
    )
    occfld_deltas = _build_aggregate_deltas(
        baseline_result.summary.by_occfld,
        variant_result.summary.by_occfld,
    )
    community_deltas = _build_aggregate_deltas(
        baseline_result.summary.by_community,
        variant_result.summary.by_community,
    )
    force_element_deltas = _build_aggregate_deltas(
        baseline_result.summary.by_force_element,
        variant_result.summary.by_force_element,
    )
    rule_change = baseline_result.metadata.processing_rule != variant_result.metadata.processing_rule
    if rule_change:
        rule_summary = (
            f"Processing rule changed from {baseline_result.metadata.processing_rule} "
            f"to {variant_result.metadata.processing_rule}."
        )
    else:
        rule_summary = f"Both scenarios used {variant_result.metadata.processing_rule}."

    authorization_basis = _build_comparison_authorization_basis(
        baseline_result.summary.authorization_basis,
        variant_result.summary.authorization_basis,
    )
    return ProjectionComparisonSummary(
        largest_inventory_gains=sorted(cell_deltas, key=lambda item: item.inventory_delta, reverse=True)[:3],
        largest_inventory_losses=sorted(cell_deltas, key=lambda item: item.inventory_delta)[:3],
        largest_gap_improvements=sorted(cell_deltas, key=lambda item: item.gap_delta, reverse=True)[:3],
        largest_gap_worsenings=sorted(cell_deltas, key=lambda item: item.gap_delta)[:3],
        by_occfld=occfld_deltas,
        by_community=community_deltas,
        by_force_element=force_element_deltas,
        authorization_basis=authorization_basis,
        rule_change=rule_change,
        rule_summary=rule_summary,
        policy_deltas=policy_deltas,
        drivers=_build_comparison_drivers(
            baseline_result,
            variant_result,
            cell_deltas,
            policy_deltas,
            rule_summary,
            community_deltas,
            force_element_deltas,
        ),
    )


def _aggregate_projected_cells(projected_inventory: list[ProjectedCell], key_name: str) -> list[ProjectionAggregate]:
    grouped: dict[str, dict[str, int]] = defaultdict(lambda: {"inventory": 0, "demand": 0, "gap": 0})
    for item in projected_inventory:
        key = getattr(item, key_name)
        grouped[key]["inventory"] += item.inventory
        grouped[key]["demand"] += item.demand
        grouped[key]["gap"] += item.gap
    return _build_projection_aggregates(grouped)


def _aggregate_projected_cells_by_group(
    projected_inventory: list[ProjectedCell],
    cell_groups: dict[str, dict[str, str]],
    group_name: str,
) -> list[ProjectionAggregate]:
    grouped: dict[str, dict[str, int]] = defaultdict(lambda: {"inventory": 0, "demand": 0, "gap": 0})
    for item in projected_inventory:
        key = cell_groups.get(item.cell_id, {}).get(group_name)
        if not key:
            continue
        grouped[key]["inventory"] += item.inventory
        grouped[key]["demand"] += item.demand
        grouped[key]["gap"] += item.gap
    return _build_projection_aggregates(grouped)


def _build_projection_aggregates(grouped: dict[str, dict[str, int]]) -> list[ProjectionAggregate]:
    return [ProjectionAggregate(key=key, inventory=values["inventory"], demand=values["demand"], gap=values["gap"]) for key, values in sorted(grouped.items())]


def _build_fill_summaries(
    projected_inventory: list[ProjectedCell],
    cell_groups: dict[str, dict[str, str]],
    authorization_by_cell: dict[str, int],
    group_name: str,
) -> list[FillSummary]:
    grouped: dict[str, dict[str, int]] = defaultdict(lambda: {"inventory": 0, "authorization": 0})
    for item in projected_inventory:
        key = cell_groups.get(item.cell_id, {}).get(group_name)
        if not key:
            continue
        authorization = authorization_by_cell.get(item.cell_id, item.demand)
        grouped[key]["inventory"] += item.inventory
        grouped[key]["authorization"] += authorization
    fills: list[FillSummary] = []
    for key, values in sorted(grouped.items()):
        authorization = values["authorization"]
        if authorization <= 0:
            continue
        inventory = values["inventory"]
        gap = inventory - authorization
        fill_rate = inventory / authorization
        fills.append(
            FillSummary(
                group_type=group_name,
                key=key,
                inventory=inventory,
                authorization=authorization,
                gap=gap,
                fill_rate=round(fill_rate, 4),
                status=_classify_fill_status(fill_rate),
            )
        )
    return fills


def _build_readiness_signals(fill_by_community: list[FillSummary], fill_by_force_element: list[FillSummary]) -> list[ReadinessSignal]:
    signals: list[ReadinessSignal] = []
    for item in [*fill_by_community, *fill_by_force_element]:
        if item.gap >= 0 and item.fill_rate >= 0.95:
            continue
        signals.append(
            ReadinessSignal(
                group_type=item.group_type,
                key=item.key,
                inventory=item.inventory,
                demand=item.authorization,
                gap=item.gap,
                fill_rate=item.fill_rate,
                status=item.status,
            )
        )
    return sorted(signals, key=lambda item: (item.fill_rate, item.gap, item.group_type, item.key))[:6]


def _build_authorization_basis(
    fill_by_community: list[FillSummary],
    authorization_source: str,
    authorization_artifact_id: str | None,
) -> AuthorizationBasis:
    if not fill_by_community:
        return AuthorizationBasis(
            source="none",
            artifact_id=None,
            description="Grouped fill and readiness views are unavailable for scenarios without pack reference context.",
        )
    if authorization_source == "authorization":
        artifact_detail = authorization_artifact_id or "unnamed authorization artifact"
        return AuthorizationBasis(
            source="authorization",
            artifact_id=authorization_artifact_id,
            description=f"Grouped fill and readiness views use explicit authorization data from {artifact_detail}.",
        )
    return AuthorizationBasis(
        source="demand_proxy",
        artifact_id=None,
        description="Grouped fill and readiness views fall back to demand as a proxy because no authorization artifact was provided.",
    )


def _build_comparison_authorization_basis(
    baseline_basis: AuthorizationBasis,
    variant_basis: AuthorizationBasis,
) -> ComparisonAuthorizationBasis:
    if baseline_basis.source == "none" and variant_basis.source == "none":
        description = (
            "Grouped comparison views do not have authorization provenance because neither scenario exposes "
            "pack-backed grouped fill/readiness data."
        )
    elif baseline_basis.source == variant_basis.source:
        basis_label = (
            "explicit authorization"
            if baseline_basis.source == "authorization"
            else baseline_basis.source.replace('_', ' ')
        )
        description = f"Grouped comparison views use {basis_label} semantics on both sides."
    else:
        description = (
            "Grouped comparison views mix authorization semantics across scenarios; review the baseline and variant "
            "authorization basis before interpreting readiness-oriented deltas."
        )
    return ComparisonAuthorizationBasis(
        baseline=baseline_basis,
        variant=variant_basis,
        description=description,
    )


def _classify_fill_status(fill_rate: float) -> str:
    if fill_rate < 0.85:
        return "critical"
    if fill_rate < 0.95:
        return "stressed"
    return "healthy"


def _build_aggregate_deltas(
    baseline: list[ProjectionAggregate],
    variant: list[ProjectionAggregate],
) -> list[ComparisonAggregateDelta]:
    baseline_by_key = {item.key: item for item in baseline}
    variant_by_key = {item.key: item for item in variant}
    deltas: list[ComparisonAggregateDelta] = []
    for key in sorted(set(baseline_by_key) | set(variant_by_key)):
        baseline_item = baseline_by_key.get(key)
        variant_item = variant_by_key.get(key)
        baseline_inventory = 0 if baseline_item is None else baseline_item.inventory
        variant_inventory = 0 if variant_item is None else variant_item.inventory
        baseline_gap = 0 if baseline_item is None else baseline_item.gap
        variant_gap = 0 if variant_item is None else variant_item.gap
        deltas.append(
            ComparisonAggregateDelta(
                key=key,
                baseline_inventory=baseline_inventory,
                variant_inventory=variant_inventory,
                baseline_gap=baseline_gap,
                variant_gap=variant_gap,
                inventory_delta=variant_inventory - baseline_inventory,
                gap_delta=variant_gap - baseline_gap,
            )
        )
    return deltas


def _build_policy_deltas(baseline_policy: PolicySummary, variant_policy: PolicySummary) -> list[PolicyDelta]:
    categories = [
        ("rate_table_entries", "Rate Tables"),
        ("rate_overrides", "Rate Overrides"),
        ("accession_table_entries", "Accession Tables"),
        ("accession_overrides", "Accession Overrides"),
    ]
    return [
        PolicyDelta(
            category=label,
            baseline_count=getattr(baseline_policy, field_name),
            variant_count=getattr(variant_policy, field_name),
            delta=getattr(variant_policy, field_name) - getattr(baseline_policy, field_name),
        )
        for field_name, label in categories
    ]


def _build_comparison_drivers(
    baseline_result: ProjectionResult,
    variant_result: ProjectionResult,
    cell_deltas: list[ComparisonCellDelta],
    policy_deltas: list[PolicyDelta],
    rule_summary: str,
    community_deltas: list[ComparisonAggregateDelta],
    force_element_deltas: list[ComparisonAggregateDelta],
) -> list[ComparisonDriver]:
    drivers: list[ComparisonDriver] = [ComparisonDriver(kind="rule", title="Processing Rule", detail=rule_summary)]
    for delta in policy_deltas:
        if delta.delta == 0:
            continue
        sign = "+" if delta.delta > 0 else ""
        drivers.append(
            ComparisonDriver(
                kind="policy",
                title=delta.category,
                detail=f"Baseline {delta.baseline_count}, variant {delta.variant_count} ({sign}{delta.delta}).",
            )
        )
    for title_prefix, deltas in [("Top Community Driver", community_deltas), ("Top Force Element Driver", force_element_deltas)]:
        strongest_group = _select_strongest_aggregate_delta(deltas)
        if strongest_group is None:
            continue
        direction = "gain" if strongest_group.inventory_delta > 0 else "loss"
        drivers.append(
            ComparisonDriver(
                kind="outcome",
                title=f"{title_prefix}: {strongest_group.key}",
                detail=(
                    f"{strongest_group.key} saw an inventory {direction} of {abs(strongest_group.inventory_delta)} "
                    f"and a gap change of {strongest_group.gap_delta:+d}."
                ),
            )
        )
    strongest = sorted(cell_deltas, key=lambda item: (abs(item.inventory_delta), abs(item.gap_delta)), reverse=True)[:3]
    for item in strongest:
        if item.inventory_delta == 0 and item.gap_delta == 0:
            continue
        direction = "gain" if item.inventory_delta > 0 else "loss"
        detail = f"{item.cell_id} saw an inventory {direction} of {abs(item.inventory_delta)} and a gap change of {item.gap_delta:+d}."
        drivers.append(ComparisonDriver(kind="outcome", title=f"Top Cell Driver: {item.cell_id}", detail=detail))
    if len(drivers) == 1:
        drivers.append(
            ComparisonDriver(
                kind="outcome",
                title="No Material Delta",
                detail=(
                    f"{baseline_result.metadata.scenario_metadata.label or baseline_result.scenario_id} and "
                    f"{variant_result.metadata.scenario_metadata.label or variant_result.scenario_id} produced matching policy counts and near-identical cell outcomes."
                ),
            )
        )
    return drivers


def _select_strongest_aggregate_delta(deltas: list[ComparisonAggregateDelta]) -> ComparisonAggregateDelta | None:
    meaningful = [item for item in deltas if item.inventory_delta != 0 or item.gap_delta != 0]
    if not meaningful:
        return None
    return sorted(meaningful, key=lambda item: (abs(item.inventory_delta), abs(item.gap_delta), item.key), reverse=True)[0]
