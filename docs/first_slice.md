# MSim First Slice

**Date:** 2026-03-25

## Slice Statement

An analyst sends a small manpower scenario to `POST /api/projection/run` or loads a named fixture from `GET /api/projection/scenarios/{scenario_name}` and receives a deterministic projection result for a short planning horizon.

## Entry Point

HTTP API on the standalone backend.

## Core Action Loop

1. Validate scenario payload or load named fixture.
2. Build career-flow graph with `gameplan.graph`.
3. Apply optional structured rate table replacements, rate overrides, structured accession table replacements, and accession overrides by specialty, grade, and projection year.
4. Run deterministic annual steps using app orchestration built on `gameplan.engine`.
5. Apply either the sequential baseline rule or the phased alternative rule.
6. Derive analyst-facing summaries by grade, specialty, and cell-level shortages or overages.
7. Optionally compare baseline and variant runs and surface top cell deltas.
8. Return structured JSON result.

## Transition Rules

### Default Baseline

- `sequential_declared_order`
- decision record: `docs/decisions/ADR-0001-sequential-transition-rule.md`
- restart checkpoint: `docs/checkpoints/2026-03-25-sequential-rule-baseline.md`

### Alternative Mode

- `phased_standard_v1`
- phase order: `accession -> promotion -> lateral_move -> loss`
- decision record: `docs/decisions/ADR-0002-phased-standard-processing.md`
- checkpoint: `docs/checkpoints/2026-03-25-phased-rule-added.md`

## Policy Inputs

Scenarios may define `rate_table` to replace rate-based transition rates by cohort and year window, `rate_overrides` to multiply those rates, `accession_table` to replace accession amounts by target cohort and year window, and `accession_overrides` to apply additive adjustments after the base or table-derived amount is selected. Rate tables and overrides must include at least one cohort selector so policy remains targeted rather than global.

## Visible Result

- scenario identifier
- projection horizon
- projected inventory by career cell
- aggregate metrics
- aggregate summaries by grade and specialty
- shortage and overage highlights
- optional baseline-vs-variant deltas and comparison highlights
- run metadata with semantic provenance

## Failure Path

Invalid scenarios return request validation errors with actionable detail.
