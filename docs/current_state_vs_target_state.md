# Current State vs Target State

This page distinguishes what the standalone MSim repo implements today from the broader target-state vision captured in the roadmap and visuals.

## Current State

The repo currently delivers a narrow but working Phase 0 seed:

- deterministic manpower projection over a small scenario model
- career-flow graph validation built on `gameplan.graph`
- app-local orchestration that uses `gameplan.engine` as the simulation substrate seam
- FastAPI endpoints for run, compare, export, and local library persistence
- named scenario fixtures and analyst-facing scenario catalog metadata
- export artifacts in JSON and CSV
- file-backed local persistence under `workspace_data/`
- a thin analyst workbench served by FastAPI
- regression tests that define the current semantic baseline

## Target State

The target-state MSim vision is materially broader:

- force-wide enlisted projection
- reusable shared manpower domain logic in `gameplan.domains.manpower`
- readiness and billet linkage
- training pipeline modeling
- uncertainty, sensitivity, and optimization workflows
- AI-grounded what-if exploration
- officer, warrant, and cross-service generalization
- eventual operational and budget integration

## What Is Real Now vs Planned

### Real in this repo now

- inline or named scenario execution
- deterministic projection
- sequential and phased processing-rule support
- policy tables and overrides for rates and accessions
- baseline-versus-variant comparison
- provenance metadata, exports, and local saved records
- local docs and visuals describing the larger platform direction

### Planned but not implemented here yet

- authoritative or live data adapters
- full-force graph loading and calibration
- `gameplan.data` integration replacing file-backed persistence
- shared `gameplan.domains.manpower` package consumption
- billet mapping and readiness summaries in the product
- Monte Carlo, sensitivity, and optimization execution paths
- AI tool orchestration over the simulation
- multi-user, realtime, or session-based workflows

## Boundary Guidance

Use this rule when reading the docs:

- if a document describes API routes, persistence behavior, fixtures, or the thin workbench, it is usually describing current repo behavior
- if a document describes readiness, optimization, AI-guided analysis, full-force projection, or cross-service generalization, it is usually describing target-state direction unless explicitly marked otherwise

## Why This Page Exists

The repo now has a strong vision set, but the implementation is intentionally earlier than that vision. This page keeps the documentation honest while preserving the larger direction.
