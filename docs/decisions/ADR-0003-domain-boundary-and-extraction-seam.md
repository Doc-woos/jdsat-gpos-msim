# ADR-0003: Domain Boundary and Extraction Seam

**Date:** 2026-03-26  
**Status:** Accepted  
**Applies To:** Standalone MSim deterministic projection foundation

## Decision

MSim keeps a three-layer internal seam for the current deterministic app:

- `backend/domain/*` holds pure manpower semantics and scenario/result domain models
- `backend/core/*` holds app orchestration, provenance, scenario loading, export, and persistence adapters
- `backend/api/*` holds HTTP contract models and thin route handlers only

This seam is also the intended extraction boundary for a future shared `gameplan.domains.manpower` package.

## What Counts As Pure Domain Logic

The following responsibilities are treated as pure domain logic in this repo:

- shared neutral scenario and algorithm schemas exposed through `backend/domain/models.py`
- app-local scenario metadata and final result envelopes layered in `backend/domain/models.py`
- career-flow graph construction in `backend/domain/graph_builder.py`
- deterministic year-step transition application in `backend/domain/projection.py`
- rule-sensitive manpower behavior such as accession, promotion, lateral move, and loss semantics
- policy matching or policy application helpers when they can be expressed without HTTP, filesystem, or product-output coupling

These are the first extraction candidates for shared-package work.

## What Remains App-Local

The following responsibilities remain app-local even if shared manpower logic later exists:

- FastAPI request and response wrappers in `backend/api/*`
- route wiring, fixture endpoints, and export endpoints
- local workspace persistence under `workspace_data/`
- artifact export formatting and filename conventions
- analyst-facing summaries, comparison drivers, and product wording
- scenario provenance metadata such as labels, authorship, notes, and app-facing version tags
- standalone repo environment bootstrapping via `backend/core/gameplan_loader.py`

## Initial Boundary Violations Identified

At the start of M1, the clearest boundary issues were:

- scenario fingerprint generation existed in both `backend/api/routes.py` and `backend/core/simulation.py`
- UTC timestamp generation existed in both `backend/api/routes.py` and `backend/core/simulation.py`
- policy summary and policy override helpers lived inside `backend/core/simulation.py`
- `backend/core/persistence.py` depended on `backend/api/models.py` for `LibraryRecord`
- `backend/core/exporter.py` depended on `backend/api/models.py` for export artifact types

These have been normalized into `backend/core/provenance.py`, `backend/domain/policy.py`, and `backend/domain/models.py` so core services no longer depend upward on API-layer contract types.

## Extraction Seam

If `gameplan.domains.manpower` is created, the preferred migration path is:

1. move pure scenario, graph, transition, and policy helpers into the shared package
2. keep `backend/core/simulation.py` as the app orchestration layer that composes shared algorithms
3. keep `backend/api/*`, persistence, exports, and workbench behavior in this repo

The goal is to extract algorithms, not to move the entire application into GamePlanOS.

For current planning, full app-facing result envelopes remain repo-local. `ProjectionScenario.metadata` also remains app-local because it serves provenance and product needs rather than neutral manpower algorithms. A future shared `gameplan.domains.manpower` package should expose neutral algorithms and supporting schemas first, while MSim continues to own provenance metadata, summaries, exports, persistence, and final API-facing result contracts.

## Consequences

Pros:

- clarifies what should and should not move into a future shared package
- reduces the chance that API or persistence concerns leak into manpower algorithms
- gives M1 refactoring a concrete target state

Cons:

- some existing code in `backend/core/simulation.py` still mixes orchestration and domain-adjacent helpers
- product-facing summary logic is still close to projection orchestration and will need later cleanup
- some persistence and export semantics are still app-local and will need later hardening before any storage abstraction change

## Follow-On Work

M1 should continue with:

- documenting the current versus intended responsibility split in `docs/implementation_m1.md`
- moving additional reusable helpers out of `backend/api/routes.py` and `backend/core/simulation.py`
- deciding which policy helpers should stay app-local versus become package candidates


