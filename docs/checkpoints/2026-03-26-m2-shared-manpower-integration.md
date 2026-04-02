# M2 Shared Manpower Integration Checkpoint

**Date:** 2026-03-26  
**Status:** Shared package scaffolded and consumed by the standalone app

## Summary

A first `gameplan.domains.manpower` package now exists in `C:\dev\jdsat-gameplan-os` and the standalone MSim repo now consumes its neutral manpower schemas and pure helpers.

The current repo keeps ownership of:

- app-facing result envelopes
- provenance and export semantics
- persistence adapters
- analyst-facing summaries and comparison wording
- HTTP request and response contracts

## Shared Package Scope

The shared package currently owns:

- neutral manpower schemas
- career-flow graph construction
- deterministic projection-year execution helpers
- policy table and override application helpers
- compact policy summary helpers
- package-level docs and pure-domain tests

## Repo Consumption Boundary

The standalone app now uses thin wrappers in `backend/domain/*` to consume the shared package while preserving the local app contract. Most neutral shared types are now direct aliases rather than empty local subclasses.

The active seam is:

- `backend/domain/models.py`: shared neutral schemas plus app-only envelopes
- `backend/domain/graph_builder.py`: thin wrapper over shared graph builder
- `backend/domain/projection.py`: thin wrapper over shared projection helpers
- `backend/domain/policy.py`: thin wrapper over shared policy helpers
- `backend/core/simulation.py`: app-local orchestration and coercion into app-facing result types

## Verification

Standalone app:

```powershell
python -m pytest tests -q
```

Result at checkpoint: `45 passed`

Local automation now exists via `npm run deps:bootstrap`, `npm run deps:verify-gameplan`, and the contributor-facing `npm run validate`.

Shared package:

```powershell
python -m pytest -o addopts='' gameplan/domains/manpower/tests/test_manpower.py -q
```

Result at checkpoint: `8 passed`

## Known Remaining Gaps

- editable-install consumption of the external GamePlanOS repo is now verified in the local app environment
- the local source-path shim in `backend/core/gameplan_loader.py` remains as a fallback only
- some local wrapper types still duplicate shared names in order to preserve the current app contract
- broader package verification still depends on the external GamePlanOS environment being provisioned with optional dependencies

## Next Steps

1. remove remaining local pure-domain duplication only where the app contract does not depend on it
2. carry the editable-install dependency path into repeatable CI once local bootstrap automation has proven stable
3. begin force-wide scenario-shape work only after the package boundary remains stable under regression coverage
