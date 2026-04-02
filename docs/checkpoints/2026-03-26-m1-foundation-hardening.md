# 2026-03-26 M1 Foundation Hardening

**Date:** 2026-03-26  
**Status:** Recorded checkpoint for the hardened deterministic projection baseline

## Summary

The standalone MSim repo now has a clearer internal seam between pure manpower logic, app orchestration, and API contract code while preserving the current deterministic MVP behavior.

## Included Changes

- provenance helpers centralized in `backend/core/provenance.py`
- policy summary and policy application helpers extracted into `backend/domain/policy.py`
- analyst-facing summary builders extracted into `backend/core/summary.py`
- shared library and export contracts moved into `backend/domain/models.py`
- scenario validation tightened for duplicate identifiers and policy cohort selectors
- persistence and export adapters now share slug and timestamp-token naming helpers
- direct regression tests added for policy validation, summary behavior, persistence ordering, and export artifact invariants

## Stable Semantic Baseline

The deterministic baseline remains:

- `processing_rule: sequential_declared_order`
- `decision_ref: ADR-0001`
- `checkpoint_ref: 2026-03-25-sequential-rule-baseline`

The phased alternative remains:

- `processing_rule: phased_standard_v1`
- `decision_ref: ADR-0002`
- `checkpoint_ref: 2026-03-25-phased-rule-added`

## Validation Status

Verification command:

```powershell
python -m pytest tests -q
```

Result at checkpoint: `43 passed`

## Notes

This checkpoint hardens the current app-local implementation; it does not create `gameplan.domains.manpower` yet. The next step after this checkpoint is M2 extraction planning or any remaining M1.4 coverage judged necessary for the current slice.
