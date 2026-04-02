# Checkpoint: Phased Rule Added

**Date:** 2026-03-25

This checkpoint records the first repo state that supports both:

- `sequential_declared_order`
- `phased_standard_v1`

## Intent

Use this checkpoint when you want the dual-rule MVP but do not want later semantic changes layered on top.

## Validation

```text
python -m pytest tests -q
```
