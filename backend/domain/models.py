"""App-local manpower models and contracts for the standalone MSim app."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


ProcessingRule = Literal["sequential_declared_order", "phased_standard_v1"]
TransitionType = Literal["accession", "promotion", "lateral_move", "loss"]
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


class CareerCell(BaseModel):
    """One inventory-bearing career cell."""

    cell_id: str = Field(min_length=1)
    specialty: str = Field(min_length=1)
    grade: str = Field(min_length=1)
    inventory: int = Field(ge=0)
    demand: int = Field(default=0, ge=0)


class Transition(BaseModel):
    """One transition between career cells or system boundaries."""

    transition_id: str = Field(min_length=1)
    transition_type: TransitionType
    source_cell_id: str | None = None
    target_cell_id: str | None = None
    rate: float | None = Field(default=None, ge=0.0)
    amount: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_shape(self) -> "Transition":
        if self.transition_type == "accession":
            if self.target_cell_id is None or self.amount is None:
                raise ValueError("accession transitions require target_cell_id and amount")
            return self
        if self.transition_type in {"promotion", "lateral_move"}:
            if self.source_cell_id is None or self.target_cell_id is None or self.rate is None:
                raise ValueError(
                    f"{self.transition_type} transitions require source_cell_id, target_cell_id, and rate"
                )
            return self
        if self.transition_type == "loss":
            if self.source_cell_id is None or self.rate is None:
                raise ValueError("loss transitions require source_cell_id and rate")
        return self


class RateTableEntry(BaseModel):
    """Rate replacement entry for matching cohorts and year windows."""

    entry_id: str = Field(min_length=1)
    transition_type: TransitionType
    source_specialty: str | None = None
    source_grade: str | None = None
    target_specialty: str | None = None
    target_grade: str | None = None
    year_start: int = Field(default=1, ge=1)
    year_end: int = Field(default=10_000, ge=1)
    rate: float = Field(ge=0.0)

    @model_validator(mode="after")
    def validate_selectors(self) -> "RateTableEntry":
        if self.year_end < self.year_start:
            raise ValueError("year_end must be greater than or equal to year_start")
        if not any([self.source_specialty, self.source_grade, self.target_specialty, self.target_grade]):
            raise ValueError("rate_table entries require at least one cohort selector")
        return self


class RateOverride(BaseModel):
    """Rate multiplier applied after base or table-derived rate selection."""

    override_id: str = Field(min_length=1)
    transition_type: TransitionType
    source_specialty: str | None = None
    source_grade: str | None = None
    target_specialty: str | None = None
    target_grade: str | None = None
    year_start: int = Field(default=1, ge=1)
    year_end: int = Field(default=10_000, ge=1)
    rate_multiplier: float = Field(ge=0.0)

    @model_validator(mode="after")
    def validate_selectors(self) -> "RateOverride":
        if self.year_end < self.year_start:
            raise ValueError("year_end must be greater than or equal to year_start")
        if not any([self.source_specialty, self.source_grade, self.target_specialty, self.target_grade]):
            raise ValueError("rate_overrides require at least one cohort selector")
        return self


class AccessionTableEntry(BaseModel):
    """Accession amount replacement entry for matching cohorts and year windows."""

    entry_id: str = Field(min_length=1)
    target_specialty: str | None = None
    target_grade: str | None = None
    year_start: int = Field(default=1, ge=1)
    year_end: int = Field(default=10_000, ge=1)
    amount: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_selectors(self) -> "AccessionTableEntry":
        if self.year_end < self.year_start:
            raise ValueError("year_end must be greater than or equal to year_start")
        if not any([self.target_specialty, self.target_grade]):
            raise ValueError("accession_table entries require at least one cohort selector")
        return self


class AccessionOverride(BaseModel):
    """Signed additive accession override after base or table-derived selection."""

    override_id: str = Field(min_length=1)
    target_specialty: str | None = None
    target_grade: str | None = None
    year_start: int = Field(default=1, ge=1)
    year_end: int = Field(default=10_000, ge=1)
    amount_delta: int

    @model_validator(mode="after")
    def validate_selectors(self) -> "AccessionOverride":
        if self.year_end < self.year_start:
            raise ValueError("year_end must be greater than or equal to year_start")
        if not any([self.target_specialty, self.target_grade]):
            raise ValueError("accession_overrides require at least one cohort selector")
        return self


class PolicySummary(BaseModel):
    """Counts of policy input categories applied to a scenario."""

    rate_table_entries: int
    rate_overrides: int
    accession_table_entries: int
    accession_overrides: int


class ProjectionScenario(BaseModel):
    """Scenario payload for the deterministic projection slice."""

    scenario_id: str = Field(min_length=1)
    horizon_years: int = Field(ge=1)
    processing_rule: ProcessingRule = "sequential_declared_order"
    metadata: ScenarioMetadata = Field(default_factory=ScenarioMetadata)
    career_cells: list[CareerCell] = Field(min_length=1)
    transitions: list[Transition]
    rate_table: list[RateTableEntry] = Field(default_factory=list)
    rate_overrides: list[RateOverride] = Field(default_factory=list)
    accession_table: list[AccessionTableEntry] = Field(default_factory=list)
    accession_overrides: list[AccessionOverride] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_shape(self) -> "ProjectionScenario":
        cell_ids = [cell.cell_id for cell in self.career_cells]
        if len(cell_ids) != len(set(cell_ids)):
            raise ValueError("career_cells must use unique cell_id values")
        transition_ids = [transition.transition_id for transition in self.transitions]
        if len(transition_ids) != len(set(transition_ids)):
            raise ValueError("transitions must use unique transition_id values")
        known_cell_ids = set(cell_ids)
        for transition in self.transitions:
            if transition.source_cell_id and transition.source_cell_id not in known_cell_ids:
                raise ValueError(f"transition '{transition.transition_id}' references unknown source_cell_id '{transition.source_cell_id}'")
            if transition.target_cell_id and transition.target_cell_id not in known_cell_ids:
                raise ValueError(f"transition '{transition.transition_id}' references unknown target_cell_id '{transition.target_cell_id}'")
        return self


class ProjectedCell(BaseModel):
    """Projected post-run cell state."""

    cell_id: str
    specialty: str
    grade: str
    inventory: int
    demand: int
    gap: int


class ProjectionAggregate(BaseModel):
    """Aggregate inventory/demand/gap summary."""

    key: str
    inventory: int
    demand: int
    gap: int


class ComparisonCellDelta(BaseModel):
    """Cell-level delta between baseline and variant."""

    cell_id: str
    inventory_delta: int
    gap_delta: int


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


class AnalystExplanation(BaseModel):
    """Structured analyst-facing explanation for one grouped outcome or delta."""

    title: str
    scope: str
    group_type: str | None = None
    key: str | None = None
    reason_trail: list[str] = Field(default_factory=list)


class WatchlistItem(BaseModel):
    """Ranked analyst watchlist item for a grouped risk or delta hotspot."""

    title: str
    scope: str
    group_type: str
    key: str
    severity: str
    metric: str
    value: str
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


class ProjectionMetrics(BaseModel):
    """Aggregate metrics for the run."""

    total_inventory: int
    total_demand: int
    total_gap: int
    transitions_applied: dict[str, int]


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
    watchlist: list[WatchlistItem] = Field(default_factory=list)
    takeaways: list[str] = Field(default_factory=list)
    explanations: list[AnalystExplanation] = Field(default_factory=list)
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
    watchlist: list[WatchlistItem] = Field(default_factory=list)
    takeaways: list[str] = Field(default_factory=list)
    explanations: list[AnalystExplanation] = Field(default_factory=list)


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
