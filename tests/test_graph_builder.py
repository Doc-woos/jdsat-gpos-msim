"""Tests for the career-flow graph builder."""

from __future__ import annotations

from backend.domain.graph_builder import SOURCE_NODE_ID, SINK_NODE_ID, build_career_flow_graph
from backend.domain.models import CareerCell, ProjectionScenario, Transition


def test_build_career_flow_graph_creates_expected_nodes_and_edges() -> None:
    """The graph builder should include pseudo source/sink nodes and transitions."""
    scenario = ProjectionScenario(
        scenario_id="graph-test",
        horizon_years=1,
        career_cells=[
            CareerCell(cell_id="0311-E3", specialty="0311", grade="E3", inventory=10),
            CareerCell(cell_id="0311-E4", specialty="0311", grade="E4", inventory=5),
        ],
        transitions=[
            Transition(
                transition_id="acc",
                transition_type="accession",
                target_cell_id="0311-E3",
                amount=3,
            ),
            Transition(
                transition_id="prom",
                transition_type="promotion",
                source_cell_id="0311-E3",
                target_cell_id="0311-E4",
                rate=0.2,
            ),
            Transition(
                transition_id="loss",
                transition_type="loss",
                source_cell_id="0311-E4",
                rate=0.1,
            ),
        ],
    )

    graph = build_career_flow_graph(scenario)

    assert SOURCE_NODE_ID in graph.nodes
    assert SINK_NODE_ID in graph.nodes
    assert graph.node_count == 4
    assert graph.edge_count == 3
    assert set(graph.labels) == {"accession", "loss", "promotion"}
