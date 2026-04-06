from __future__ import annotations

from backend.core.summary import build_projection_summary
from backend.domain.models import ProjectedCell


def test_build_projection_summary_aggregates_grade_and_specialty_views() -> None:
    projected_inventory = [
        ProjectedCell(cell_id="0311-E3", specialty="0311", grade="E3", inventory=10, demand=12, gap=-2),
        ProjectedCell(cell_id="0311-E4", specialty="0311", grade="E4", inventory=8, demand=8, gap=0),
        ProjectedCell(cell_id="1721-E3", specialty="1721", grade="E3", inventory=6, demand=4, gap=2),
    ]

    summary = build_projection_summary(projected_inventory)

    assert [item.key for item in summary.by_grade] == ["E3", "E4"]
    assert summary.by_grade[0].inventory == 16
    assert summary.by_grade[0].demand == 16
    assert summary.by_grade[0].gap == 0
    assert [item.key for item in summary.by_specialty] == ["0311", "1721"]
    assert summary.by_occfld == []
    assert summary.by_community == []
    assert summary.by_force_element == []
    assert summary.fill_by_occfld == []
    assert summary.fill_by_community == []
    assert summary.fill_by_force_element == []
    assert summary.authorization_basis.source == "none"
    assert summary.readiness_signals == []
    assert summary.watchlist == []
    assert summary.takeaways[0] == "Grouped fill and readiness views are unavailable for scenarios without pack reference context."
    assert "No grouped readiness pressure signals are currently active." in summary.takeaways
    assert summary.explanations[0].title == "Top cell shortage: 0311-E3"
    assert "Demand basis: cell demand is 12." in summary.explanations[0].reason_trail
    assert summary.largest_shortages[0].cell_id == "0311-E3"
    assert summary.largest_overages[0].cell_id == "1721-E3"


def test_build_projection_summary_aggregates_app_local_group_views_when_available() -> None:
    projected_inventory = [
        ProjectedCell(cell_id="0311-E3", specialty="0311", grade="E3", inventory=10, demand=12, gap=-2),
        ProjectedCell(cell_id="0311-E4", specialty="0311", grade="E4", inventory=8, demand=8, gap=0),
        ProjectedCell(cell_id="1721-E4", specialty="1721", grade="E4", inventory=6, demand=4, gap=2),
    ]

    summary = build_projection_summary(
        projected_inventory,
        cell_groups={
            "0311-E3": {"occfld": "03", "community": "infantry", "force_element": "gce"},
            "0311-E4": {"occfld": "03", "community": "infantry", "force_element": "gce"},
            "1721-E4": {"occfld": "17", "community": "cyber", "force_element": "mig"},
        },
    )

    assert [item.key for item in summary.by_occfld] == ["03", "17"]
    assert summary.by_occfld[0].inventory == 18
    assert [item.key for item in summary.by_community] == ["cyber", "infantry"]
    infantry = next(item for item in summary.by_community if item.key == "infantry")
    assert infantry.inventory == 18
    assert infantry.demand == 20
    assert infantry.gap == -2
    assert [item.key for item in summary.by_force_element] == ["gce", "mig"]
    assert summary.fill_by_community[0].group_type == "community"
    assert summary.fill_by_community[0].key == "cyber"
    infantry_fill = next(item for item in summary.fill_by_community if item.key == "infantry")
    assert infantry_fill.authorization == 20
    assert infantry_fill.fill_rate == 0.9
    assert infantry_fill.status == "stressed"
    assert summary.authorization_basis.source == "demand_proxy"
    assert summary.readiness_signals[0].group_type == "community"
    assert summary.readiness_signals[0].key == "infantry"
    assert summary.readiness_signals[0].status == "stressed"
    assert summary.watchlist[0].title == "community watch: infantry"
    assert summary.watchlist[0].value == "90%"
    assert summary.watchlist[0].metric == "fill_rate"
    assert summary.watchlist[0].severity == "stressed"
    assert summary.takeaways[0] == "Grouped fill and readiness views fall back to demand as a proxy because no authorization artifact was provided."
    assert "Top readiness pressure is community infantry at 90% fill with a -2 gap." in summary.takeaways
    assert summary.explanations[0].title == "Top readiness pressure: community infantry"
    assert "Demand basis: demand-proxy authorization." in summary.explanations[0].reason_trail
    assert "Top linked force element: gce is -2 against authorization at 90% fill." in summary.explanations[0].reason_trail
    assert summary.explanations[1].title == "Top cell shortage: 0311-E3"
    assert "Contributing community: infantry is -2 against demand proxy." in summary.explanations[1].reason_trail


def test_build_projection_summary_emits_critical_readiness_signal_for_low_fill_group() -> None:
    projected_inventory = [
        ProjectedCell(cell_id="0311-E3", specialty="0311", grade="E3", inventory=8, demand=20, gap=-12),
    ]

    summary = build_projection_summary(
        projected_inventory,
        cell_groups={
            "0311-E3": {"occfld": "03", "community": "infantry", "force_element": "gce"},
        },
    )

    assert summary.fill_by_community[0].group_type == "community"
    assert summary.fill_by_community[0].key == "infantry"
    assert summary.fill_by_community[0].fill_rate == 0.4
    assert summary.fill_by_community[0].status == "critical"
    assert summary.readiness_signals[0].group_type == "community"
    assert summary.readiness_signals[0].key == "infantry"
    assert summary.readiness_signals[0].fill_rate == 0.4
    assert summary.readiness_signals[0].status == "critical"
    assert summary.watchlist[0].severity == "critical"
    assert summary.watchlist[0].value == "40%"
    assert "Top readiness pressure is community infantry at 40% fill with a -12 gap." in summary.takeaways
    assert "Dominant gap: -12 at 40% fill." in summary.explanations[0].reason_trail


def test_build_projection_summary_prefers_explicit_authorization_over_demand_for_fill_views() -> None:
    projected_inventory = [
        ProjectedCell(cell_id="0311-E3", specialty="0311", grade="E3", inventory=10, demand=12, gap=-2),
    ]

    summary = build_projection_summary(
        projected_inventory,
        cell_groups={
            "0311-E3": {"occfld": "03", "community": "infantry", "force_element": "gce"},
        },
        authorization_by_cell={"0311-E3": 20},
        authorization_source="authorization",
        authorization_artifact_id="auth-pack-v1",
    )

    assert summary.by_community[0].demand == 12
    assert summary.fill_by_community[0].authorization == 20
    assert summary.authorization_basis.source == "authorization"
    assert summary.authorization_basis.artifact_id == "auth-pack-v1"
    assert summary.fill_by_community[0].fill_rate == 0.5
    assert summary.fill_by_community[0].status == "critical"
    assert summary.readiness_signals[0].demand == 20
    assert summary.watchlist[0].detail == "infantry is -10 against authorization at 50% fill."
    assert summary.takeaways[0] == "Grouped fill and readiness views use explicit authorization data from auth-pack-v1."
    assert "Demand basis: explicit authorization from auth-pack-v1." in summary.explanations[0].reason_trail


def test_build_comparison_summary_includes_group_deltas_and_group_drivers() -> None:
    from backend.core.summary import build_comparison_summary
    from backend.domain.models import ProjectionMetrics, ProjectionResult, ProjectionRunMetadata, ProjectionSummary, ScenarioMetadata, PolicySummary, ProjectionAggregate, ComparisonCellDelta

    baseline = ProjectionResult(
        scenario_id='baseline',
        horizon_years=1,
        projected_inventory=[],
        metrics=ProjectionMetrics(total_inventory=10, total_demand=10, total_gap=0, transitions_applied={'promotion': 0, 'lateral_move': 0, 'loss': 0, 'accession': 0}),
        summary=ProjectionSummary(
            by_grade=[],
            by_specialty=[],
            by_occfld=[ProjectionAggregate(key='03', inventory=18, demand=20, gap=-2)],
            by_community=[ProjectionAggregate(key='infantry', inventory=18, demand=20, gap=-2)],
            by_force_element=[ProjectionAggregate(key='gce', inventory=18, demand=20, gap=-2)],
            fill_by_occfld=[],
            fill_by_community=[],
            fill_by_force_element=[],
            authorization_basis={"source": "demand_proxy", "artifact_id": None, "description": "baseline demand proxy"},
            readiness_signals=[],
            watchlist=[],
            largest_shortages=[],
            largest_overages=[],
        ),
        metadata=ProjectionRunMetadata(
            engine='gameplan.engine',
            graph_nodes=1,
            graph_edges=1,
            years_simulated=1,
            deterministic=True,
            processing_rule='sequential_declared_order',
            decision_ref='ADR-0001',
            checkpoint_ref='checkpoint',
            run_timestamp='2026-03-27T00:00:00Z',
            scenario_fingerprint='a' * 64,
            scenario_metadata=ScenarioMetadata(label='Baseline'),
            policy_summary=PolicySummary(rate_table_entries=0, rate_overrides=0, accession_table_entries=0, accession_overrides=0),
        ),
    )
    variant = ProjectionResult(
        scenario_id='variant',
        horizon_years=1,
        projected_inventory=[],
        metrics=ProjectionMetrics(total_inventory=14, total_demand=10, total_gap=4, transitions_applied={'promotion': 0, 'lateral_move': 0, 'loss': 0, 'accession': 0}),
        summary=ProjectionSummary(
            by_grade=[],
            by_specialty=[],
            by_occfld=[ProjectionAggregate(key='03', inventory=22, demand=20, gap=2)],
            by_community=[ProjectionAggregate(key='infantry', inventory=22, demand=20, gap=2)],
            by_force_element=[ProjectionAggregate(key='gce', inventory=22, demand=20, gap=2)],
            fill_by_occfld=[],
            fill_by_community=[],
            fill_by_force_element=[],
            authorization_basis={"source": "authorization", "artifact_id": "auth-pack-v1", "description": "variant explicit auth"},
            readiness_signals=[],
            watchlist=[],
            largest_shortages=[],
            largest_overages=[],
        ),
        metadata=ProjectionRunMetadata(
            engine='gameplan.engine',
            graph_nodes=1,
            graph_edges=1,
            years_simulated=1,
            deterministic=True,
            processing_rule='sequential_declared_order',
            decision_ref='ADR-0001',
            checkpoint_ref='checkpoint',
            run_timestamp='2026-03-27T00:00:00Z',
            scenario_fingerprint='b' * 64,
            scenario_metadata=ScenarioMetadata(label='Variant'),
            policy_summary=PolicySummary(rate_table_entries=0, rate_overrides=1, accession_table_entries=0, accession_overrides=0),
        ),
    )

    summary = build_comparison_summary(
        baseline,
        variant,
        [ComparisonCellDelta(cell_id='0311-E4', inventory_delta=4, gap_delta=4)],
    )

    assert summary.by_community[0].key == 'infantry'
    assert summary.by_community[0].inventory_delta == 4
    assert summary.authorization_basis.baseline.source == 'demand_proxy'
    assert summary.authorization_basis.variant.source == 'authorization'
    assert 'mix authorization semantics' in summary.authorization_basis.description
    assert summary.by_force_element[0].key == 'gce'
    assert summary.by_force_element[0].gap_delta == 4
    assert any(driver.title == 'Top Community Driver: infantry' for driver in summary.drivers)
    assert any(driver.title == 'Top Force Element Driver: gce' for driver in summary.drivers)
    assert summary.watchlist[0].title == 'community watch: infantry'
    assert summary.watchlist[0].severity == 'improving'
    assert summary.watchlist[0].value == '+4'
    assert summary.takeaways[0] == 'Both scenarios used sequential_declared_order.'
    assert 'mix authorization semantics' in summary.takeaways[1]
    assert 'Strongest community shift is infantry with +4 inventory and +4 gap.' in summary.takeaways
    assert summary.explanations[0].title == 'Top community shift: infantry'
    assert 'Dominant change: +4 inventory and +4 gap.' in summary.explanations[0].reason_trail
    assert 'Linked force element: gce moved +4 inventory and +4 gap.' in summary.explanations[0].reason_trail
    assert 'Policy context: Rate Overrides changed from 0 to 1 (+1).' in summary.explanations[0].reason_trail
