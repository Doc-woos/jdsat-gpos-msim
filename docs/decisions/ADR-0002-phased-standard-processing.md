# ADR-0002: Add Phased Standard Processing Rule

**Date:** 2026-03-25  
**Status:** Accepted  
**Applies To:** Deterministic MVP projection slice

## Decision

Add `phased_standard_v1` as an explicit alternative processing rule while preserving `sequential_declared_order` as the default baseline and restart point.

## Phased Standard V1

Annual transition phases execute in this fixed order:

1. `accession`
2. `promotion`
3. `lateral_move`
4. `loss`

Within a phase, transitions are still processed in declared order.

## Why

This introduces explicit phase semantics without breaking the keyed sequential baseline. It lets analysts compare rule-sensitive outcomes while keeping the original checkpoint intact.

## Preservation Rule

- `sequential_declared_order` remains the default processing rule.
- ADR-0001 and the sequential baseline checkpoint remain the fallback restart point.

## Checkpoint

This rule maps to checkpoint `2026-03-25-phased-rule-added`.
