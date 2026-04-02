# Manpower Extraction Plan

**Date:** 2026-03-26  
**Status:** M2.2 and M2.4 baseline established; living plan for continued shared-package extraction

## Purpose

This document maps the standalone MSim boundary to the emerging shared `gameplan.domains.manpower` package.

The extraction is no longer hypothetical. A first package scaffold now exists in `C:\dev\jdsat-gameplan-os`, and this repo now consumes the shared manpower models and pure helpers through thin local wrappers.

## Reference Baseline

Use these documents as the semantic baseline for continued extraction work:

- `docs/checkpoints/2026-03-26-m1-foundation-hardening.md`
- `docs/checkpoints/2026-03-26-m2-shared-manpower-integration.md`
- `docs/decisions/ADR-0003-domain-boundary-and-extraction-seam.md`

Current verification baseline:

```powershell
python -m pytest tests -q
```

## Current Integration Status

The current split is now:

- `gameplan.domains.manpower`: neutral manpower schemas, graph construction, projection-year logic, and policy application helpers
- `backend/domain/*`: thin app-local wrappers over the shared package plus app-only provenance metadata, result, and artifact contracts; neutral shared types are aliased directly where the app does not need to extend them
- `backend/core/*`: orchestration, provenance, summaries, persistence, exports, and fixture loading
- `backend/api/*`: HTTP request and response wiring

This is the intended seam.

## Extraction Goal

Continue moving pure manpower semantics into the shared package while keeping this repo responsible for:

- app orchestration
- HTTP contracts and routes
- scenario fixture management
- product-facing summaries and explanation wording
- exports and persistence adapters
- standalone repo bootstrapping and tooling

## What Has Already Moved

These responsibilities now have a shared-package home in `gameplan.domains.manpower`:

- pure scenario schemas other than app-local provenance metadata, plus neutral algorithm-output schemas
- processing-rule and transition-type literals
- policy-table and override schemas
- career-flow graph construction
- deterministic year-step execution
- policy matching and policy application behavior
- compact count-based policy summary behavior

## What Should Stay In This Repo

These modules should remain repo-local even as shared extraction continues:

### `backend/core/simulation.py`

Keep as the app orchestration layer that:

- builds graphs through shared helpers
- runs policy application and year-step logic through shared helpers
- assembles app-facing run metadata
- composes product-facing summaries
- returns the stable repo contract

### `backend/core/scenario_loader.py`

Stay repo-local because it owns:

- fixture directory conventions
- named-scenario loading
- catalog metadata assembly from local files

### `backend/core/provenance.py`

Stay repo-local for now because it owns app-facing provenance and file-naming behavior for:

- saved record paths
- export filenames
- repo-local audit metadata

Possible future split:

- scenario fingerprinting could become a neutral shared helper later
- filename and record-token helpers should remain app-local unless another app needs the same convention

### `backend/core/summary.py`

Stay repo-local because it is product-facing:

- analyst summary groupings
- policy delta presentation labels
- comparison driver wording
- top-cell explanation formatting

### `backend/core/persistence.py`

Stay repo-local because it is a file-system adapter for this standalone app.

### `backend/core/exporter.py`

Stay repo-local because export envelopes, filenames, and CSV comment conventions are product-output concerns.

### `backend/api/*`

Stay repo-local. No extraction value.

## Shared Package Shape

The current shared package shape is:

- `gameplan/domains/manpower/__init__.py`
- `gameplan/domains/manpower/algorithms/models.py`
- `gameplan/domains/manpower/algorithms/graph.py`
- `gameplan/domains/manpower/algorithms/projection.py`
- `gameplan/domains/manpower/algorithms/policy.py`
- `gameplan/domains/manpower/tests/test_manpower.py`
- `gameplan/domains/manpower/docs/*`

Current public exports include:

- `ProjectionScenario`
- `CareerCell`
- `Transition`
- `RateTableEntry`
- `RateOverride`
- `AccessionTableEntry`
- `AccessionOverride`
- `ProjectedCell`
- `ProjectionAggregate`
- `ComparisonCellDelta`
- `PolicySummary`
- `build_career_flow_graph`
- `run_projection_year`
- `apply_policy_overrides`
- `build_policy_summary`

## Remaining Extraction Sequence

### Step 1

Preserve dual-layer regression coverage:

- package tests for shared manpower semantics
- app tests for app-facing orchestration, exports, persistence, and API behavior

### Step 2

Keep this repo importing shared helpers behind the existing `backend/core/simulation.py` orchestration layer.

### Step 3

Remove any remaining duplicated pure-domain definitions in this repo once parity stays proven.

### Step 4

Refine the package API only when a second app or a clearer shared use case requires it.

## Extraction Constraints

Do not continue moving behavior into the shared package if any of these become true:

- package APIs are forced to carry app-specific export or persistence types
- summary or explanation wording is bundled into algorithmic helpers
- scenario fixture conventions leak into the shared package
- app-level regression coverage no longer protects the public MSim contract

## Current Gaps

The current integration still leaves a few open questions:

- whether `PolicySummary` should remain a public shared type or become an internal helper return type later
- whether graph node and edge payload dataclasses should stay public package types or become internal implementation details
- how this standalone repo should consume GamePlanOS in development and CI without relying indefinitely on the local source-path shim

## Decision Recorded

For current planning, the shared package should expose lower-level algorithm outputs, not the full app-facing `ProjectionResult` or `ProjectionComparison` envelopes.

This repo remains the owner of:

- scenario provenance metadata such as labels, authorship, notes, and local version tags
- final run metadata
- provenance fields
- analyst-facing summaries
- comparison drivers and wording
- export and persistence contracts
