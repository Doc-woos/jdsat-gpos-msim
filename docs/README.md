# MSim Docs

This directory is the working documentation set for the standalone MSim application.

It is organized around four needs:

- product and platform vision
- implementation planning
- architecture and boundary guidance
- validation and checkpoints

## Start Here

- [Current State vs Target State](current_state_vs_target_state.md)
- [State Of The Model Brief](state_of_model_brief.md)
- [App Brief](app_brief.md)
- [First Slice](first_slice.md)
- [Visuals](visuals.md)
- [Roadmap](roadmap.md)
- [Backlog](backlog.md)
- [Session Handoff](session_handoff.md)
- [Manpower Extraction Plan](manpower_extraction_plan.md)

## Vision and Structure

- [Force Analytics Flow](force_analytics_flow.md)
- [Analyst Workflow Diagram](analyst_workflow_diagram.md)
- [Career Network Structure Diagram](career_network_structure.md)
- [Simulation Policy Data Separation Diagram](simulation_policy_data_separation.md)
- [Readiness Linkage Diagram](readiness_linkage_diagram.md)

## Implementation Guidance

- [Implementation M1](implementation_m1.md)
- [Manpower Extraction Plan](manpower_extraction_plan.md)
- [Provenance](provenance.md)
- [Validation Plan](validation_plan.md)

## Decision Records and Checkpoints

- `decisions/`
- `checkpoints/`
- latest checkpoint: [2026-03-27 M3 Grouped Readiness and Export Handoff](checkpoints/2026-03-27-m3-grouped-readiness-and-export-handoff.md)

## Rendering Notes

Rendered diagram artifacts are generated from the Mermaid `.mmd` sources.

Preferred review format:
- `docs/*.svg`

Fallback format:
- `docs/*.png`

Regenerate all diagram outputs with:

```powershell
npm install
npm run docs:render-diagrams
```


## Development

For local GamePlanOS dependency setup, use [development_dependencies.md](development_dependencies.md).

For the current M3.1 design target, use [force_wide_scenario_shape.md](force_wide_scenario_shape.md).
