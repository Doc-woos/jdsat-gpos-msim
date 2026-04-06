"""App-local career-flow graph builder."""

from __future__ import annotations

from dataclasses import dataclass

from backend.domain.models import ProjectionScenario, TransitionType


SOURCE_NODE_ID = "__source__"
SINK_NODE_ID = "__sink__"


@dataclass(frozen=True, slots=True)
class CareerNodeData:
    cell_id: str
    specialty: str
    grade: str


@dataclass(frozen=True, slots=True)
class TransitionData:
    transition_id: str
    transition_type: TransitionType


@dataclass(frozen=True, slots=True)
class SimpleEdge:
    source_id: str
    target_id: str
    data: TransitionData


class CareerFlowGraph:
    """Minimal graph contract needed by the app and tests."""

    def __init__(self, nodes: dict[str, CareerNodeData | None], edges: list[SimpleEdge]) -> None:
        self.nodes = nodes
        self.edges = edges
        self.node_count = len(nodes)
        self.edge_count = len(edges)
        self.labels = tuple(sorted({edge.data.transition_type for edge in edges}))


def build_career_flow_graph(scenario: ProjectionScenario) -> CareerFlowGraph:
    nodes: dict[str, CareerNodeData | None] = {
        SOURCE_NODE_ID: None,
        SINK_NODE_ID: None,
    }
    for cell in scenario.career_cells:
        nodes[cell.cell_id] = CareerNodeData(
            cell_id=cell.cell_id,
            specialty=cell.specialty,
            grade=cell.grade,
        )

    edges: list[SimpleEdge] = []
    for transition in scenario.transitions:
        if transition.transition_type == "accession":
            source_id = SOURCE_NODE_ID
            target_id = transition.target_cell_id
        elif transition.transition_type == "loss":
            source_id = transition.source_cell_id
            target_id = SINK_NODE_ID
        else:
            source_id = transition.source_cell_id
            target_id = transition.target_cell_id
        edges.append(
            SimpleEdge(
                source_id=source_id or SOURCE_NODE_ID,
                target_id=target_id or SINK_NODE_ID,
                data=TransitionData(
                    transition_id=transition.transition_id,
                    transition_type=transition.transition_type,
                ),
            )
        )
    return CareerFlowGraph(nodes=nodes, edges=edges)


__all__ = ["SOURCE_NODE_ID", "SINK_NODE_ID", "CareerNodeData", "TransitionData", "build_career_flow_graph"]
