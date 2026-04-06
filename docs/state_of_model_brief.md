# State Of The Model Brief

**Date:** 2026-03-27  
**Status:** Current implementation brief for the standalone MSim app

## Executive Summary

MSim is now past the initial deterministic MVP stage and into an early analyst-usable force analytics baseline.

What is real now:

- app-local neutral manpower algorithms under `backend/domain/`
- app-local projection and comparison flows over named scenarios and reusable synthetic packs
- grouped rollups by `occfld`, `community`, and `force_element`
- grouped authorization/fill summaries and readiness pressure signals for named pack-backed scenarios
- full and compact export flows that preserve those grouped analyst views
- analyst takeaway strings, ranked watchlists, and explanation trails in the API, exports, and static workbench
- a static workbench that exposes those results and exports directly

What is not real yet:

- billet-level modeling
- billet fill or vacancy semantics by unit/position
- training pipeline modeling
- Monte Carlo, sensitivity, or optimization workflows
- officer/warrant or cross-service generalization

## Model State In One Sentence

The current model is best understood as a **grouped manpower projection and comparison model with an early readiness proxy**, not a billet-level readiness model.

## Visual Summary

### 1. Force Analytics Flow

![Force Analytics Flow](force_analytics_flow.svg)

This captures the top-level story: scenario inputs feed projection, comparison, grouped analysis, and analyst decision support.

### 2. Simulation / Policy / Data Separation

![Simulation / Policy / Data Separation](simulation_policy_data_separation.svg)

This is the most important architecture boundary. Neutral manpower algorithms sit in the shared GamePlanOS seam. App-local provenance, summaries, exports, persistence, and workbench behavior stay here.
This is the intended long-term architecture boundary. In the current verified repo state, neutral manpower algorithms still live locally under `backend/domain/` because the referenced shared `gameplan.domains.manpower` package is not present in the current `C:\dev\jdsat-gameplan-os` checkout.

### 3. Readiness Linkage

![Readiness Linkage](readiness_linkage_diagram.svg)

This shows the target direction. The repo now has only the first bridge into this space: grouped authorization/fill summaries and readiness pressure signals.

### 4. Analyst Workflow

![Analyst Workflow](analyst_workflow_diagram.svg)

This remains the right user-facing frame: define or load a scenario, run or compare it, inspect grouped outcomes, and export portable artifacts.

## Current Functional Baseline

### Scenario and data shape

- monolithic JSON scenarios still work for compact tests and examples
- decomposed manifest-backed scenarios now also work
- reusable synthetic force packs support multiple named scenarios without cloning baseline topology and policy inputs

### Simulation boundary

- `backend/domain/` currently owns neutral manpower types and algorithms
- this repo owns app-facing result envelopes such as `ProjectionResult` and `ProjectionComparison`
- pack metadata and grouping semantics remain repo-local through scenario assembly and summary logic
- `gameplan.engine` and `gameplan.graph` remain the active shared GamePlanOS dependencies in use

### Analyst-facing outputs

For named pack-backed runs, the app now exposes:

- grouped inventory/demand rollups
- grouped authorization/fill summaries
- grouped readiness pressure signals
- grouped comparison deltas
- comparison drivers by community and force element
- ranked grouped watchlist items for projection risk and comparison hotspots
- explanation trails that capture demand basis, dominant gap/delta, and linked grouped contributors
- authorization-basis provenance so the analyst can see whether the grouped view is grounded in explicit authorization data or a demand fallback

### Export and handoff state

The app now supports:

- full projection JSON and CSV
- full comparison JSON and CSV
- compact projection summary CSV
- compact comparison summary CSV
- export catalog discovery through the API and workbench

Those exports preserve the grouped analyst context instead of dropping back to raw cell-only outputs.

## Honest Constraints

The model should still be described carefully.

It does **not** yet do these things:

- map inventory to billet-level structures
- compute billet fill by unit or position
- represent training throughput or washout
- provide stochastic uncertainty
- optimize policy choices

The readiness view is therefore useful but still coarse. It is a grouped pressure view, not an operationally complete readiness model.

## Recommendation

The right next step is to deepen analyst reporting on the current grouped model before introducing billet-level schema complexity.

Recommended sequence:

1. keep billet-level modeling out for now
2. treat grouped authorization/fill/readiness as the current analyst contract
3. improve explanation, reporting, and handoff artifacts around that grouped contract
4. only introduce billet-level inputs when there is a concrete schema and data plan worth locking in

## Dependency Note

The current `C:\dev\jdsat-gameplan-os` checkout does not contain `gameplan.domains.manpower`.

That means the repo should currently be described as:

- using local deterministic manpower domain logic
- using GamePlanOS for the shared packages that do exist here
- preserving a future extraction path into a shared manpower package once that package actually exists

## Restart References

For restart context, use:

- [Session Handoff](session_handoff.md)
- [Latest Checkpoint](checkpoints/2026-03-27-m3-grouped-readiness-and-export-handoff.md)
- [Roadmap](roadmap.md)
- [Backlog](backlog.md)
