# Session Handoff

**Date:** 2026-03-27  
**Purpose:** Fast restart context for the standalone MSim repo without relying on prior chat history

## Where The Repo Is Now

This repo is a standalone FastAPI manpower simulation app built on GamePlanOS concepts and packages.

The current baseline is:

- app-local neutral manpower algorithms and schemas in `backend/domain/*`
- app-local orchestration, provenance, exports, persistence, summaries, and analyst UX
- decomposed scenario manifests and reusable synthetic force packs
- named pack-backed projection and comparison flows with grouped reporting
- grouped authorization/fill summaries and readiness pressure signals
- repo-local analyst takeaways derived from grouped summaries for projection and comparison handoff
- repo-local ranked watchlists and explanation trails for grouped projection risk and comparison hotspot review
- compact and full export flows that preserve those grouped analyst views

## Current Architecture Boundary

Use these boundaries when resuming work.

Shared GamePlanOS responsibilities:

- `gameplan.engine` for runtime substrate
- `gameplan.graph` as a reference source for graph/topology concerns

Repo-local responsibilities:

- `backend/core/scenario_loader.py` for named-scenario expansion, pack assembly, and reference context
- `backend/core/simulation.py` for app orchestration over shared algorithms
- `backend/core/summary.py` for app-local grouped summaries, drivers, fill views, readiness signals, watchlists, explanations, and analyst takeaways
- `backend/core/exporter.py` for full and compact analyst export artifacts, including watchlist, explanation, and takeaway sections in CSVs
- `backend/core/persistence.py` and `backend/core/provenance.py` for local records and artifact naming
- `backend/domain/*` for the current deterministic manpower models, graph builder, policy helpers, and year-step execution
- `backend/api/*` for HTTP contracts and route wiring
- `backend/web/*` for the static analyst workbench

Keep app-facing envelopes local:

- `ProjectionResult`
- `ProjectionComparison`
- grouped readiness/fill summary structures
- export catalog and workbench-specific affordances

## Current Product Semantics

The app currently supports two readiness-related layers:

1. grouped inventory vs authorization/fill summaries
2. grouped readiness pressure signals derived from those fill views

It now also supports a third app-local interpretation layer:

3. concise analyst takeaways derived from authorization provenance, grouped pressure, and dominant comparison shifts

And a fourth analyst-priority layer:

4. ranked grouped watchlists plus short explanation trails for what to brief first and why

Important constraint:

- this is a grouped readiness proxy only
- it is not billet-level modeling
- explicit authorization artifacts are preferred when present
- demand can still act as a fallback proxy when no authorization artifact exists
- summaries expose `authorization_basis` so analysts can see which semantic basis was used

## Scenario And Pack State

Named scenario support now includes:

- monolithic `scenarios/*.json`
- directory-backed manifest scenarios
- reusable pack-backed scenarios under `scenarios/packs/*`

The active synthetic enlisted pack proves:

- multi-community topology
- deeper grade ladders
- named baseline/variant scenario reuse
- internal grouping tags for `occfld`, `community`, and `force_element`

Those grouping tags are used only in repo-local reporting and validation, not in the neutral shared simulation contract.

## Export And Analyst UX State

Current export surface:

- full projection JSON/CSV
- full comparison JSON/CSV
- compact projection summary CSV
- compact comparison summary CSV
- export catalog endpoint and workbench panel

Current analyst-visible export behavior:

- grouped fill/readiness sections survive in projection CSVs when available
- grouped deltas plus baseline/variant fill/readiness sections survive in comparison CSVs
- compact projection and comparison summary CSVs now include dedicated watchlist, explanation, and takeaway sections
- workbench result panels explain which grouped sections an export will contain
- workbench insight cards now surface analyst takeaways, ranked watchlists, and explanation trails before detailed grouped tables

## Verification Command

Use this as the default regression check:

```powershell
python -m pytest tests -q
```

Current known baseline: `87 passed`

## Recommended Next Work

Recommended next move: continue with analyst-facing depth on the grouped model before committing to billet-level inputs.

Recommended order:

1. keep billet-level modeling out for now
2. capture the current grouped authorization/fill/readiness contract clearly in docs
3. deepen analyst reporting, explanation, and handoff artifacts on top of the grouped model
4. only then decide whether billet-level inputs are mature enough to justify a new schema

## If Restarting After Shutdown

Read these first:

- `docs/session_handoff.md`
- `docs/checkpoints/2026-03-27-m3-grouped-readiness-and-export-handoff.md`
- `docs/roadmap.md`
- `docs/backlog.md`
- `docs/force_wide_scenario_shape.md`
- `docs/readiness_linkage_diagram.md`

Then verify:

```powershell
python -m pytest tests -q
```
