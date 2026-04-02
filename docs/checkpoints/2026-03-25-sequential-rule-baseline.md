# Checkpoint: Sequential Rule Baseline

**Date:** 2026-03-25

This checkpoint records the current MVP baseline before any future rework of transition semantics.

## Baseline Behavior

- deterministic projection
- sequential transition processing
- named fixture loading
- baseline-vs-variant comparison

## Key Files

- `backend/domain/projection.py`
- `backend/domain/models.py`
- `backend/core/simulation.py`
- `backend/core/scenario_loader.py`
- `backend/api/models.py`
- `backend/api/routes.py`
- `scenarios/baseline_small.json`
- `scenarios/baseline_boosted.json`
- `tests/test_api.py`
- `tests/test_projection.py`

## Validation

```text
python -m pytest tests -q
```

Expected result when this checkpoint was recorded:

```text
7 passed
```

## Intent

If future work introduces phased or policy-specific transition ordering and we need to restart from the last known-good MVP baseline, restart from this checkpoint and ADR-0001.
