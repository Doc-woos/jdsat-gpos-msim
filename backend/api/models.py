"""Pydantic API models for the standalone MSim backend."""

from __future__ import annotations

from pydantic import BaseModel, Field

from backend.domain.models import (
    ExportArtifact,
    ExportFormat,
    LibraryRecord,
    ProjectionComparison,
    ProjectionResult,
    ProjectionScenario,
    ScenarioCatalogEntry,
)


class HealthResponse(BaseModel):
    """Health response for the backend."""

    app: str = Field(description="Application identifier")
    status: str = Field(description="Service status")
    slice: str = Field(description="Current implemented slice")


class ProjectionRunRequest(BaseModel):
    """Projection run request payload."""

    scenario: ProjectionScenario


class ProjectionRunResponse(BaseModel):
    """Projection run response payload."""

    result: ProjectionResult


class NamedScenarioListResponse(BaseModel):
    """Available named scenario fixtures."""

    scenario_names: list[str]


class ScenarioCatalogResponse(BaseModel):
    """Analyst-facing named scenario catalog."""

    scenarios: list[ScenarioCatalogEntry]


class ExportCatalogEntry(BaseModel):
    """Analyst-facing export option description."""

    export_id: str
    label: str
    scope: str
    format: str
    endpoint: str
    description: str


class ExportCatalogResponse(BaseModel):
    """Available export artifacts and their intended use."""

    exports: list[ExportCatalogEntry]


class NamedProjectionScenarioResponse(BaseModel):
    """Named scenario definition payload."""

    scenario_name: str
    scenario: ProjectionScenario


class NamedProjectionRunResponse(BaseModel):
    """Named projection run response payload."""

    scenario_name: str
    result: ProjectionResult


class ProjectionComparisonRequest(BaseModel):
    """Projection comparison request payload."""

    baseline: ProjectionScenario
    variant: ProjectionScenario


class NamedProjectionComparisonRequest(BaseModel):
    """Named scenario comparison request payload."""

    baseline_scenario_name: str
    variant_scenario_name: str


class ProjectionComparisonResponse(BaseModel):
    """Projection comparison response payload."""

    comparison: ProjectionComparison


class ProjectionExportRequest(BaseModel):
    """Projection export request payload."""

    scenario: ProjectionScenario
    format: ExportFormat = "json"


class ProjectionExportResponse(BaseModel):
    """Projection export response payload."""

    artifact: ExportArtifact


class ProjectionSummaryExportRequest(BaseModel):
    """Compact projection-summary export request payload."""

    scenario: ProjectionScenario


class ProjectionSummaryExportResponse(BaseModel):
    """Compact projection-summary export response payload."""

    artifact: ExportArtifact


class ProjectionComparisonExportRequest(BaseModel):
    """Projection comparison export request payload."""

    baseline: ProjectionScenario
    variant: ProjectionScenario
    format: ExportFormat = "json"


class NamedProjectionComparisonExportRequest(BaseModel):
    """Named scenario comparison export request payload."""

    baseline_scenario_name: str
    variant_scenario_name: str
    format: ExportFormat = "json"


class ProjectionComparisonExportResponse(BaseModel):
    """Projection comparison export response payload."""

    artifact: ExportArtifact


class ProjectionComparisonSummaryExportRequest(BaseModel):
    """Compact projection comparison-summary export request payload."""

    baseline: ProjectionScenario
    variant: ProjectionScenario


class NamedProjectionComparisonSummaryExportRequest(BaseModel):
    """Compact named comparison-summary export request payload."""

    baseline_scenario_name: str
    variant_scenario_name: str


class ProjectionComparisonSummaryExportResponse(BaseModel):
    """Compact projection comparison-summary export response payload."""

    artifact: ExportArtifact


class LibraryRecordListResponse(BaseModel):
    """List of local workspace library records."""

    records: list[LibraryRecord]


class ScenarioSaveRequest(BaseModel):
    """Save a scenario snapshot to the local workspace library."""

    scenario: ProjectionScenario


class ProjectionRunSaveRequest(BaseModel):
    """Save a projection run record to the local workspace library."""

    scenario: ProjectionScenario


class ProjectionComparisonSaveRequest(BaseModel):
    """Save a comparison run record to the local workspace library."""

    baseline: ProjectionScenario
    variant: ProjectionScenario


class NamedProjectionComparisonSaveRequest(BaseModel):
    """Save a named comparison run to the local workspace library."""

    baseline_scenario_name: str
    variant_scenario_name: str


class LibraryRecordResponse(BaseModel):
    """Single local workspace library record response."""

    record: LibraryRecord
