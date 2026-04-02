# ADR-0001: Keep Sequential Transition Rule For MVP Baseline

**Date:** 2026-03-25  
**Status:** Accepted  
**Applies To:** Deterministic MVP projection slice

## Decision

The current MSim MVP uses a **sequential transition rule**.

Transitions are applied:

1. in the order declared in the scenario payload
2. against the current in-memory state after each prior transition has already mutated it
3. with deterministic rounding for source-based transfers

This is the active rule for:

- `POST /api/projection/run`
- `GET /api/projection/scenarios/{scenario_name}`
- `POST /api/projection/compare`
- `POST /api/projection/compare-named`

## Why This Decision Was Taken

This rule is the smallest stable behavior that:

- keeps the first slice deterministic and easy to inspect
- avoids introducing a separate phase scheduler before domain semantics are settled
- gives us a clear baseline for fixture-based regression testing
- keeps the code path simple enough to revise later without hidden coupling

## Current Semantics

For one projection year:

- `accession` adds a fixed amount to the target cell when encountered
- `promotion` and `lateral_move` transfer `round(inventory * rate)` from source to target using the source inventory at that moment
- `loss` removes `round(inventory * rate)` from the source using the source inventory at that moment

Because transitions mutate state in sequence, later transitions observe earlier changes from the same year.

## Explicit Non-Decision

We are **not** claiming this is the long-term manpower policy model.

We are intentionally deferring alternatives such as:

- phase-based processing (`accessions -> promotions -> losses`)
- same-period snapshot-based evaluation
- policy-specific ordering by transition type
- finer-grained fiscal or monthly processing semantics

## Consequences

Pros:

- very easy to reason about and test
- stable baseline for named fixtures and comparisons
- easy to replace once domain semantics are approved

Cons:

- results are sensitive to transition ordering in the scenario file
- not yet aligned to a formal manpower policy phase model
- comparison outputs will change if we later adopt phased processing

## Restart Baseline

If we later decide to abandon a new transition-processing approach, this decision marks the restart point.

Baseline files:

- `backend/domain/projection.py`
- `backend/core/simulation.py`
- `backend/api/routes.py`
- `scenarios/baseline_small.json`
- `scenarios/baseline_boosted.json`
- `tests/test_projection.py`
- `tests/test_api.py`

Baseline verification command:

```text
python -m pytest tests -q
```

Expected status at decision time:

```text
7 passed
```
