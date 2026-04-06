"""Analyst-facing summary builders for projection and comparison outputs."""

from __future__ import annotations

from collections import defaultdict

from backend.domain.models import (
    AnalystExplanation,
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
    WatchlistItem,
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
    takeaways = _build_projection_takeaways(
        authorization_basis=authorization_basis,
        readiness_signals=readiness_signals,
        largest_shortages=largest_shortages,
        largest_overages=largest_overages,
    )
    explanations = _build_projection_explanations(
        authorization_basis=authorization_basis,
        readiness_signals=readiness_signals,
        largest_shortages=largest_shortages,
        fill_by_community=fill_by_community,
        fill_by_force_element=fill_by_force_element,
        cell_groups=cell_groups,
    )
    watchlist = _build_projection_watchlist(
        authorization_basis=authorization_basis,
        readiness_signals=readiness_signals,
        fill_by_community=fill_by_community,
        fill_by_force_element=fill_by_force_element,
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
        watchlist=watchlist,
        takeaways=takeaways,
        explanations=explanations,
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
    takeaways = _build_comparison_takeaways(
        baseline_result=baseline_result,
        variant_result=variant_result,
        rule_summary=rule_summary,
        authorization_basis=authorization_basis,
        community_deltas=community_deltas,
        force_element_deltas=force_element_deltas,
        policy_deltas=policy_deltas,
    )
    explanations = _build_comparison_explanations(
        authorization_basis=authorization_basis,
        rule_summary=rule_summary,
        community_deltas=community_deltas,
        force_element_deltas=force_element_deltas,
        policy_deltas=policy_deltas,
    )
    watchlist = _build_comparison_watchlist(
        authorization_basis=authorization_basis,
        community_deltas=community_deltas,
        force_element_deltas=force_element_deltas,
        policy_deltas=policy_deltas,
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
        watchlist=watchlist,
        takeaways=takeaways,
        explanations=explanations,
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


def _build_projection_takeaways(
    authorization_basis: AuthorizationBasis,
    readiness_signals: list[ReadinessSignal],
    largest_shortages: list[ProjectedCell],
    largest_overages: list[ProjectedCell],
) -> list[str]:
    takeaways: list[str] = [authorization_basis.description]
    if readiness_signals:
        top_signal = readiness_signals[0]
        takeaways.append(
            f"Top readiness pressure is {top_signal.group_type} {top_signal.key} at "
            f"{round(top_signal.fill_rate * 100)}% fill with a {signed_int(top_signal.gap)} gap."
        )
    else:
        takeaways.append("No grouped readiness pressure signals are currently active.")

    if largest_shortages:
        top_shortage = largest_shortages[0]
        takeaways.append(
            f"Largest cell shortage is {top_shortage.cell_id} at {top_shortage.inventory}/{top_shortage.demand} "
            f"with a {signed_int(top_shortage.gap)} gap."
        )
    elif largest_overages:
        top_overage = largest_overages[0]
        takeaways.append(
            f"Largest positive inventory cushion is {top_overage.cell_id} at {top_overage.inventory}/{top_overage.demand} "
            f"with a {signed_int(top_overage.gap)} gap."
        )
    return takeaways


def _build_projection_explanations(
    authorization_basis: AuthorizationBasis,
    readiness_signals: list[ReadinessSignal],
    largest_shortages: list[ProjectedCell],
    fill_by_community: list[FillSummary],
    fill_by_force_element: list[FillSummary],
    cell_groups: dict[str, dict[str, str]],
) -> list[AnalystExplanation]:
    explanations: list[AnalystExplanation] = []
    if readiness_signals:
        top_signal = readiness_signals[0]
        explanations.append(
            AnalystExplanation(
                title=f"Top readiness pressure: {top_signal.group_type} {top_signal.key}",
                scope="projection",
                group_type=top_signal.group_type,
                key=top_signal.key,
                reason_trail=[
                    f"Demand basis: {_authorization_basis_label(authorization_basis)}.",
                    f"Dominant gap: {signed_int(top_signal.gap)} at {round(top_signal.fill_rate * 100)}% fill.",
                    _linked_group_reason(
                        signal=top_signal,
                        fill_by_community=fill_by_community,
                        fill_by_force_element=fill_by_force_element,
                    ),
                ],
            )
        )
    if largest_shortages:
        top_shortage = largest_shortages[0]
        group_info = cell_groups.get(top_shortage.cell_id, {})
        reasons = [
            f"Demand basis: cell demand is {top_shortage.demand}.",
            f"Dominant gap: {signed_int(top_shortage.gap)} at {top_shortage.inventory}/{top_shortage.demand}.",
        ]
        if group_info.get("community"):
            related_community = _find_fill_summary(fill_by_community, group_info["community"])
            if related_community is not None:
                reasons.append(
                    f"Contributing community: {group_info['community']} is {signed_int(related_community.gap)} "
                    f"against {_authorization_noun(authorization_basis)}."
                )
        if group_info.get("force_element"):
            related_force_element = _find_fill_summary(fill_by_force_element, group_info["force_element"])
            if related_force_element is not None:
                reasons.append(
                    f"Contributing force element: {group_info['force_element']} is {signed_int(related_force_element.gap)} "
                    f"against {_authorization_noun(authorization_basis)}."
                )
        explanations.append(
            AnalystExplanation(
                title=f"Top cell shortage: {top_shortage.cell_id}",
                scope="projection",
                group_type="cell",
                key=top_shortage.cell_id,
                reason_trail=reasons,
            )
        )
    return explanations


def _build_projection_watchlist(
    authorization_basis: AuthorizationBasis,
    readiness_signals: list[ReadinessSignal],
    fill_by_community: list[FillSummary],
    fill_by_force_element: list[FillSummary],
) -> list[WatchlistItem]:
    items: list[WatchlistItem] = []
    for signal in readiness_signals[:3]:
        items.append(
            WatchlistItem(
                title=f"{signal.group_type} watch: {signal.key}",
                scope="projection",
                group_type=signal.group_type,
                key=signal.key,
                severity=signal.status,
                metric="fill_rate",
                value=f"{round(signal.fill_rate * 100)}%",
                detail=(
                    f"{signal.key} is {signed_int(signal.gap)} against {_authorization_noun(authorization_basis)} "
                    f"at {round(signal.fill_rate * 100)}% fill."
                ),
            )
        )
    for summary in _top_negative_fill_summaries(fill_by_community, limit=2):
        items.append(
            WatchlistItem(
                title=f"community watch: {summary.key}",
                scope="projection",
                group_type="community",
                key=summary.key,
                severity=summary.status,
                metric="gap",
                value=signed_int(summary.gap),
                detail=(
                    f"{summary.key} is {signed_int(summary.gap)} against {_authorization_noun(authorization_basis)} "
                    f"with {round(summary.fill_rate * 100)}% fill."
                ),
            )
        )
    for summary in _top_negative_fill_summaries(fill_by_force_element, limit=2):
        items.append(
            WatchlistItem(
                title=f"force_element watch: {summary.key}",
                scope="projection",
                group_type="force_element",
                key=summary.key,
                severity=summary.status,
                metric="gap",
                value=signed_int(summary.gap),
                detail=(
                    f"{summary.key} is {signed_int(summary.gap)} against {_authorization_noun(authorization_basis)} "
                    f"with {round(summary.fill_rate * 100)}% fill."
                ),
            )
        )
    return _dedupe_watchlist(items)


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


def _build_comparison_takeaways(
    baseline_result: ProjectionResult,
    variant_result: ProjectionResult,
    rule_summary: str,
    authorization_basis: ComparisonAuthorizationBasis,
    community_deltas: list[ComparisonAggregateDelta],
    force_element_deltas: list[ComparisonAggregateDelta],
    policy_deltas: list[PolicyDelta],
) -> list[str]:
    takeaways = [rule_summary, authorization_basis.description]
    strongest_community = _select_strongest_aggregate_delta(community_deltas)
    if strongest_community is not None:
        takeaways.append(
            f"Strongest community shift is {strongest_community.key} with "
            f"{signed_int(strongest_community.inventory_delta)} inventory and "
            f"{signed_int(strongest_community.gap_delta)} gap."
        )
    strongest_force_element = _select_strongest_aggregate_delta(force_element_deltas)
    if strongest_force_element is not None:
        takeaways.append(
            f"Strongest force-element shift is {strongest_force_element.key} with "
            f"{signed_int(strongest_force_element.inventory_delta)} inventory and "
            f"{signed_int(strongest_force_element.gap_delta)} gap."
        )
    changed_policies = [delta for delta in policy_deltas if delta.delta != 0]
    if changed_policies:
        first_policy = changed_policies[0]
        takeaways.append(
            f"Primary policy count change is {first_policy.category}: "
            f"{first_policy.baseline_count} to {first_policy.variant_count} "
            f"({signed_int(first_policy.delta)})."
        )
    elif baseline_result.metrics.total_inventory == variant_result.metrics.total_inventory and baseline_result.metrics.total_gap == variant_result.metrics.total_gap:
        takeaways.append("Baseline and variant totals are unchanged, so differences are limited to distribution or metadata.")
    return takeaways


def _build_comparison_explanations(
    authorization_basis: ComparisonAuthorizationBasis,
    rule_summary: str,
    community_deltas: list[ComparisonAggregateDelta],
    force_element_deltas: list[ComparisonAggregateDelta],
    policy_deltas: list[PolicyDelta],
) -> list[AnalystExplanation]:
    explanations: list[AnalystExplanation] = []
    strongest_community = _select_strongest_aggregate_delta(community_deltas)
    strongest_force_element = _select_strongest_aggregate_delta(force_element_deltas)
    leading_policy = next((delta for delta in policy_deltas if delta.delta != 0), None)
    if strongest_community is not None:
        reasons = [
            f"Authorization basis: {authorization_basis.description}",
            f"Dominant change: {signed_int(strongest_community.inventory_delta)} inventory and {signed_int(strongest_community.gap_delta)} gap.",
            _linked_delta_reason("force element", strongest_force_element),
        ]
        if leading_policy is not None:
            reasons.append(_policy_delta_reason(leading_policy))
        else:
            reasons.append(rule_summary)
        explanations.append(
            AnalystExplanation(
                title=f"Top community shift: {strongest_community.key}",
                scope="comparison",
                group_type="community",
                key=strongest_community.key,
                reason_trail=reasons,
            )
        )
    if strongest_force_element is not None:
        reasons = [
            f"Authorization basis: {authorization_basis.description}",
            f"Dominant change: {signed_int(strongest_force_element.inventory_delta)} inventory and {signed_int(strongest_force_element.gap_delta)} gap.",
            _linked_delta_reason("community", strongest_community),
        ]
        if leading_policy is not None:
            reasons.append(_policy_delta_reason(leading_policy))
        else:
            reasons.append(rule_summary)
        explanations.append(
            AnalystExplanation(
                title=f"Top force-element shift: {strongest_force_element.key}",
                scope="comparison",
                group_type="force_element",
                key=strongest_force_element.key,
                reason_trail=reasons,
            )
        )
    return explanations


def _build_comparison_watchlist(
    authorization_basis: ComparisonAuthorizationBasis,
    community_deltas: list[ComparisonAggregateDelta],
    force_element_deltas: list[ComparisonAggregateDelta],
    policy_deltas: list[PolicyDelta],
) -> list[WatchlistItem]:
    items: list[WatchlistItem] = []
    for delta in _top_delta_watchlist_items(community_deltas, "community", authorization_basis.description):
        items.append(delta)
    for delta in _top_delta_watchlist_items(force_element_deltas, "force_element", authorization_basis.description):
        items.append(delta)
    for policy_delta in [item for item in policy_deltas if item.delta != 0][:2]:
        items.append(
            WatchlistItem(
                title=f"policy watch: {policy_delta.category}",
                scope="comparison",
                group_type="policy",
                key=policy_delta.category,
                severity="changed",
                metric="delta",
                value=signed_int(policy_delta.delta),
                detail=(
                    f"{policy_delta.category} changed from {policy_delta.baseline_count} to "
                    f"{policy_delta.variant_count} ({signed_int(policy_delta.delta)})."
                ),
            )
        )
    return _dedupe_watchlist(items)


def _classify_fill_status(fill_rate: float) -> str:
    if fill_rate < 0.85:
        return "critical"
    if fill_rate < 0.95:
        return "stressed"
    return "healthy"


def signed_int(value: int) -> str:
    return f"{value:+d}"


def _authorization_basis_label(authorization_basis: AuthorizationBasis) -> str:
    if authorization_basis.source == "authorization":
        artifact_detail = authorization_basis.artifact_id or "explicit authorization"
        return f"explicit authorization from {artifact_detail}"
    if authorization_basis.source == "demand_proxy":
        return "demand-proxy authorization"
    return "unavailable grouped authorization context"


def _authorization_noun(authorization_basis: AuthorizationBasis) -> str:
    if authorization_basis.source == "authorization":
        return "authorization"
    if authorization_basis.source == "demand_proxy":
        return "demand proxy"
    return "group context"


def _find_fill_summary(summaries: list[FillSummary], key: str) -> FillSummary | None:
    for item in summaries:
        if item.key == key:
            return item
    return None


def _linked_group_reason(
    signal: ReadinessSignal,
    fill_by_community: list[FillSummary],
    fill_by_force_element: list[FillSummary],
) -> str:
    if signal.group_type == "community":
        linked = _select_strongest_fill_summary(fill_by_force_element)
        if linked is not None:
            return (
                f"Top linked force element: {linked.key} is {signed_int(linked.gap)} "
                f"against authorization at {round(linked.fill_rate * 100)}% fill."
            )
    if signal.group_type == "force_element":
        linked = _select_strongest_fill_summary(fill_by_community)
        if linked is not None:
            return (
                f"Top linked community: {linked.key} is {signed_int(linked.gap)} "
                f"against authorization at {round(linked.fill_rate * 100)}% fill."
            )
    return "No linked grouped contributor stands out beyond the top signal."


def _select_strongest_fill_summary(summaries: list[FillSummary]) -> FillSummary | None:
    meaningful = [item for item in summaries if item.gap != 0]
    if not meaningful:
        return None
    return sorted(meaningful, key=lambda item: (abs(item.gap), -item.fill_rate, item.key), reverse=True)[0]


def _linked_delta_reason(group_label: str, delta: ComparisonAggregateDelta | None) -> str:
    if delta is None:
        return f"No linked {group_label} delta stands out."
    return (
        f"Linked {group_label}: {delta.key} moved {signed_int(delta.inventory_delta)} inventory "
        f"and {signed_int(delta.gap_delta)} gap."
    )


def _policy_delta_reason(policy_delta: PolicyDelta) -> str:
    return (
        f"Policy context: {policy_delta.category} changed from {policy_delta.baseline_count} "
        f"to {policy_delta.variant_count} ({signed_int(policy_delta.delta)})."
    )


def _top_negative_fill_summaries(summaries: list[FillSummary], limit: int) -> list[FillSummary]:
    filtered = [item for item in summaries if item.gap < 0 or item.fill_rate < 0.95]
    return sorted(filtered, key=lambda item: (item.fill_rate, item.gap, item.key))[:limit]


def _top_delta_watchlist_items(
    deltas: list[ComparisonAggregateDelta],
    group_type: str,
    authorization_description: str,
) -> list[WatchlistItem]:
    ranked = sorted(
        [item for item in deltas if item.inventory_delta != 0 or item.gap_delta != 0],
        key=lambda item: (abs(item.gap_delta), abs(item.inventory_delta), item.key),
        reverse=True,
    )[:2]
    items: list[WatchlistItem] = []
    for delta in ranked:
        severity = "improving" if delta.gap_delta > 0 else "worsening"
        items.append(
            WatchlistItem(
                title=f"{group_type} watch: {delta.key}",
                scope="comparison",
                group_type=group_type,
                key=delta.key,
                severity=severity,
                metric="gap_delta",
                value=signed_int(delta.gap_delta),
                detail=(
                    f"{delta.key} moved {signed_int(delta.inventory_delta)} inventory and "
                    f"{signed_int(delta.gap_delta)} gap. {authorization_description}"
                ),
            )
        )
    return items


def _dedupe_watchlist(items: list[WatchlistItem]) -> list[WatchlistItem]:
    seen: set[tuple[str, str]] = set()
    unique: list[WatchlistItem] = []
    for item in items:
        key = (item.group_type, item.key)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique[:5]


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
