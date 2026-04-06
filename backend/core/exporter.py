"""Export helpers for portable projection artifacts."""

from __future__ import annotations

import json

from backend.core.provenance import build_file_slug, build_timestamp_slug
from backend.domain.models import ExportArtifact, ExportFormat, ProjectionComparison, ProjectionResult


class ProjectionExportService:
    """Build storage-free JSON and CSV exports for current run results."""

    def export_projection(
        self,
        result: ProjectionResult,
        export_format: ExportFormat,
    ) -> ExportArtifact:
        """Export a single projection result."""
        filename = self._build_projection_filename(result, export_format)
        if export_format == "json":
            content = self._build_projection_json(result)
            media_type = "application/json"
        else:
            content = self._build_projection_csv(result)
            media_type = "text/csv"
        return ExportArtifact(
            kind="projection_export",
            format=export_format,
            filename=filename,
            media_type=media_type,
            content=content,
        )

    def export_comparison(
        self,
        comparison: ProjectionComparison,
        export_format: ExportFormat,
    ) -> ExportArtifact:
        """Export a comparison result."""
        filename = self._build_comparison_filename(comparison, export_format)
        if export_format == "json":
            content = self._build_comparison_json(comparison)
            media_type = "application/json"
        else:
            content = self._build_comparison_csv(comparison)
            media_type = "text/csv"
        return ExportArtifact(
            kind="comparison_export",
            format=export_format,
            filename=filename,
            media_type=media_type,
            content=content,
        )

    def export_projection_summary(self, result: ProjectionResult) -> ExportArtifact:
        """Export a compact projection-summary CSV artifact."""
        filename = self._build_projection_summary_filename(result)
        return ExportArtifact(
            kind="projection_summary_export",
            format="csv",
            filename=filename,
            media_type="text/csv",
            content=self._build_projection_summary_csv(result),
        )

    def export_comparison_summary(self, comparison: ProjectionComparison) -> ExportArtifact:
        """Export a compact comparison-summary CSV artifact."""
        filename = self._build_comparison_summary_filename(comparison)
        return ExportArtifact(
            kind="comparison_summary_export",
            format="csv",
            filename=filename,
            media_type="text/csv",
            content=self._build_comparison_summary_csv(comparison),
        )

    def _build_projection_filename(
        self,
        result: ProjectionResult,
        export_format: ExportFormat,
    ) -> str:
        """Build a stable projection export filename."""
        timestamp = build_timestamp_slug(result.metadata.run_timestamp)
        fingerprint = result.metadata.scenario_fingerprint[:8]
        scenario_id = build_file_slug(result.scenario_id, fallback="artifact")
        return f"{scenario_id}-{fingerprint}-{timestamp}.{export_format}"

    def _build_comparison_filename(
        self,
        comparison: ProjectionComparison,
        export_format: ExportFormat,
    ) -> str:
        """Build a stable comparison export filename."""
        timestamp = build_timestamp_slug(comparison.variant.metadata.run_timestamp)
        baseline_id = build_file_slug(comparison.baseline.scenario_id, fallback="artifact")
        variant_id = build_file_slug(comparison.variant.scenario_id, fallback="artifact")
        fingerprint = comparison.variant.metadata.scenario_fingerprint[:8]
        return f"{baseline_id}-vs-{variant_id}-{fingerprint}-{timestamp}.{export_format}"

    def _build_projection_summary_filename(self, result: ProjectionResult) -> str:
        timestamp = build_timestamp_slug(result.metadata.run_timestamp)
        fingerprint = result.metadata.scenario_fingerprint[:8]
        scenario_id = build_file_slug(result.scenario_id, fallback="artifact")
        return f"{scenario_id}-summary-{fingerprint}-{timestamp}.csv"

    def _build_comparison_summary_filename(self, comparison: ProjectionComparison) -> str:
        timestamp = build_timestamp_slug(comparison.variant.metadata.run_timestamp)
        baseline_id = build_file_slug(comparison.baseline.scenario_id, fallback="artifact")
        variant_id = build_file_slug(comparison.variant.scenario_id, fallback="artifact")
        fingerprint = comparison.variant.metadata.scenario_fingerprint[:8]
        return f"{baseline_id}-vs-{variant_id}-summary-{fingerprint}-{timestamp}.csv"

    def _build_projection_json(self, result: ProjectionResult) -> str:
        """Build a JSON export for one projection run."""
        payload = {
            "artifact_kind": "projection_export",
            "result": result.model_dump(mode="json"),
        }
        return json.dumps(payload, indent=2, sort_keys=True)

    def _build_comparison_json(self, comparison: ProjectionComparison) -> str:
        """Build a JSON export for one comparison run."""
        payload = {
            "artifact_kind": "comparison_export",
            "comparison": comparison.model_dump(mode="json"),
        }
        return json.dumps(payload, indent=2, sort_keys=True)

    def _build_projection_csv(self, result: ProjectionResult) -> str:
        """Build a CSV export for one projection run with embedded provenance comments."""
        lines = [
            "# kind: projection_export",
            f"# scenario_id: {result.scenario_id}",
            f"# scenario_fingerprint: {result.metadata.scenario_fingerprint}",
            f"# processing_rule: {result.metadata.processing_rule}",
            f"# decision_ref: {result.metadata.decision_ref}",
            f"# checkpoint_ref: {result.metadata.checkpoint_ref}",
            f"# run_timestamp: {result.metadata.run_timestamp}",
            f"# scenario_version: {result.metadata.scenario_metadata.version}",
            f"# authorization_basis: {result.summary.authorization_basis.source}",
            "cell_id,specialty,grade,inventory,demand,gap",
        ]
        for cell in result.projected_inventory:
            lines.append(
                f"{cell.cell_id},{cell.specialty},{cell.grade},{cell.inventory},{cell.demand},{cell.gap}"
            )
        self._append_projection_context_sections(lines, result)
        return "\n".join(lines)

    def _build_projection_summary_csv(self, result: ProjectionResult) -> str:
        lines = [
            "# kind: projection_summary_export",
            f"# scenario_id: {result.scenario_id}",
            f"# scenario_fingerprint: {result.metadata.scenario_fingerprint}",
            f"# processing_rule: {result.metadata.processing_rule}",
            f"# authorization_basis: {result.summary.authorization_basis.source}",
        ]
        self._append_takeaway_section(lines, result.summary.takeaways)
        self._append_watchlist_section(lines, result.summary.watchlist)
        self._append_explanation_section(lines, result.summary.explanations)
        self._append_projection_aggregate_section(lines, "by_grade", result.summary.by_grade)
        self._append_projection_aggregate_section(lines, "by_specialty", result.summary.by_specialty)
        self._append_projection_aggregate_section(lines, "by_occfld", result.summary.by_occfld)
        self._append_projection_aggregate_section(lines, "by_community", result.summary.by_community)
        self._append_projection_aggregate_section(lines, "by_force_element", result.summary.by_force_element)
        self._append_projection_context_sections(lines, result)
        return "\n".join(lines)

    def _build_comparison_summary_csv(self, comparison: ProjectionComparison) -> str:
        lines = [
            "# kind: comparison_summary_export",
            f"# baseline_scenario_id: {comparison.baseline.scenario_id}",
            f"# variant_scenario_id: {comparison.variant.scenario_id}",
            f"# baseline_authorization_basis: {comparison.summary.authorization_basis.baseline.source}",
            f"# variant_authorization_basis: {comparison.summary.authorization_basis.variant.source}",
        ]
        self._append_takeaway_section(lines, comparison.summary.takeaways)
        self._append_watchlist_section(lines, comparison.summary.watchlist)
        self._append_explanation_section(lines, comparison.summary.explanations)
        self._append_policy_delta_section(lines, comparison.summary.policy_deltas)
        self._append_driver_section(lines, comparison.summary.drivers)
        self._append_aggregate_delta_section(lines, "occfld_deltas", comparison.summary.by_occfld)
        self._append_aggregate_delta_section(lines, "community_deltas", comparison.summary.by_community)
        self._append_aggregate_delta_section(lines, "force_element_deltas", comparison.summary.by_force_element)
        self._append_comparison_context_sections(lines, comparison)
        return "\n".join(lines)

    def _build_comparison_csv(self, comparison: ProjectionComparison) -> str:
        """Build a CSV export for one comparison run with embedded provenance comments."""
        baseline_cells = {cell.cell_id: cell for cell in comparison.baseline.projected_inventory}
        variant_cells = {cell.cell_id: cell for cell in comparison.variant.projected_inventory}
        lines = [
            "# kind: comparison_export",
            f"# baseline_scenario_id: {comparison.baseline.scenario_id}",
            f"# variant_scenario_id: {comparison.variant.scenario_id}",
            f"# baseline_fingerprint: {comparison.baseline.metadata.scenario_fingerprint}",
            f"# variant_fingerprint: {comparison.variant.metadata.scenario_fingerprint}",
            f"# processing_rule: {comparison.variant.metadata.processing_rule}",
            f"# decision_ref: {comparison.variant.metadata.decision_ref}",
            f"# checkpoint_ref: {comparison.variant.metadata.checkpoint_ref}",
            f"# run_timestamp: {comparison.variant.metadata.run_timestamp}",
            f"# baseline_authorization_basis: {comparison.summary.authorization_basis.baseline.source}",
            f"# variant_authorization_basis: {comparison.summary.authorization_basis.variant.source}",
            "cell_id,baseline_inventory,variant_inventory,baseline_gap,variant_gap,inventory_delta,gap_delta",
        ]
        for delta in comparison.cell_deltas:
            baseline = baseline_cells.get(delta.cell_id)
            variant = variant_cells.get(delta.cell_id)
            baseline_inventory = 0 if baseline is None else baseline.inventory
            variant_inventory = 0 if variant is None else variant.inventory
            baseline_gap = 0 if baseline is None else baseline.gap
            variant_gap = 0 if variant is None else variant.gap
            lines.append(
                f"{delta.cell_id},{baseline_inventory},{variant_inventory},{baseline_gap},{variant_gap},{delta.inventory_delta},{delta.gap_delta}"
            )
        self._append_aggregate_delta_section(lines, "occfld_deltas", comparison.summary.by_occfld)
        self._append_aggregate_delta_section(lines, "community_deltas", comparison.summary.by_community)
        self._append_aggregate_delta_section(lines, "force_element_deltas", comparison.summary.by_force_element)
        self._append_comparison_context_sections(lines, comparison)
        return "\n".join(lines)

    def _append_projection_context_sections(self, lines: list[str], result: ProjectionResult) -> None:
        self._append_watchlist_section(lines, result.summary.watchlist)
        self._append_explanation_section(lines, result.summary.explanations)
        self._append_fill_summary_section(lines, "fill_by_occfld", result.summary.fill_by_occfld)
        self._append_fill_summary_section(lines, "fill_by_community", result.summary.fill_by_community)
        self._append_fill_summary_section(lines, "fill_by_force_element", result.summary.fill_by_force_element)
        self._append_readiness_signal_section(lines, result.summary.readiness_signals)

    def _append_comparison_context_sections(self, lines: list[str], comparison: ProjectionComparison) -> None:
        self._append_watchlist_section(lines, comparison.summary.watchlist)
        self._append_explanation_section(lines, comparison.summary.explanations)
        self._append_side_summary_sections(lines, "baseline", comparison.baseline)
        self._append_side_summary_sections(lines, "variant", comparison.variant)

    def _append_side_summary_sections(self, lines: list[str], prefix: str, result: ProjectionResult) -> None:
        self._append_fill_summary_section(lines, f"{prefix}_fill_by_occfld", result.summary.fill_by_occfld)
        self._append_fill_summary_section(lines, f"{prefix}_fill_by_community", result.summary.fill_by_community)
        self._append_fill_summary_section(lines, f"{prefix}_fill_by_force_element", result.summary.fill_by_force_element)
        self._append_readiness_signal_section(lines, result.summary.readiness_signals, section_name=f"{prefix}_readiness_signals")

    @staticmethod
    def _append_projection_aggregate_section(lines: list[str], section_name: str, aggregates: list) -> None:
        if not aggregates:
            return
        lines.append("")
        lines.append(f"# section: {section_name}")
        lines.append("key,inventory,demand,gap")
        for item in aggregates:
            lines.append(f"{item.key},{item.inventory},{item.demand},{item.gap}")

    @staticmethod
    def _append_policy_delta_section(lines: list[str], policy_deltas: list) -> None:
        if not policy_deltas:
            return
        lines.append("")
        lines.append("# section: policy_deltas")
        lines.append("category,baseline_count,variant_count,delta")
        for item in policy_deltas:
            lines.append(f"{item.category},{item.baseline_count},{item.variant_count},{item.delta}")

    @staticmethod
    def _append_driver_section(lines: list[str], drivers: list) -> None:
        if not drivers:
            return
        lines.append("")
        lines.append("# section: drivers")
        lines.append("kind,title,detail")
        for item in drivers:
            detail = item.detail.replace(",", ";")
            title = item.title.replace(",", ";")
            lines.append(f"{item.kind},{title},{detail}")

    @staticmethod
    def _append_takeaway_section(lines: list[str], takeaways: list[str]) -> None:
        if not takeaways:
            return
        lines.append("")
        lines.append("# section: takeaways")
        lines.append("order,takeaway")
        for index, takeaway in enumerate(takeaways, start=1):
            safe_takeaway = takeaway.replace(",", ";")
            lines.append(f"{index},{safe_takeaway}")

    @staticmethod
    def _append_explanation_section(lines: list[str], explanations: list) -> None:
        if not explanations:
            return
        lines.append("")
        lines.append("# section: explanations")
        lines.append("title,scope,group_type,key,reason_trail")
        for item in explanations:
            title = item.title.replace(",", ";")
            scope = item.scope.replace(",", ";")
            group_type = "" if item.group_type is None else item.group_type.replace(",", ";")
            key = "" if item.key is None else item.key.replace(",", ";")
            reason_trail = " | ".join(reason.replace(",", ";") for reason in item.reason_trail)
            lines.append(f"{title},{scope},{group_type},{key},{reason_trail}")

    @staticmethod
    def _append_watchlist_section(lines: list[str], watchlist: list) -> None:
        if not watchlist:
            return
        lines.append("")
        lines.append("# section: watchlist")
        lines.append("title,scope,group_type,key,severity,metric,value,detail")
        for item in watchlist:
            title = item.title.replace(",", ";")
            scope = item.scope.replace(",", ";")
            group_type = item.group_type.replace(",", ";")
            key = item.key.replace(",", ";")
            severity = item.severity.replace(",", ";")
            metric = item.metric.replace(",", ";")
            value = item.value.replace(",", ";")
            detail = item.detail.replace(",", ";")
            lines.append(f"{title},{scope},{group_type},{key},{severity},{metric},{value},{detail}")

    @staticmethod
    def _append_aggregate_delta_section(lines: list[str], section_name: str, deltas: list) -> None:
        if not deltas:
            return
        lines.append("")
        lines.append(f"# section: {section_name}")
        lines.append("key,baseline_inventory,variant_inventory,baseline_gap,variant_gap,inventory_delta,gap_delta")
        for delta in deltas:
            lines.append(
                f"{delta.key},{delta.baseline_inventory},{delta.variant_inventory},"
                f"{delta.baseline_gap},{delta.variant_gap},{delta.inventory_delta},{delta.gap_delta}"
            )

    @staticmethod
    def _append_fill_summary_section(lines: list[str], section_name: str, summaries: list) -> None:
        if not summaries:
            return
        lines.append("")
        lines.append(f"# section: {section_name}")
        lines.append("group_type,key,inventory,authorization,gap,fill_rate,status")
        for item in summaries:
            lines.append(
                f"{item.group_type},{item.key},{item.inventory},{item.authorization},{item.gap},{item.fill_rate},{item.status}"
            )

    @staticmethod
    def _append_readiness_signal_section(lines: list[str], signals: list, section_name: str = "readiness_signals") -> None:
        if not signals:
            return
        lines.append("")
        lines.append(f"# section: {section_name}")
        lines.append("group_type,key,inventory,demand,gap,fill_rate,status")
        for item in signals:
            lines.append(
                f"{item.group_type},{item.key},{item.inventory},{item.demand},{item.gap},{item.fill_rate},{item.status}"
            )
