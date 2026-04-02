# M3 Grouped Readiness and Export Handoff Checkpoint

**Date:** 2026-03-27  
**Status:** Standalone app baseline is stable after grouped reporting, authorization-aware summaries, compact exports, and API/export cleanup

## Summary

The repo has moved beyond initial M3.1 scenario-shape groundwork into a stable analyst-facing baseline for pack-backed force projection.

The current app can now:

- run named pack-backed scenarios through the shared `gameplan.domains.manpower` seam
- summarize outcomes by `occfld`, `community`, and `force_element`
- compare named scenarios with grouped deltas and grouped narrative drivers
- compute grouped authorization/fill summaries and readiness pressure signals
- preserve those grouped views in full exports, compact summary exports, saved records, and the analyst workbench

This is still a grouped readiness proxy, not billet-level modeling.

## What Landed Since The Prior M3 Checkpoint

- named pack-backed projection summaries now expose grouped rollups, grouped fill summaries, readiness signals, and explicit `authorization_basis`
- named pack-backed comparisons now expose grouped deltas, grouped drivers, and baseline/variant authorization provenance
- comparison save/export flows now preserve the richer grouped summary path instead of dropping back to inline-style payloads
- projection CSV exports now include grouped fill/readiness sections when present
- comparison CSV exports now include grouped delta sections plus baseline/variant grouped fill and readiness sections
- compact summary export endpoints now exist for both projection and comparison flows
- the workbench now exposes `Export Summary CSV` actions and a visible export catalog
- result panels and export controls now explain which grouped sections a CSV will contain
- API/export wiring was cleaned up so named scenario comparison/export flows reuse local helpers instead of repeating load/compare logic
- export catalog definitions were moved into a shared app-local module
- exporter section assembly was reduced to shared helper paths instead of repeating grouped fill/readiness logic in multiple methods
- the upstream GamePlanOS Pydantic deprecation warning was removed at `gameplan/ai/graph/models/events.py`

## Stable Boundary Snapshot

Shared GamePlanOS package responsibilities:

- neutral manpower schemas and algorithms in `gameplan.domains.manpower`
- reusable engine/graph seams

Repo-local responsibilities:

- app-facing result envelopes and summary models
- scenario-pack assembly and pack metadata/grouping context
- provenance, exports, persistence, and API routes
- analyst-facing grouped reporting and readiness proxy behavior
- static workbench UX

Still intentionally repo-local for now:

- grouped authorization/fill/readiness summaries
- `ProjectionResult` / `ProjectionComparison`
- pack metadata and grouping context
- any future billet-level inputs

## Verification

```powershell
python -m pytest tests -q
```

Result at checkpoint: `87 passed`

## Recommended Next Step

Recommended next product step: deepen analyst reporting on the current grouped model before introducing billet-level schemas.

Specifically:

1. keep billet-level modeling out for now
2. document the grouped authorization/fill/readiness model clearly as the current readiness contract
3. improve analyst-facing reporting and interpretation on top of that grouped model
4. only introduce billet-level inputs when there is a concrete schema and data plan worth committing to

## Not Built Yet

- billet-level authorization or billet-fill modeling
- unit-level readiness semantics beyond grouped authorization/fill proxies
- Monte Carlo, sensitivity, or optimization workflows
- officer, warrant, or cross-service graph generalization
- live-data adapters
