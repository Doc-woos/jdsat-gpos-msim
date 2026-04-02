# M3 Scenario Shape Foundation Checkpoint

**Date:** 2026-03-26  
**Status:** Force-wide scenario shape documented and initial loader support implemented

## Summary

The repo now has an explicit M3.1 design note for force-wide scenario structure and initial support for decomposed manifest-backed fixtures.

## What Landed

- `docs/force_wide_scenario_shape.md` records the preferred manifest-plus-reference-artifacts direction
- `backend/core/scenario_loader.py` now supports both:
  - current monolithic `scenarios/*.json` fixtures
  - directory-backed fixtures containing `scenario.json` plus referenced artifacts
- medium-scale decomposed example fixtures now exist in `scenarios/medium_infantry_team/`, `scenarios/medium_policy_team/`, `scenarios/medium_unordered_sequential/`, and `scenarios/medium_unordered_phased/`
- a shared synthetic force pack now exists in `scenarios/packs/force_pack_usmc_enlisted_v1/` with multiple named scenarios reusing it
- that synthetic pack now spans infantry, cyber, motor transport, aviation maintenance, and communications as an early cross-community enlisted scaffold
- the scaffold now includes deeper multi-grade ladders and additional year-phased baseline rate/accession behavior, including senior cyber and aviation cells that make later-year promotion behavior meaningful under the shared pack
- `scenarios/synthetic_enlisted_baseline/` and `scenarios/synthetic_enlisted_cyber_push/` prove one pack can support multiple scenario manifests with local divergence
- shared-pack artifacts now carry pack metadata and cell grouping tags for future reporting/linkage
- `ScenarioLoader.load_reference_context()` exposes app-local pack metadata and grouping context without changing the simulation contract
- named pack-backed projection runs now surface app-local summary rollups by OccFld, community, and force element while inline runs remain unchanged
- named pack-backed comparisons now surface grouped deltas and comparison drivers by community and force element without changing the neutral simulation contract
- named comparison exports and named saved comparison records now preserve grouped deltas so analyst-visible pack semantics survive beyond the workbench UI
- named pack-backed projection runs now expose app-local readiness pressure signals and grouped authorization/fill summaries derived from explicit authorization data when available, falling back to demand only when an authorization artifact is absent; explicit authorization artifacts are now also validated for full topology coverage so the readiness proxy does not silently degrade, the projection summary exposes the authorization basis used for those analyst-facing views, and comparison summaries now expose baseline/variant authorization provenance for grouped deltas; projection CSV exports now carry grouped fill/readiness sections for analyst reuse outside the workbench, comparison CSV exports now carry baseline/variant grouped fill and readiness sections alongside grouped deltas, the workbench explicitly calls out those richer CSV contents both in the export controls and in the loaded result panels, and analysts can now export dedicated compact summary CSV artifacts directly from the workbench
- pack validation now enforces shared pack_id/service consistency and full declared group dimensions
- regression tests now cover manifest expansion, named scenario discovery, and negative-path validation for directory-backed fixtures
- `backend/core/scenario_loader.py` now validates decomposed manifests and referenced artifacts before expansion

## Boundary Kept Intact

The simulation service still consumes the same expanded `ProjectionScenario` contract.

That means:

- simulation orchestration did not need to change
- app-facing API contracts did not need to change
- the new loader path remains an assembly concern, not a simulation concern

## Verification

```powershell
python -m pytest tests -q
```

Result at checkpoint: `62 passed`

## Remaining M3.1 Work

- preserve and extend the medium-scale decomposed fixture set as the assembly contract evolves
- decide the exact long-term artifact schema for topology, inventory, demand, and rate packs if broader reuse appears
- begin force-wide pack assembly only after medium-scale fixture behavior remains stable under regression coverage






