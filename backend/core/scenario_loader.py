"""Scenario loading helpers for named first-slice fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from backend.domain.models import ProjectionScenario, ScenarioCatalogEntry


class ArtifactMetadata(BaseModel):
    """Optional metadata carried by a referenced scenario artifact."""

    artifact_id: str | None = None
    pack_id: str | None = None
    service: str | None = None
    snapshot: str | None = None
    description: str | None = None
    group_dimensions: list[str] = Field(default_factory=list)


class ScenarioRefs(BaseModel):
    """Referenced artifacts for a decomposed scenario manifest."""

    topology: str = Field(min_length=1)
    inventory: str = Field(min_length=1)
    demand: str = Field(min_length=1)
    authorization: str | None = None
    rates: str = Field(min_length=1)
    accessions: str = Field(min_length=1)


class PolicyOverrides(BaseModel):
    """Scenario-local policy overrides applied after baseline artifact expansion."""

    rate_overrides: list[dict] = Field(default_factory=list)
    accession_overrides: list[dict] = Field(default_factory=list)


class CellDelta(BaseModel):
    """Inventory or demand adjustment for one existing cell."""

    cell_id: str = Field(min_length=1)
    delta: int


class ScenarioAdjustments(BaseModel):
    """Scenario-local baseline adjustments applied before policy overrides."""

    inventory_deltas: list[CellDelta] = Field(default_factory=list)
    demand_deltas: list[CellDelta] = Field(default_factory=list)


class DecomposedScenarioManifest(BaseModel):
    """Small scenario manifest that references larger baseline artifacts."""

    scenario_id: str = Field(min_length=1)
    horizon_years: int = Field(ge=1)
    processing_rule: str = Field(default="sequential_declared_order", min_length=1)
    metadata: dict = Field(default_factory=dict)
    scenario_refs: ScenarioRefs
    policy_overrides: PolicyOverrides = Field(default_factory=PolicyOverrides)
    scenario_adjustments: ScenarioAdjustments = Field(default_factory=ScenarioAdjustments)


class TopologyCellArtifact(BaseModel):
    cell_id: str = Field(min_length=1)
    specialty: str = Field(min_length=1)
    grade: str = Field(min_length=1)
    groups: dict[str, str] = Field(default_factory=dict)


class TopologyArtifact(BaseModel):
    artifact_metadata: ArtifactMetadata | None = None
    career_cells: list[TopologyCellArtifact] = Field(min_length=1)
    transitions: list[dict] = Field(default_factory=list)


class InventoryArtifactItem(BaseModel):
    cell_id: str = Field(min_length=1)
    inventory: int = Field(ge=0)


class InventoryArtifact(BaseModel):
    artifact_metadata: ArtifactMetadata | None = None
    inventory: list[InventoryArtifactItem] = Field(default_factory=list)


class DemandArtifactItem(BaseModel):
    cell_id: str = Field(min_length=1)
    demand: int = Field(ge=0)


class DemandArtifact(BaseModel):
    artifact_metadata: ArtifactMetadata | None = None
    demand: list[DemandArtifactItem] = Field(default_factory=list)


class AuthorizationArtifactItem(BaseModel):
    cell_id: str = Field(min_length=1)
    authorization: int = Field(ge=0)


class AuthorizationArtifact(BaseModel):
    artifact_metadata: ArtifactMetadata | None = None
    authorization: list[AuthorizationArtifactItem] = Field(default_factory=list)


class RateArtifact(BaseModel):
    artifact_metadata: ArtifactMetadata | None = None
    rate_table: list[dict] = Field(default_factory=list)


class AccessionArtifact(BaseModel):
    artifact_metadata: ArtifactMetadata | None = None
    accession_table: list[dict] = Field(default_factory=list)


class ScenarioReferenceContext(BaseModel):
    """App-local reference context for a decomposed scenario."""

    scenario_name: str
    pack_id: str | None = None
    service: str | None = None
    topology_artifact_id: str | None = None
    inventory_artifact_id: str | None = None
    demand_artifact_id: str | None = None
    authorization_artifact_id: str | None = None
    authorization_source: str = "demand_proxy"
    rate_artifact_id: str | None = None
    accession_artifact_id: str | None = None
    group_dimensions: list[str] = Field(default_factory=list)
    cell_groups: dict[str, dict[str, str]] = Field(default_factory=dict)
    authorization_by_cell: dict[str, int] = Field(default_factory=dict)


class ScenarioLoader:
    """Load named scenarios from the local scenarios directory."""

    def __init__(self, base_path: Path | None = None) -> None:
        self._base_path = base_path or Path("scenarios")

    def list_named(self) -> list[str]:
        names = {path.stem for path in self._base_path.glob("*.json")}
        names.update(
            path.name for path in self._base_path.iterdir() if path.is_dir() and (path / "scenario.json").exists()
        )
        return sorted(names)

    def list_catalog(self) -> list[ScenarioCatalogEntry]:
        catalog: list[ScenarioCatalogEntry] = []
        for scenario_name in self.list_named():
            scenario = self.load_named(scenario_name)
            label = scenario.metadata.label or scenario.scenario_id
            catalog.append(
                ScenarioCatalogEntry(
                    scenario_name=scenario_name,
                    scenario_id=scenario.scenario_id,
                    label=label,
                    processing_rule=scenario.processing_rule,
                    version=scenario.metadata.version,
                    source=scenario.metadata.source,
                    notes=scenario.metadata.notes,
                )
            )
        return catalog

    def load_named(self, scenario_name: str) -> ProjectionScenario:
        path = self._resolve_named_path(scenario_name)
        payload = json.loads(path.read_text())
        scenario_payload = self._expand_payload(payload["scenario"], path.parent)
        return ProjectionScenario.model_validate(scenario_payload)

    def load_reference_context(self, scenario_name: str) -> ScenarioReferenceContext | None:
        path = self._resolve_named_path(scenario_name)
        payload = json.loads(path.read_text())
        scenario_payload = payload["scenario"]
        if "scenario_refs" not in scenario_payload:
            return None

        manifest = DecomposedScenarioManifest.model_validate(scenario_payload)
        topology = TopologyArtifact.model_validate(self._load_json(path.parent / manifest.scenario_refs.topology))
        inventory = InventoryArtifact.model_validate(self._load_json(path.parent / manifest.scenario_refs.inventory))
        demand = DemandArtifact.model_validate(self._load_json(path.parent / manifest.scenario_refs.demand))
        authorization = self._load_authorization_artifact(path.parent, manifest)
        rates = RateArtifact.model_validate(self._load_json(path.parent / manifest.scenario_refs.rates))
        accessions = AccessionArtifact.model_validate(self._load_json(path.parent / manifest.scenario_refs.accessions))

        self._validate_artifact_consistency(topology, inventory, demand, authorization, rates, accessions)
        self._validate_group_dimensions(topology)

        topology_metadata = topology.artifact_metadata or ArtifactMetadata()
        authorization_metadata = None if authorization is None else authorization.artifact_metadata or ArtifactMetadata()
        return ScenarioReferenceContext(
            scenario_name=scenario_name,
            pack_id=topology_metadata.pack_id,
            service=topology_metadata.service,
            topology_artifact_id=topology_metadata.artifact_id,
            inventory_artifact_id=(inventory.artifact_metadata or ArtifactMetadata()).artifact_id,
            demand_artifact_id=(demand.artifact_metadata or ArtifactMetadata()).artifact_id,
            authorization_artifact_id=None if authorization_metadata is None else authorization_metadata.artifact_id,
            authorization_source="authorization" if authorization is not None else "demand_proxy",
            rate_artifact_id=(rates.artifact_metadata or ArtifactMetadata()).artifact_id,
            accession_artifact_id=(accessions.artifact_metadata or ArtifactMetadata()).artifact_id,
            group_dimensions=topology_metadata.group_dimensions,
            cell_groups={cell.cell_id: cell.groups for cell in topology.career_cells},
            authorization_by_cell=self._build_authorization_map(demand, authorization),
        )

    def _resolve_named_path(self, scenario_name: str) -> Path:
        file_path = self._base_path / f"{scenario_name}.json"
        if file_path.exists():
            return file_path
        directory_path = self._base_path / scenario_name / "scenario.json"
        if directory_path.exists():
            return directory_path
        raise FileNotFoundError(f"Scenario fixture '{scenario_name}' was not found.")

    def _expand_payload(self, scenario_payload: dict, base_dir: Path) -> dict:
        if "scenario_refs" not in scenario_payload:
            return scenario_payload

        manifest = DecomposedScenarioManifest.model_validate(scenario_payload)
        expanded = {
            "scenario_id": manifest.scenario_id,
            "horizon_years": manifest.horizon_years,
            "processing_rule": manifest.processing_rule,
            "metadata": manifest.metadata,
        }

        topology = TopologyArtifact.model_validate(self._load_json(base_dir / manifest.scenario_refs.topology))
        inventory = InventoryArtifact.model_validate(self._load_json(base_dir / manifest.scenario_refs.inventory))
        demand = DemandArtifact.model_validate(self._load_json(base_dir / manifest.scenario_refs.demand))
        authorization = self._load_authorization_artifact(base_dir, manifest)
        rates = RateArtifact.model_validate(self._load_json(base_dir / manifest.scenario_refs.rates))
        accessions = AccessionArtifact.model_validate(self._load_json(base_dir / manifest.scenario_refs.accessions))

        self._validate_artifact_consistency(topology, inventory, demand, authorization, rates, accessions)
        self._validate_group_dimensions(topology)

        cells_by_id = {
            cell.cell_id: {"cell_id": cell.cell_id, "specialty": cell.specialty, "grade": cell.grade}
            for cell in topology.career_cells
        }
        self._apply_inventory(cells_by_id, inventory)
        self._apply_demand(cells_by_id, demand)
        self._apply_adjustments(cells_by_id, manifest.scenario_adjustments)

        expanded["career_cells"] = list(cells_by_id.values())
        expanded["transitions"] = topology.transitions
        expanded["rate_table"] = rates.rate_table
        expanded["rate_overrides"] = manifest.policy_overrides.rate_overrides
        expanded["accession_table"] = accessions.accession_table
        expanded["accession_overrides"] = manifest.policy_overrides.accession_overrides
        return expanded

    @staticmethod
    def _validate_artifact_consistency(
        topology: TopologyArtifact,
        inventory: InventoryArtifact,
        demand: DemandArtifact,
        authorization: AuthorizationArtifact | None,
        rates: RateArtifact,
        accessions: AccessionArtifact,
    ) -> None:
        metadata_by_name = {
            "topology": topology.artifact_metadata,
            "inventory": inventory.artifact_metadata,
            "demand": demand.artifact_metadata,
            "authorization": None if authorization is None else authorization.artifact_metadata,
            "rates": rates.artifact_metadata,
            "accessions": accessions.artifact_metadata,
        }
        pack_ids = {
            metadata.pack_id for metadata in metadata_by_name.values() if metadata is not None and metadata.pack_id is not None
        }
        if len(pack_ids) > 1:
            raise ValueError(f"referenced artifacts must agree on pack_id values; found {sorted(pack_ids)}")
        services = {
            metadata.service for metadata in metadata_by_name.values() if metadata is not None and metadata.service is not None
        }
        if len(services) > 1:
            raise ValueError(f"referenced artifacts must agree on service values; found {sorted(services)}")
        ScenarioLoader._validate_authorization_artifact(topology, authorization)

    @staticmethod
    def _validate_authorization_artifact(
        topology: TopologyArtifact,
        authorization: AuthorizationArtifact | None,
    ) -> None:
        if authorization is None:
            return
        known_cell_ids = {cell.cell_id for cell in topology.career_cells}
        authorization_ids = {item.cell_id for item in authorization.authorization}
        unknown = sorted(authorization_ids - known_cell_ids)
        if unknown:
            raise ValueError(f"authorization artifact references unknown cell_id values: {unknown}")
        missing = sorted(known_cell_ids - authorization_ids)
        if missing:
            raise ValueError(f"authorization artifact must cover all topology cell_id values; missing {missing}")

    @staticmethod
    def _validate_group_dimensions(topology: TopologyArtifact) -> None:
        metadata = topology.artifact_metadata
        if metadata is None or not metadata.group_dimensions:
            return
        expected = set(metadata.group_dimensions)
        for cell in topology.career_cells:
            actual = set(cell.groups)
            if actual != expected:
                raise ValueError(
                    f"topology cell '{cell.cell_id}' must define groups {sorted(expected)}; found {sorted(actual)}"
                )

    @staticmethod
    def _apply_inventory(cells_by_id: dict[str, dict], inventory: InventoryArtifact) -> None:
        for item in inventory.inventory:
            cell = cells_by_id.get(item.cell_id)
            if cell is None:
                raise ValueError(f"inventory artifact references unknown cell_id '{item.cell_id}'")
            cell["inventory"] = item.inventory

    @staticmethod
    def _apply_demand(cells_by_id: dict[str, dict], demand: DemandArtifact) -> None:
        for item in demand.demand:
            cell = cells_by_id.get(item.cell_id)
            if cell is None:
                raise ValueError(f"demand artifact references unknown cell_id '{item.cell_id}'")
            cell["demand"] = item.demand

    @staticmethod
    def _apply_adjustments(cells_by_id: dict[str, dict], adjustments: ScenarioAdjustments) -> None:
        for item in adjustments.inventory_deltas:
            cell = cells_by_id.get(item.cell_id)
            if cell is None:
                raise ValueError(f"inventory_deltas references unknown cell_id '{item.cell_id}'")
            cell["inventory"] += item.delta
        for item in adjustments.demand_deltas:
            cell = cells_by_id.get(item.cell_id)
            if cell is None:
                raise ValueError(f"demand_deltas references unknown cell_id '{item.cell_id}'")
            cell["demand"] += item.delta

    @staticmethod
    def _build_authorization_map(
        demand: DemandArtifact,
        authorization: AuthorizationArtifact | None,
    ) -> dict[str, int]:
        if authorization is not None:
            return {item.cell_id: item.authorization for item in authorization.authorization}
        return {item.cell_id: item.demand for item in demand.demand}

    @staticmethod
    def _load_authorization_artifact(
        base_dir: Path,
        manifest: DecomposedScenarioManifest,
    ) -> AuthorizationArtifact | None:
        if not manifest.scenario_refs.authorization:
            return None
        return AuthorizationArtifact.model_validate(
            ScenarioLoader._load_json(base_dir / manifest.scenario_refs.authorization)
        )

    @staticmethod
    def _load_json(path: Path) -> dict:
        return json.loads(path.read_text())
