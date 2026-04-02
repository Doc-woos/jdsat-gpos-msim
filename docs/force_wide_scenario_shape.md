# Force-Wide Scenario Shape

**Date:** 2026-03-27  
**Status:** M3.1 design note for force-wide enlisted scenario structure

## Purpose

This document defines the recommended scenario shape for moving MSim from compact demo fixtures to force-wide enlisted projection.

It does not change the current API or loader yet. It establishes the target structure that future loader, validation, and fixture work should follow.

## Current Constraint

The current repo loads named fixtures from `scenarios/*.json` and validates a single monolithic `scenario` payload.

That works for the compact MVP because the fixture includes:

- `career_cells`
- `transitions`
- optional policy tables and overrides
- app-local provenance metadata

For force-wide enlisted projection, that shape becomes brittle because:

- the full enlisted graph is too large to hand-author safely in one file
- topology, baseline inventory, and policy experiments change at different rates
- calibration and reference data need separate versioning from policy experiments
- the same force structure should support many scenario variants without duplication

## Design Goals

The force-wide shape should:

- preserve the current stable simulation contract where practical
- keep neutral manpower semantics in shared `gameplan.domains.manpower` types
- keep app-local provenance metadata in this repo
- separate reusable reference data from scenario-specific overrides
- support small, medium, and force-wide fixtures with the same conceptual model
- stay portable for offline development and file-based testing
- avoid requiring `gameplan.data` before the force-wide model is proven

## Recommendation

Use a two-layer shape:

1. a small scenario manifest that defines the run intent
2. one or more referenced data artifacts that provide topology, inventory, demand, and policy baselines

The manifest becomes the analyst-facing scenario. The referenced artifacts become reusable force inputs.

## Proposed Artifact Split

### Scenario Manifest

The manifest should remain app-facing and relatively small.

Recommended responsibilities:

- scenario identity
- horizon and processing rule
- app-local metadata
- timestep or planning cadence when introduced
- references to baseline topology and data artifacts
- optional scenario-local policy overrides
- optional scenario-local inventory or demand adjustments

### Reference Artifacts

Reference artifacts should hold larger reusable inputs.

Recommended categories:

- career topology
- baseline inventory snapshot
- baseline authorization or demand snapshot
- baseline rate tables
- baseline accession tables
- optional service or community configuration packs

This lets one force structure support many scenarios without cloning thousands of cells and transitions into each scenario file.

The current repo now also proves shared-pack reuse through `scenarios/packs/force_pack_usmc_enlisted_v1/` plus multiple named manifests that reference it. That synthetic pack also carries grouping metadata such as OccFld, community, and force-element tags for future reporting and billet/readiness linkage, and now acts as an early cross-community enlisted scaffold rather than a tiny toy cluster. It now includes deeper multi-grade ladders across infantry, cyber, aviation maintenance, motor transport, and communications, including senior cyber and aviation nodes that stress later-year promotion behavior. It also now includes richer year-phased baseline behavior, which is a better stress test of projection semantics than adding breadth alone.

## Recommended Manifest Shape

A future force-wide manifest should look conceptually like this:

```json
{
  "scenario": {
    "scenario_id": "usmc-enlisted-fy2028-baseline",
    "horizon_years": 10,
    "processing_rule": "phased_standard_v1",
    "metadata": {
      "version": "0.3.0",
      "label": "USMC Enlisted FY2028 Baseline",
      "created_by": "msim-team",
      "source": "synthetic-force-pack",
      "notes": "Force-wide enlisted baseline for early M3 validation."
    },
    "scenario_refs": {
      "topology": "force_pack_usmc_enlisted_v1/topology.json",
      "inventory": "force_pack_usmc_enlisted_v1/inventory_fy2028.json",
      "demand": "force_pack_usmc_enlisted_v1/demand_fy2028.json",
      "rates": "force_pack_usmc_enlisted_v1/rate_tables.json",
      "accessions": "force_pack_usmc_enlisted_v1/accession_tables.json"
    },
    "policy_overrides": {
      "rate_overrides": [],
      "accession_overrides": []
    },
    "scenario_adjustments": {
      "inventory_deltas": [],
      "demand_deltas": []
    }
  }
}
```

The exact field names can change, but the separation should not.

## What Belongs In the Manifest

Keep these in the scenario manifest:

- `scenario_id`
- `horizon_years`
- `processing_rule`
- app-local `metadata`
- scenario-to-artifact references
- scenario-local policy overrides for what-if analysis
- small scenario-local deltas for inventory or demand adjustments

These are analyst-owned or experiment-owned inputs.

## What Should Move Out of the Manifest

Move these into referenced artifacts for force-wide runs:

- the full `career_cells` list
- the full `transitions` list
- force-wide baseline inventory snapshots
- force-wide demand or authorization snapshots
- large baseline rate tables
- large baseline accession tables

These are reference-data assets, not scenario-specific reasoning inputs.

## Reference Artifact Shapes

### Topology Artifact

Owns structural force shape:

- specialty-grade cells
- transition topology
- optional grouping tags such as OccFld, community, or force element
- optional artifact metadata such as pack id, service, snapshot, and artifact id
- optional validation metadata for source and version

### Inventory Artifact

Owns the starting inventory state for a named time slice:

- cell inventory counts
- optional subpopulation tags if later needed
- snapshot date or fiscal-year reference

### Demand Artifact

Owns the baseline required force shape:

- cell-level demand or authorization counts
- optional organizational rollups if later linked to billets
- source version and snapshot date

### Rate Artifact

Owns baseline behavior assumptions:

- promotion, loss, and lateral-move rates by cohort and year window
- accession tables by target cohort and year window
- calibration source and validity window

## Loader Implications

The current loader reads one file and validates one payload. A force-wide loader should instead:

1. load the manifest
2. resolve local referenced artifacts
3. materialize a fully expanded `ProjectionScenario`-compatible payload in memory
4. apply scenario-local overrides and adjustments last
5. validate the expanded scenario before simulation

That preserves the current simulation core while changing only scenario assembly.

The loader path should use typed manifest and artifact validation so decomposed scenarios fail early with contract errors instead of low-level key or path errors. The current repo now does this in `backend/core/scenario_loader.py` for medium-scale decomposed fixtures.

## Expansion Order

The assembly order should be deterministic:

1. topology artifact
2. inventory artifact
3. demand artifact
4. baseline rates and accessions
5. scenario-local adjustments
6. scenario-local overrides
7. final validation

That order keeps baseline data distinct from analyst what-if inputs.

## Fixture Strategy

Current medium-scale examples in this repo:

- `scenarios/medium_infantry_team/` for baseline manifest expansion
- `scenarios/medium_policy_team/` for policy-heavy manifest expansion
- `scenarios/medium_unordered_sequential/` and `scenarios/medium_unordered_phased/` for processing-rule divergence under the same referenced artifacts
- `scenarios/synthetic_enlisted_baseline/` and `scenarios/synthetic_enlisted_cyber_push/` for shared-pack reuse across multiple named scenarios


Use three fixture tiers.

### Small

Keep the current single-file compact fixtures.

Purpose:

- unit tests
- contract tests
- explainable examples

### Medium

Add decomposed fixtures for one community or OccFld.

Purpose:

- loader and assembly tests
- early topology scaling tests
- policy-override tests against referenced artifacts

### Force-Wide

Add decomposed force packs for the full enlisted model.

Purpose:

- integration and performance testing
- force-wide reporting validation
- baseline-versus-variant scenario comparisons without duplicated baseline files

## Minimum Data Required For a Full Enlisted Run

A credible force-wide enlisted run needs, at minimum:

- specialty-grade cell universe for the enlisted force
- promotion, accession, lateral-move, and loss transition topology
- starting inventory by cell for one baseline snapshot
- baseline demand or authorization by cell
- baseline rate assumptions by cohort
- baseline accession assumptions by target cohort
- grouping metadata sufficient for reporting by grade and specialty

Without those inputs, the run may be executable but not analytically credible.

## What Stays App-Local

These concerns stay in this repo even when the force-wide shape lands:

- manifest metadata for provenance and labels
- named fixture conventions under `scenarios/`
- scenario assembly and file resolution behavior
- export and persistence behavior
- analyst-facing labels and summaries

## What Could Move Later

The following may become shared-package concerns later if multiple apps need them:

- neutral reference-artifact schemas
- artifact expansion helpers from manifest to full scenario payload
- graph validation helpers for large topology packs

Do not move them yet unless a second consumer appears.

The current repo now keeps those grouping and artifact-metadata semantics app-local through `ScenarioLoader.load_reference_context()`, which is a better fit than pushing them into the neutral simulation contract prematurely. Those app-local group tags now also feed named-scenario projection summaries and named-comparison summaries, so analysts can review rollups and deltas by OccFld, community, and force element without changing the neutral simulation payload. Named comparison exports and saved comparison records now preserve those grouped deltas as well, which keeps the richer comparison view portable beyond the workbench. The same app-local grouping seam now also drives lightweight readiness pressure signals and grouped authorization/fill summaries for named pack-backed projections, using explicit authorization artifacts when present and falling back to grouped demand only as a compatibility path until billet-level linkage exists. When an explicit authorization artifact is present, the loader now requires full topology coverage so fill summaries do not silently mix authoritative and fallback counts. Projection summaries also now expose an app-local authorization-basis field so analysts can see whether grouped fill/readiness views came from explicit authorization data or the demand fallback path. Comparison summaries now carry the same provenance for baseline and variant grouped views so grouped deltas remain interpretable. Projection CSV exports now also include grouped fill and readiness sections, and comparison CSV exports now carry baseline/variant grouped fill and readiness sections alongside grouped deltas, so the analyst-facing authorization and readiness view survives outside the workbench.

Within that app-local seam, group dimensions should be treated as a contract: if a topology artifact declares grouping dimensions, every cell in that topology should provide the full declared set, and all referenced artifacts should agree on pack identity.

## Near-Term Implementation Sequence

1. add this design note and treat it as the M3.1 source of truth
2. preserve and expand the current medium-scale decomposed fixtures before force-wide data
3. extend `ScenarioLoader` to resolve manifest references into a full scenario payload
4. keep the simulation service consuming the same expanded `ProjectionScenario` contract
5. add force-wide packs only after medium-scale assembly is proven

## Decision Recorded

For force-wide enlisted projection, the repo should not continue scaling by stuffing the entire force into one monolithic scenario JSON file.

The preferred direction is a small manifest plus referenced baseline artifacts, expanded into the existing scenario contract at load time.






