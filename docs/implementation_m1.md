# M1 Implementation Plan

**Date:** 2026-03-26  
**Status:** Working implementation plan for Milestone M1 in `docs/backlog.md`

## Scope

This plan covers Milestone M1 from `docs/backlog.md`.

Documentation orientation and vision visuals are now in place; M1 is the next implementation-focused step.

Covered epics:

- `M1.1` Clarify Domain and Orchestration Boundaries
- `M1.2` Stabilize Scenario and Result Contracts
- `M1.3` Strengthen Provenance and Persistence Semantics
- `M1.4` Tighten Validation and Baseline Coverage

The goal is to harden the current deterministic projection slice without materially expanding product scope.

## Desired Outcome

At the end of M1, this repo should have:

- clearer separation between pure manpower logic, app orchestration, and API contract code
- better documented and better tested scenario and result schemas
- stronger provenance and persistence semantics
- a more explicit baseline to support later extraction into `gameplan.domains.manpower`

## Non-Goals

M1 does not attempt to:

- add new manpower policy categories beyond the current MVP
- build `gameplan.domains.manpower`
- introduce Monte Carlo, optimization, or AI workflow changes
- redesign the browser workbench
- replace file-backed persistence with a full `gameplan.data` integration

## Current File Targets

### Primary code targets

- `backend/domain/models.py`
- `backend/domain/projection.py`
- `backend/domain/graph_builder.py`
- `backend/core/simulation.py`
- `backend/core/scenario_loader.py`
- `backend/core/persistence.py`
- `backend/core/exporter.py`
- `backend/api/models.py`
- `backend/api/routes.py`

### Primary test targets

- `tests/test_projection.py`
- `tests/test_graph_builder.py`
- `tests/test_api.py`

### Primary doc targets

- `docs/provenance.md`
- `docs/validation_plan.md`
- `docs/roadmap.md`
- `docs/backlog.md`
- `docs/current_state_vs_target_state.md`

### Likely new docs

- `docs/implementation_m1.md`
- `docs/decisions/ADR-0003-domain-boundary-and-extraction-seam.md`
- `docs/checkpoints/2026-03-26-m1-foundation-hardening.md`

## Current Boundary Snapshot

The current repo boundary should be read as follows:

- `backend/domain/*`: pure scenario and result models, graph construction, deterministic year-step projection logic
- `backend/core/*`: app orchestration, provenance helpers, fixture loading, export formatting, and persistence adapters
- `backend/api/*`: HTTP request and response wrappers plus thin route delegation

### Current Boundary Notes

- `backend/domain/graph_builder.py` and `backend/domain/projection.py` are already on the right side of the seam and are likely early extraction candidates.
- `backend/core/simulation.py` is intentionally app-local, but it still contains some domain-adjacent helpers that may move later.
- `backend/api/routes.py` should not own shared calculation or provenance behavior.
- `backend/core/persistence.py` and `backend/core/exporter.py` are adapters and should stay repo-local even if shared manpower logic emerges.

### M1.1 Progress

- shared provenance helpers have been centralized into `backend/core/provenance.py`
- `backend/api/routes.py` now delegates fingerprint and timestamp generation instead of owning those helpers directly
- pure policy summary and policy override helpers now live in `backend/domain/policy.py`
- `LibraryRecord` now lives in `backend/domain/models.py`, so persistence no longer depends on an API-layer model
- export artifact contracts now live in `backend/domain/models.py`, so `backend/core/exporter.py` no longer depends on API-layer types
- analyst-facing projection and comparison summary builders now live in `backend/core/summary.py`, reducing orchestration clutter in `backend/core/simulation.py`
- provenance helper calls are now inlined in orchestration rather than wrapped by service-local pass-through methods
- duplicate cell and transition identifiers now fail schema validation explicitly
- policy tables and overrides now require at least one cohort selector
- persistence and export adapters now share provenance naming helpers for slugs and timestamp tokens
- direct regression tests now pin saved-record ordering and export filename/provenance invariants
- M1 foundation checkpoint recorded in `docs/checkpoints/2026-03-26-m1-foundation-hardening.md`
- ADR-0003 records the intended extraction seam

## Task Order

### Step 1: Document the Current Boundary and Intended Boundary

#### Goal

Make the current architecture explicit before refactoring.

#### Work

- inventory logic currently living in `backend/api`, `backend/core`, and `backend/domain`
- classify each responsibility as one of:
  - pure domain logic
  - app orchestration
  - API contract
  - persistence/export adapter
  - product-facing summary logic
- record which functions are likely extraction candidates for future shared package work

#### Expected outputs

- `docs/implementation_m1.md` section describing current and intended boundaries
- `ADR-0003` establishing the extraction seam between app-local orchestration and future shared manpower logic

#### Files likely touched

- `docs/implementation_m1.md`
- `docs/decisions/ADR-0003-domain-boundary-and-extraction-seam.md`
- `docs/provenance.md`

#### Notes

This step should happen before moving code so later refactors have a clear target state.

### Step 2: Refactor for Cleaner Core and Domain Separation

#### Goal

Reduce mixing between orchestration and pure logic while preserving current behavior.

#### Work

- review `backend/core/simulation.py` for logic that can move into domain-level helpers
- review `backend/api/routes.py` for helper code that belongs outside the route module
- keep policy application and projection semantics out of API handlers
- keep product-specific summaries and artifact formatting out of pure domain helpers
- preserve the current public API contract while improving internal structure

#### Expected outputs

- clearer responsibility split between:
  - `backend/domain/*`
  - `backend/core/*`
  - `backend/api/*`
- reduced duplication of fingerprint/timestamp or scenario-normalization logic where practical

#### Files likely touched

- `backend/core/simulation.py`
- `backend/domain/projection.py`
- `backend/domain/models.py`
- `backend/api/routes.py`
- `backend/core/persistence.py`
- `backend/core/exporter.py`

#### Notes

This is the most likely step to expose extraction candidates for `gameplan.domains.manpower`.

### Step 3: Stabilize Scenario and Result Contracts

#### Goal

Make the contract explicit enough that future refactoring does not accidentally change user-visible behavior.

#### Work

- review all request and response schemas for implicit assumptions
- determine which metadata fields are part of the stable contract versus implementation details
- tighten validation where the schema currently allows ambiguous or weak input shapes
- document scenario versioning expectations and compatibility assumptions
- confirm alignment between docs, fixtures, and tests

#### Expected outputs

- clearer schema rules in `backend/domain/models.py` and `backend/api/models.py`
- documentation updates describing what is contractually stable

#### Files likely touched

- `backend/domain/models.py`
- `backend/api/models.py`
- `docs/validation_plan.md`
- `docs/implementation_m1.md`

### Step 4: Harden Provenance and Persistence Semantics

#### Goal

Make run metadata and saved records more intentionally stable and ready for future storage changes.

#### Work

- review fingerprint generation for canonical behavior
- review timestamp generation and file naming conventions
- document the expected provenance semantics for runs, exports, and saved library records
- isolate persistence-facing logic where practical so storage backend changes do not ripple into the API contract
- identify which persistence helpers are pure formatting utilities versus file-system adapters

#### Expected outputs

- stronger provenance notes in docs
- cleaner persistence boundary for future `gameplan.data` migration
- regression tests around fingerprint and persisted record shape

#### Files likely touched

- `backend/core/persistence.py`
- `backend/core/exporter.py`
- `backend/core/simulation.py`
- `docs/provenance.md`
- `docs/implementation_m1.md`

### Step 5: Expand Baseline Validation Coverage

#### Goal

Increase protection around the current MVP behavior before larger architecture changes.

#### Work

- add or refine tests for schema error paths
- add tests for policy application edge cases and ordering semantics
- add tests for export and persistence invariants that are currently only indirectly covered
- validate that the documented baseline still matches actual test behavior

#### Expected outputs

- broader regression coverage for current deterministic semantics
- confidence to proceed into M2 extraction work

#### Files likely touched

- `tests/test_api.py`
- `tests/test_projection.py`
- `tests/test_graph_builder.py`
- `docs/validation_plan.md`

### Step 6: Record the Hardened Baseline

#### Goal

Leave M1 with an explicit checkpoint and updated planning docs.

#### Work

- add a checkpoint doc for the M1-hardened foundation
- update roadmap or backlog wording only if implementation reveals material sequencing changes
- record any deferred issues discovered during M1 that should become M2 backlog items

#### Expected outputs

- `docs/checkpoints/2026-03-26-m1-foundation-hardening.md`
- synchronized planning docs

## Proposed ADRs and Docs

### ADR-0003: Domain Boundary and Extraction Seam

Purpose:

- define what counts as pure manpower logic in this repo
- define what remains app-local orchestration
- define the initial seam for later extraction into `gameplan.domains.manpower`

### implementation_m1.md

Purpose:

- track the M1 execution notes
- record the current versus intended module responsibilities
- capture follow-on extraction candidates for M2

### M1 Checkpoint

Purpose:

- capture the post-hardening semantic baseline before shared-package extraction begins

## Test Plan

### Required validation command

```powershell
python -m pytest tests -q
```

### Minimum test additions expected during M1

- contract tests for schema validation edge cases
- tests that pin provenance expectations more directly
- tests for persistence record shape and saved-path behavior
- tests that pin ordering-sensitive policy behavior more explicitly

### Testing principle

M1 should increase confidence without changing the current MVP's user-visible semantics unless a change is explicitly documented and accepted.

## Risks

- refactoring `backend/core/simulation.py` may accidentally change projection semantics
- tightening schemas may break existing fixtures or tests if hidden assumptions exist
- provenance cleanup may expose inconsistencies across run, export, and persistence flows
- overly aggressive cleanup could blur the future extraction seam instead of clarifying it

## Exit Criteria

M1 is complete when:

- the core/domain/API split is documented and reflected in the code more clearly
- the scenario and result contracts are more explicit and better tested
- provenance and persistence semantics are documented and regression-covered
- a new checkpoint captures the hardened deterministic baseline
- the repo is better prepared for M2 shared-package extraction work

## Recommended Immediate Execution Slice

If M1 is implemented in small batches, the first batch should be:

1. document boundaries and add `ADR-0003`
2. refactor the most obvious boundary violations in `backend/core/simulation.py` and `backend/api/routes.py`
3. add direct provenance and persistence tests
4. record the checkpoint once tests pass











