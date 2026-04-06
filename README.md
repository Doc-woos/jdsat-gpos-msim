# MSim

Standalone GamePlanOS-based force analytics application focused on a first MVP for deterministic manpower projection.

## Status

This repository is a standalone app repo, not a GamePlanOS monorepo workspace. The current slice is:

- backend-only simulation core with a FastAPI-served analyst workbench
- single analyst workflow
- deterministic small-scenario projection
- named fixture loading, analyst-facing scenario catalog metadata, and baseline-vs-variant comparison
- dual processing rules: sequential baseline and phased alternative
- structured rate tables by cohort and year window
- scenario-level rate overrides by specialty and grade
- year-phased overrides by projection year
- structured accession tables by cohort and year window
- accession amount overrides, including year-phased accessions
- scenario metadata, fingerprints, and run timestamps for auditability
- JSON and CSV export artifacts for runs and comparisons
- comparison storytelling with rule summaries, policy deltas, and outcome drivers
- concise analyst takeaways, ranked watchlists, and explanation trails derived from grouped summaries for projection and comparison handoff
- local workspace persistence for versioned scenario, run, and comparison records
- explicit semantic provenance in API metadata
- fixture discovery through the API
- analyst-facing projection and comparison summaries
- portable structure with provenance notes

## First Slice

Submit a small manpower scenario to the backend and receive:

- scenario identifier
- projection horizon
- projected inventory by career cell
- aggregate metrics
- run metadata
- aggregate summaries by grade and specialty
- comparison highlights for policy-adjusted variants
- portable export artifacts for handoff and reproducibility
- local saved records for replay and audit

The repo also supports listing named local scenario fixtures, browsing an analyst-facing scenario catalog with labels and notes, running a named fixture, comparing a baseline scenario to a policy-adjusted variant, exporting either result as JSON or CSV, saving records into a local workspace library, and using a thin browser workbench at the root path.

## Analyst Workbench

Open the root path after starting the API:

```text
http://127.0.0.1:8000/
```

The workbench supports:

- browsing labeled demo scenarios with source and note context
- running named scenarios
- comparing named scenarios
- inspecting result metrics, metadata, and cell tables
- reviewing ranked grouped watchlists, explanation trails, and comparison drivers that explain rule and policy differences
- exporting projection and comparison artifacts as JSON or CSV
- saving scenario snapshots, runs, and comparisons into the local library
- reviewing the current saved library index

The current workbench styling follows the visual language of the local reference app at `C:\dev\RRL Content Automation Engine` while keeping this app's structure and behavior independent.

## Scenario Catalog

Named fixtures are now exposed through two API surfaces:

```text
GET /api/projection/scenarios
GET /api/projection/catalog
```

`/api/projection/scenarios` remains the minimal stable name list.
`/api/projection/catalog` provides analyst-facing labels, processing rule, version, source, and notes for each fixture.

## Comparison Storytelling

Comparison responses now include:

- `rule_change`
- `rule_summary`
- `policy_deltas`
- `drivers`

These fields explain whether the processing rule changed, how policy input counts differ between baseline and variant, and which cell-level outcome shifts were most material.

Pack-backed grouped summaries also expose:

- `watchlist`
- `explanations`

These fields rank the grouped risks or delta hotspots worth briefing first and capture a short reason trail for why they matter.

## Local Library

The app now supports local workspace persistence through these endpoints:

```text
GET  /api/library/records
POST /api/library/scenarios/save
POST /api/library/runs/save
POST /api/library/comparisons/save
```

Saved records are written under:

```text
workspace_data/
  scenarios/
  runs/
  comparisons/
```

This is file-backed local persistence, not a database. Each save produces a versioned JSON record with a timestamped filename so repeated saves do not overwrite prior records.

## Processing Rules

Supported rules:

- `sequential_declared_order`
- `phased_standard_v1`

Current default baseline:

- `sequential_declared_order`
- `decision_ref: ADR-0001`
- `checkpoint_ref: 2026-03-25-sequential-rule-baseline`

Phased alternative:

- `phased_standard_v1`
- `decision_ref: ADR-0002`
- `checkpoint_ref: 2026-03-25-phased-rule-added`

## Policy Inputs

Scenarios may optionally include:

- `metadata` with `version`, `label`, `created_by`, `source`, and `notes`
- `rate_table` for structured replacement rates by transition cohort and year window
- `rate_overrides` for multiplicative adjustments after the base or table-derived rate is selected
- `accession_table` for structured accession amounts by target specialty, grade, and year window
- `accession_overrides` for additive adjustments on top of the base or table-derived accession amount

`rate_table` replaces the base transition rate for matching rate-based transitions in matching years. `rate_overrides` then apply multiplicative adjustments after that replacement step.

`accession_table` replaces the base accession amount for matching cohorts in matching years. `accession_overrides` then apply signed additive deltas after that replacement step.
## GamePlanOS Dependency

This repo currently depends on the GamePlanOS checkout for shared substrate packages such as `gameplan.engine` and `gameplan.graph`.

The previously planned shared manpower package path, `gameplan.domains.manpower`, is not present in the current reference checkout. The deterministic manpower models, graph builder, policy helpers, and year-step execution therefore live in this repo under `backend/domain/*` until a real shared package exists again.

Preferred development setup is still an editable install of the GamePlanOS reference repo rather than relying on `GAMEPLAN_SRC`.

Recommended bootstrap command:

```powershell
npm run deps:bootstrap
```

Direct install command:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_gameplan_editable.ps1
```

Fallback only:

- set `GAMEPLAN_SRC` to the GamePlanOS source root if an editable install is not available
- the app and tests will use that source-path shim only when `gameplan` is otherwise not importable for the shared substrate packages that still exist

The reference repo path used during current development is:

```text
C:\dev\jdsat-gameplan-os
```

Verification command:

```powershell
npm run deps:verify-gameplan
```

Contributor validation command:

```powershell
npm run validate
```

## Diagram Rendering

Mermaid diagram sources live in `docs/*.mmd`.

To regenerate vector and high-resolution raster outputs locally:

```powershell
npm install
npm run docs:render-diagrams
```

This emits both:

- `docs/*.svg` for zoomable documentation artifacts
- `docs/*.png` at higher resolution for raster-only consumers

The render script uses these defaults:

- PNG width: `2400`
- PNG scale: `2`
- background: `white`

The script entry point is `scripts/render_diagrams.ps1`.
## Visuals

For rendered vision diagrams, prefer the SVG artifacts in [docs/visuals.md](docs/visuals.md). They are generated from the Mermaid `.mmd` sources, previewed in that landing page, and remain sharp when zoomed.


## Docs

Project documentation starts at [docs/README.md](docs/README.md).

For the fastest orientation, start with [docs/current_state_vs_target_state.md](docs/current_state_vs_target_state.md). For the current boundary around local manpower logic and any future extraction, use [docs/manpower_extraction_plan.md](docs/manpower_extraction_plan.md).


