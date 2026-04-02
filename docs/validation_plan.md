# Validation Plan

**Date:** 2026-03-25

## Current Contract Checks

The MVP validation suite should prove the following behavior remains stable:

- root route serves the analyst workbench
- health route returns the expected app status payload
- fixture discovery lists the supported named scenarios
- scenario catalog returns analyst-facing labels and notes
- named scenario definition endpoint returns the stable fixture payload
- inline scenario execution returns the stable projection result shape
- run metadata includes timestamps, deterministic fingerprints, echoed scenario metadata, and policy summaries
- projection export returns a stable artifact envelope for JSON exports
- comparison export returns CSV content with embedded provenance comments
- comparison responses explain rule changes, policy deltas, and top outcome drivers
- library save endpoints persist scenario, run, and comparison records
- library list endpoint surfaces saved records from the local workspace
- named scenario execution preserves semantic provenance metadata
- baseline-vs-variant comparison returns stable deltas and highlight ordering
- invalid transition references fail request validation
- duplicate cell or transition identifiers fail validation
- policy tables and overrides require at least one cohort selector
- phased processing differs from sequential processing for scrambled transition order
- structured rate table entries replace matching rates by cohort and year
- rate overrides still stack after table replacement or base rates
- rate overrides change outcomes without changing the default sequential baseline
- year-windowed rate overrides affect only matching projection years
- structured accession table entries replace matching accession amounts by cohort and year
- accession overrides still stack after table replacement or base accession amounts

## Current Verification Command

```powershell
python -m pytest tests -q
```

## Stable Baseline Semantics

The default semantic checkpoint remains:

- `processing_rule: sequential_declared_order`
- `decision_ref: ADR-0001`
- `checkpoint_ref: 2026-03-25-sequential-rule-baseline`

The alternative phased mode remains:

- `processing_rule: phased_standard_v1`
- `decision_ref: ADR-0002`
- `checkpoint_ref: 2026-03-25-phased-rule-added`

## Manual Scenario Checks

Useful named scenarios for manual inspection:

- `Baseline Small Force`
- `Boosted Accessions Variant`
- `Rate Override Variant`
- `Year-2 Rate Override Variant`
- `Structured Rate Table Variant`
- `Year-2 Accession Override Variant`
- `Structured Accession Table Variant`
- `Unordered Sequential Reference`
- `Unordered Phased Reference`

## Manual Comparison Checks

Useful comparisons for narrative inspection:

- `Baseline Small Force` vs `Rate Override Variant`
- `Unordered Sequential Reference` vs `Unordered Phased Reference`

## Manual Library Checks

Useful local persistence checks:

- `POST /api/library/scenarios/save` with an inline scenario snapshot
- `POST /api/library/runs/save` with `baseline_small`
- `POST /api/library/comparisons/save` with `baseline_small` vs `baseline_boosted`
- `GET /api/library/records` after saves

## Manual Export Checks

Useful export paths for manual inspection:

- `POST /api/projection/export` with `baseline_small`
- `POST /api/projection/compare-export` with `baseline_small` vs `baseline_boosted`




