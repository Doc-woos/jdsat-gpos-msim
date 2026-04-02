"""HTTP routes for the standalone MSim backend."""

from __future__ import annotations

from fastapi import APIRouter

from backend.api.export_catalog import EXPORT_CATALOG
from backend.api.models import (
    ExportCatalogResponse,
    HealthResponse,
    LibraryRecordListResponse,
    LibraryRecordResponse,
    NamedProjectionComparisonExportRequest,
    NamedProjectionComparisonRequest,
    NamedProjectionComparisonSummaryExportRequest,
    NamedProjectionComparisonSaveRequest,
    NamedProjectionRunResponse,
    NamedProjectionScenarioResponse,
    NamedScenarioListResponse,
    ProjectionComparisonExportRequest,
    ProjectionComparisonExportResponse,
    ProjectionComparisonSummaryExportRequest,
    ProjectionComparisonSummaryExportResponse,
    ProjectionComparisonRequest,
    ProjectionComparisonResponse,
    ProjectionComparisonSaveRequest,
    ProjectionExportRequest,
    ProjectionExportResponse,
    ProjectionSummaryExportRequest,
    ProjectionSummaryExportResponse,
    ProjectionRunRequest,
    ProjectionRunResponse,
    ProjectionRunSaveRequest,
    ScenarioCatalogResponse,
    ScenarioSaveRequest,
)
from backend.core.exporter import ProjectionExportService
from backend.core.persistence import WorkspaceLibraryService
from backend.core.provenance import build_scenario_fingerprint, build_utc_timestamp
from backend.core.scenario_loader import ScenarioLoader
from backend.core.simulation import ProjectionSimulationService

router = APIRouter()
projection_service = ProjectionSimulationService()
export_service = ProjectionExportService()
library_service = WorkspaceLibraryService()
scenario_loader = ScenarioLoader()


def _load_named_projection_inputs(scenario_name: str):
    scenario = scenario_loader.load_named(scenario_name)
    reference_context = scenario_loader.load_reference_context(scenario_name)
    return scenario, reference_context


def _run_named_projection(scenario_name: str):
    scenario, reference_context = _load_named_projection_inputs(scenario_name)
    return projection_service.run(scenario, reference_context=reference_context)


def _compare_named_projection_runs(
    baseline_scenario_name: str,
    variant_scenario_name: str,
):
    baseline, baseline_reference_context = _load_named_projection_inputs(baseline_scenario_name)
    variant, variant_reference_context = _load_named_projection_inputs(variant_scenario_name)
    return projection_service.compare(
        baseline,
        variant,
        baseline_reference_context=baseline_reference_context,
        variant_reference_context=variant_reference_context,
    )


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(app="msim", status="ok", slice="projection-mvp")


@router.get("/library/records", response_model=LibraryRecordListResponse)
async def list_library_records() -> LibraryRecordListResponse:
    return LibraryRecordListResponse(records=library_service.list_records())


@router.post("/library/scenarios/save", response_model=LibraryRecordResponse)
async def save_scenario_snapshot(request: ScenarioSaveRequest) -> LibraryRecordResponse:
    fingerprint = build_scenario_fingerprint(request.scenario)
    saved_at = build_utc_timestamp()
    record = library_service.save_scenario(request.scenario, fingerprint, saved_at)
    return LibraryRecordResponse(record=record)


@router.post("/library/runs/save", response_model=LibraryRecordResponse)
async def save_projection_run(request: ProjectionRunSaveRequest) -> LibraryRecordResponse:
    result = projection_service.run(request.scenario)
    record = library_service.save_projection_run(result)
    return LibraryRecordResponse(record=record)


@router.post("/library/comparisons/save", response_model=LibraryRecordResponse)
async def save_comparison_run(request: ProjectionComparisonSaveRequest) -> LibraryRecordResponse:
    comparison = projection_service.compare(request.baseline, request.variant)
    record = library_service.save_comparison_run(comparison)
    return LibraryRecordResponse(record=record)


@router.post("/library/comparisons/save-named", response_model=LibraryRecordResponse)
async def save_named_comparison_run(request: NamedProjectionComparisonSaveRequest) -> LibraryRecordResponse:
    comparison = _compare_named_projection_runs(
        request.baseline_scenario_name,
        request.variant_scenario_name,
    )
    record = library_service.save_comparison_run(comparison)
    return LibraryRecordResponse(record=record)


@router.post("/projection/run", response_model=ProjectionRunResponse)
async def run_projection(request: ProjectionRunRequest) -> ProjectionRunResponse:
    result = projection_service.run(request.scenario)
    return ProjectionRunResponse(result=result)


@router.post("/projection/export", response_model=ProjectionExportResponse)
async def export_projection(request: ProjectionExportRequest) -> ProjectionExportResponse:
    result = projection_service.run(request.scenario)
    artifact = export_service.export_projection(result, request.format)
    return ProjectionExportResponse(artifact=artifact)


@router.post("/projection/export-summary", response_model=ProjectionSummaryExportResponse)
async def export_projection_summary(request: ProjectionSummaryExportRequest) -> ProjectionSummaryExportResponse:
    result = projection_service.run(request.scenario)
    artifact = export_service.export_projection_summary(result)
    return ProjectionSummaryExportResponse(artifact=artifact)


@router.get("/projection/scenarios", response_model=NamedScenarioListResponse)
async def list_named_projection_scenarios() -> NamedScenarioListResponse:
    return NamedScenarioListResponse(scenario_names=scenario_loader.list_named())


@router.get("/projection/catalog", response_model=ScenarioCatalogResponse)
async def list_projection_catalog() -> ScenarioCatalogResponse:
    return ScenarioCatalogResponse(scenarios=scenario_loader.list_catalog())


@router.get("/projection/export-catalog", response_model=ExportCatalogResponse)
async def get_export_catalog() -> ExportCatalogResponse:
    return ExportCatalogResponse(exports=list(EXPORT_CATALOG))


@router.get("/projection/scenarios/{scenario_name}/definition", response_model=NamedProjectionScenarioResponse)
async def get_named_projection_definition(scenario_name: str) -> NamedProjectionScenarioResponse:
    scenario = scenario_loader.load_named(scenario_name)
    return NamedProjectionScenarioResponse(scenario_name=scenario_name, scenario=scenario)


@router.get("/projection/scenarios/{scenario_name}", response_model=NamedProjectionRunResponse)
async def run_named_projection(scenario_name: str) -> NamedProjectionRunResponse:
    result = _run_named_projection(scenario_name)
    return NamedProjectionRunResponse(scenario_name=scenario_name, result=result)


@router.get("/projection/scenarios/{scenario_name}/export-summary", response_model=ProjectionSummaryExportResponse)
async def export_named_projection_summary(scenario_name: str) -> ProjectionSummaryExportResponse:
    result = _run_named_projection(scenario_name)
    artifact = export_service.export_projection_summary(result)
    return ProjectionSummaryExportResponse(artifact=artifact)


@router.post("/projection/compare", response_model=ProjectionComparisonResponse)
async def compare_projection_runs(request: ProjectionComparisonRequest) -> ProjectionComparisonResponse:
    comparison = projection_service.compare(request.baseline, request.variant)
    return ProjectionComparisonResponse(comparison=comparison)


@router.post("/projection/compare-export", response_model=ProjectionComparisonExportResponse)
async def export_projection_comparison(request: ProjectionComparisonExportRequest) -> ProjectionComparisonExportResponse:
    comparison = projection_service.compare(request.baseline, request.variant)
    artifact = export_service.export_comparison(comparison, request.format)
    return ProjectionComparisonExportResponse(artifact=artifact)


@router.post("/projection/compare-export-summary", response_model=ProjectionComparisonSummaryExportResponse)
async def export_projection_comparison_summary(
    request: ProjectionComparisonSummaryExportRequest,
) -> ProjectionComparisonSummaryExportResponse:
    comparison = projection_service.compare(request.baseline, request.variant)
    artifact = export_service.export_comparison_summary(comparison)
    return ProjectionComparisonSummaryExportResponse(artifact=artifact)


@router.post("/projection/compare-named", response_model=ProjectionComparisonResponse)
async def compare_named_projection_runs(request: NamedProjectionComparisonRequest) -> ProjectionComparisonResponse:
    comparison = _compare_named_projection_runs(
        request.baseline_scenario_name,
        request.variant_scenario_name,
    )
    return ProjectionComparisonResponse(comparison=comparison)


@router.post("/projection/compare-named-export", response_model=ProjectionComparisonExportResponse)
async def export_named_projection_comparison(
    request: NamedProjectionComparisonExportRequest,
) -> ProjectionComparisonExportResponse:
    comparison = _compare_named_projection_runs(
        request.baseline_scenario_name,
        request.variant_scenario_name,
    )
    artifact = export_service.export_comparison(comparison, request.format)
    return ProjectionComparisonExportResponse(artifact=artifact)


@router.post("/projection/compare-named-export-summary", response_model=ProjectionComparisonSummaryExportResponse)
async def export_named_projection_comparison_summary(
    request: NamedProjectionComparisonSummaryExportRequest,
) -> ProjectionComparisonSummaryExportResponse:
    comparison = _compare_named_projection_runs(
        request.baseline_scenario_name,
        request.variant_scenario_name,
    )
    artifact = export_service.export_comparison_summary(comparison)
    return ProjectionComparisonSummaryExportResponse(artifact=artifact)
