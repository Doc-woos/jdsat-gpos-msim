"""App-local domain models layered on shared GamePlan manpower schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from backend.core.gameplan_loader import ensure_gameplan_importable

ensure_gameplan_importable()

from gameplan.domains.manpower import (
    AccessionOverride as SharedAccessionOverride,
    AccessionTableEntry as SharedAccessionTableEntry,
    CareerCell as SharedCareerCell,
    ComparisonCellDelta as SharedComparisonCellDelta,
    PolicySummary as SharedPolicySummary,
    ProcessingRule,
    ProjectionAggregate as SharedProjectionAggregate,
    ProjectionScenario as SharedProjectionScenario,
    ProjectedCell as SharedProjectedCell,
    RateOverride as SharedRateOverride,
    RateTableEntry as SharedRateTableEntry,
    Transition as SharedTransition,
    TransitionType,
)


DriverKind = Literal["rule", "policy", "outcome"]
ReadinessStatus = Literal["critical", "stressed", "healthy"]
AuthorizationSource = Literal["authorization", "demand_proxy", "none"]


class ScenarioMetadata(BaseModel):
    """Optional descriptive metadata for scenario provenance."""

    version: str = Field(default="0.1.0", min_length=1)
    label: str | None = None
    created_by: str | None = None
    source: str | None = None
    notes: str | None = None


PolicySummary = SharedPolicySummary


class PolicyDelta(BaseModel):
    """Count delta for one policy input category between two scenarios."""

    category: str
    baseline_count: int
    variant_count: int
    delta: int


class ComparisonDriver(BaseModel):
    """Human-readable explanation driver for a comparison result."""

    kind: DriverKind
    title: str
    detail: str


class ScenarioCatalogEntry(BaseModel):
    """Analyst-facing catalog record for a named scenario fixture."""

    scenario_name: str
    scenario_id: str
    label: str
    processing_rule: ProcessingRule
    version: str
    source: str | None
    notes: str | None


CareerCell = SharedCareerCell
Transition = SharedTransition
RateTableEntry = SharedRateTableEntry
RateOverride = SharedRateOverride
AccessionTableEntry = SharedAccessionTableEntry
AccessionOverride = SharedAccessionOverride


class ProjectionScenario(SharedProjectionScenario):
    """Scenario payload for the deterministic projection slice."""

    metadata: ScenarioMetadata = Field(default_factory=ScenarioMetadata)


ProjectedCell = SharedProjectedCell


class ProjectionMetrics(BaseModel):
    """Aggregate metrics for the run."""

    total_inventory: int
    total_demand: int
    total_gap: int
    transitions_applied: dict[str, int]


ProjectionAggregate = SharedProjectionAggregate


class FillSummary(BaseModel):
    """Grouped inventory-versus-authorization fill summary for one app-local dimension."""

    group_type: str
    key: str
    inventory: int
    authorization: int
    gap: int
    fill_rate: float
    status: ReadinessStatus


class ReadinessSignal(BaseModel):
    """App-local readiness pressure signal derived from grouped inventory-vs-demand gaps."""

    group_type: str
    key: str
    inventory: int
    demand: int
    gap: int
    fill_rate: float
    status: ReadinessStatus


class AuthorizationBasis(BaseModel):
    """App-local provenance for grouped fill and readiness calculations."""

    source: AuthorizationSource = "none"
    artifact_id: str | None = None
    description: str


class ComparisonAuthorizationBasis(BaseModel):
    """App-local provenance for comparison-side grouped views."""

    baseline: AuthorizationBasis
    variant: AuthorizationBasis
    description: str


class ComparisonAggregateDelta(BaseModel):
    """Difference between baseline and variant for one aggregate grouping key."""

    key: str
    baseline_inventory: int
    variant_inventory: int
    baseline_gap: int
    variant_gap: int
    inventory_delta: int
    gap_delta: int


class ProjectionSummary(BaseModel):
    """Analyst-facing aggregate summaries for a projection run."""

    by_grade: list[ProjectionAggregate]
    by_specialty: list[ProjectionAggregate]
    by_occfld: list[ProjectionAggregate] = Field(default_factory=list)
    by_community: list[ProjectionAggregate] = Field(default_factory=list)
    by_force_element: list[ProjectionAggregate] = Field(default_factory=list)
    fill_by_occfld: list[FillSummary] = Field(default_factory=list)
    fill_by_community: list[FillSummary] = Field(default_factory=list)
    fill_by_force_element: list[FillSummary] = Field(default_factory=list)
    authorization_basis: AuthorizationBasis = Field(
        default_factory=lambda: AuthorizationBasis(
            source="none",
            description="Grouped fill and readiness views are unavailable for scenarios without pack reference context.",
        )
    )
    readiness_signals: list[ReadinessSignal] = Field(default_factory=list)
    largest_shortages: list[ProjectedCell]
    largest_overages: list[ProjectedCell]


class ProjectionRunMetadata(BaseModel):
    """Execution metadata for the run."""

    engine: str
    graph_nodes: int
    graph_edges: int
    years_simulated: int
    deterministic: bool
    processing_rule: ProcessingRule
    decision_ref: str
    checkpoint_ref: str
    run_timestamp: str
    scenario_fingerprint: str
    scenario_metadata: ScenarioMetadata
    policy_summary: PolicySummary


class ProjectionResult(BaseModel):
    """Stable API result contract for the first slice."""

    scenario_id: str
    horizon_years: int
    projected_inventory: list[ProjectedCell]
    metrics: ProjectionMetrics
    summary: ProjectionSummary
    metadata: ProjectionRunMetadata


ComparisonCellDelta = SharedComparisonCellDelta


class ProjectionComparisonSummary(BaseModel):
    """Analyst-facing summary for baseline-vs-variant comparison."""

    largest_inventory_gains: list[ComparisonCellDelta]
    largest_inventory_losses: list[ComparisonCellDelta]
    largest_gap_improvements: list[ComparisonCellDelta]
    largest_gap_worsenings: list[ComparisonCellDelta]
    by_occfld: list[ComparisonAggregateDelta] = Field(default_factory=list)
    by_community: list[ComparisonAggregateDelta] = Field(default_factory=list)
    by_force_element: list[ComparisonAggregateDelta] = Field(default_factory=list)
    authorization_basis: ComparisonAuthorizationBasis = Field(
        default_factory=lambda: ComparisonAuthorizationBasis(
            baseline=AuthorizationBasis(
                source="none",
                description="Grouped fill and readiness views are unavailable for scenarios without pack reference context.",
            ),
            variant=AuthorizationBasis(
                source="none",
                description="Grouped fill and readiness views are unavailable for scenarios without pack reference context.",
            ),
            description="Grouped comparison views do not have authorization provenance because neither scenario exposes pack-backed grouped fill/readiness data.",
        )
    )
    rule_change: bool
    rule_summary: str
    policy_deltas: list[PolicyDelta]
    drivers: list[ComparisonDriver]


class ProjectionComparison(BaseModel):
    """Comparison result for baseline versus variant runs."""

    baseline: ProjectionResult
    variant: ProjectionResult
    inventory_delta: int
    gap_delta: int
    cell_deltas: list[ComparisonCellDelta]
    summary: ProjectionComparisonSummary


LibraryRecordKind = Literal["scenario", "projection_run", "comparison_run"]


class LibraryRecord(BaseModel):
    """Saved local record in the workspace library."""

    record_id: str
    kind: LibraryRecordKind
    saved_at: str
    label: str
    path: str
    scenario_id: str
    scenario_fingerprint: str
    variant_scenario_id: str | None = None
    variant_scenario_fingerprint: str | None = None


ExportFormat = Literal["json", "csv"]
ExportKind = Literal["projection_export", "comparison_export", "projection_summary_export", "comparison_summary_export"]


class ExportArtifact(BaseModel):
    """Portable export artifact returned by app-local export adapters."""

    kind: ExportKind
    format: ExportFormat
    filename: str
    media_type: str
    content: str
