# MSim Milestone Backlog

**Date:** 2026-03-27  
**Status:** Working execution backlog derived from `docs/roadmap.md`

## Purpose

This backlog converts the roadmap into milestone-based execution planning for the standalone MSim repository.

Each milestone contains:

- epics grouped by outcome
- concrete tasks that can be scheduled or ticketed
- a boundary label showing whether the work belongs in this repo, GamePlanOS shared packages, or both
- dependencies that define sensible sequencing

## Boundary Labels

- `Repo`: build in `C:\dev\jdsat-gpos-msim`
- `GamePlanOS`: build in `C:\dev\jdsat-gameplan-os`
- `Joint`: coordinated work across both repos

## Milestone M1: Stable Deterministic Projection Foundation

### Outcome

Preserve the current deterministic projection slice while making the codebase durable enough to support extraction and scale-up.

### Epic M1.1: Clarify Domain and Orchestration Boundaries

**Boundary:** `Repo`

Tasks:

- audit `backend/domain` and `backend/core` responsibilities and document the intended split
- identify pure manpower logic currently embedded in orchestration code
- move helper logic out of routes where it belongs in domain or core modules
- standardize naming around scenario, policy, projection, and comparison concepts
- document what remains intentionally app-local versus extraction candidates

Dependencies:

- none

### Epic M1.2: Stabilize Scenario and Result Contracts

**Boundary:** `Repo`

Tasks:

- review `backend/domain/models.py` for schema gaps against the roadmap direction
- define scenario versioning and compatibility expectations in docs
- tighten validation around policy inputs, transition references, and metadata expectations
- identify fields that are API contract versus internal convenience
- add regression tests for any contract behavior that is currently implicit

Dependencies:

- M1.1

### Epic M1.3: Strengthen Provenance and Persistence Semantics

**Boundary:** `Repo`

Tasks:

- review current fingerprint, timestamp, and metadata handling for stability
- document the expected provenance contract for runs, comparisons, and saved records
- define a persistence migration note from file-backed workspace records toward `gameplan.data`
- isolate persistence interfaces so storage backend changes do not force API rewrites
- add tests for persistence record shape and deterministic provenance behavior

Dependencies:

- M1.2

### Epic M1.4: Tighten Validation and Baseline Coverage

**Boundary:** `Repo`

Tasks:

- identify missing tests around error paths, fixture loading, export artifacts, and library saves
- add targeted tests for edge cases in policy application ordering
- add baseline fixtures for behavior likely to regress during refactoring
- verify the docs and tests agree on the MVP baseline semantics

Dependencies:

- M1.2

## Milestone M2: Reusable Manpower Domain Core Established

### Outcome

Create the first reusable manpower domain package and switch this app to consume it without copying logic.

### Epic M2.1: Define Extraction Boundary for Shared Manpower Logic

**Boundary:** `Joint`

Tasks:

- maintain `docs/manpower_extraction_plan.md` as the package-boundary note that maps current app-local logic to future shared modules
- classify current logic into pure algorithms, app orchestration, API contract, and product-specific summaries
- identify first extraction candidates with the lowest dependency surface
- define the initial public API for `gameplan.domains.manpower` around neutral algorithms and schemas rather than app-facing result envelopes

Dependencies:

- M1 complete

### Epic M2.2: Scaffold `gameplan.domains.manpower`

**Boundary:** `GamePlanOS`

Tasks:

- preserve and refine the package directory and exports following existing domain-package patterns
- keep package docs aligned with the actual public API
- maintain tests for pure-domain behavior independent of MSim app code
- refine module layout only when it materially improves reuse or clarity

Dependencies:

- M2.1

### Epic M2.3: Extract Initial Pure Algorithms

**Boundary:** `GamePlanOS`

Tasks:

- harden career graph construction logic in shared package code
- harden projection-year transition application helpers in shared package code
- harden policy matching and policy application helpers in shared modules
- preserve current semantics with test parity against the app baseline

Dependencies:

- M2.2

### Epic M2.4: Integrate Shared Package Back Into MSim

**Boundary:** `Repo`

Tasks:

- keep app imports pointed at `gameplan.domains.manpower`
- retain app-specific orchestration in `backend/core`
- remove remaining duplicated logic once replacement behavior is proven
- update tests and provenance docs to reflect the active shared-package boundary

Dependencies:

- M2.3

## Milestone M3: Full Enlisted-Force Projection Demonstrable

### Outcome

Scale from compact fixtures to a credible force-wide enlisted projection.

### Epic M3.1: Design the Force-Wide Scenario Shape

**Boundary:** `Repo`

Tasks:

- define configuration structure for large career graphs and force-wide scenario inputs in `docs/force_wide_scenario_shape.md`
- determine what belongs in scenario payloads versus external reference data
- design fixture strategy for small, medium, and force-wide scenarios
- document minimum data required to support a full enlisted-force run
- support directory-backed manifest fixtures that expand into the current scenario contract

Dependencies:

- M2 complete

### Epic M3.2: Build Full Enlisted Career Graph Representation

**Boundary:** `Joint`

Tasks:

- define node and edge conventions for the enlisted career network
- support larger topology loading without hand-authored JSON becoming unmanageable
- add validation for graph completeness and invalid topology conditions
- create at least one force-wide reference configuration

Dependencies:

- M3.1

### Epic M3.3: Expand Policy and Projection Coverage

**Boundary:** `Joint`

Tasks:

- extend accession, promotion, retention, and loss semantics beyond the compact MVP assumptions
- add support for richer policy tables and force-wide cohort targeting
- verify execution remains deterministic for deterministic modes
- add reporting suitable for force-wide outputs by specialty and grade

Dependencies:

- M3.2

### Epic M3.4: Calibrate and Validate Early Force-Wide Scenarios

**Boundary:** `Repo`

Tasks:

- assemble synthetic or public-data-calibrated baseline inputs
- create reference scenarios for key communities such as infantry and cyber
- define expected sanity checks for force-wide output ranges
- add performance and correctness validation for larger runs

Dependencies:

- M3.3

## Milestone M4: Sensitivity and Optimization Workflows Available

### Outcome

Support uncertainty-aware policy analysis rather than only deterministic point estimates.

### Epic M4.1: Add Monte Carlo Execution Path

**Boundary:** `Joint`

Tasks:

- define replication orchestration requirements for manpower scenarios
- determine whether existing `gameplan.engine` patterns are sufficient or need extension
- add MSim-side configuration for stochastic execution
- produce aggregated result envelopes suitable for analyst consumption

Dependencies:

- M3 complete

### Epic M4.2: Add Sensitivity Analysis Workflow

**Boundary:** `Repo`

Tasks:

- identify the first policy levers to expose for sensitivity analysis
- wire `gameplan.analytics` methods into MSim workflows
- define result schemas and summaries for sensitivity outputs
- add tests and example scenarios that prove the workflow is useful

Dependencies:

- M4.1

### Epic M4.3: Add First Optimization Use Case

**Boundary:** `Repo`

Tasks:

- choose the first optimization problem, such as accession planning or retention allocation
- define objective, constraints, and required data inputs
- wire optimization outputs into comparison and explanation flows
- document assumptions and validation limits clearly

Dependencies:

- M4.2

## Milestone M5: Billet and Readiness Linkage In Place

### Outcome

Connect manpower inventory to the structure and readiness questions the force actually cares about.

### Epic M5.1: Align MSim Inventory Model With Organization Concepts

**Boundary:** `Joint`

Tasks:

- map MSim inventory cells to `gameplan.organization` concepts such as units, positions, and vacancies
- identify extensions needed for specialty and grade-aware billet modeling
- define the minimum viable readiness linkage model
- document what remains app-specific versus package-worthy

Dependencies:

- M3 complete

### Epic M5.2: Add Authorization and Vacancy Workflows

**Boundary:** `Repo`

Tasks:

- define authorization input models and load paths
- compute inventory versus authorization gaps by selected grouping
- expose billet fill and vacancy summaries through the API
- add fixture and regression coverage for readiness-oriented scenarios

Dependencies:

- M5.1

### Epic M5.3: Add Training Pipeline Modeling

**Boundary:** `Joint`

Tasks:

- define training nodes, throughput constraints, and washout assumptions
- determine which training concepts belong in shared manpower logic versus app workflows
- add training bottleneck reporting and scenario hooks
- validate the effect of training capacity on force outcomes

Dependencies:

- M5.2

## Milestone M6: AI-Grounded Scenario Exploration Available

### Outcome

Give analysts a natural-language workflow that is grounded in real simulation tools and reproducible outputs.

### Epic M6.1: Define Tool-Facing Simulation and Analysis Interfaces

**Boundary:** `Repo`

Tasks:

- define structured tool schemas for scenario build, run, compare, sensitivity, and optimization actions
- ensure tool inputs and outputs map cleanly to existing API or service boundaries
- document auditability and provenance expectations for AI workflows

Dependencies:

- M4 complete

### Epic M6.2: Implement App-Specific AI Workflows

**Boundary:** `Repo`

Tasks:

- build orchestration prompts and workflow patterns on top of `gameplan.ai`
- expose grounded tools only, not open-ended unsupported reasoning
- add analyst-facing explanation outputs tied to actual simulation results
- test AI workflows against representative policy questions

Dependencies:

- M6.1

### Epic M6.3: Optional Thin MCP Layer

**Boundary:** `Joint`

Tasks:

- decide whether MCP adds value beyond existing app APIs and tools
- if yes, implement MCP as a thin wrapper over existing MSim functions
- avoid logic duplication between MCP handlers and app services

Dependencies:

- M6.2

## Milestone M7: Officer, Warrant, and Service Generalization Proven

### Outcome

Show that the architecture generalizes by swapping policy, data, and graph topology rather than rewriting the engine.

### Epic M7.1: Add Officer and Warrant Modeling Foundations

**Boundary:** `Joint`

Tasks:

- define officer and warrant graph conventions
- add support for cross-subgraph transitions such as enlisted-to-officer and warrant accession
- expand scenario and reporting models where required
- validate combined-force semantics with targeted scenarios

Dependencies:

- M3 complete

### Epic M7.2: Introduce Service Configuration Abstraction

**Boundary:** `GamePlanOS`

Tasks:

- define a reusable service-policy abstraction for manpower modeling
- separate service-specific policy logic from shared engine behavior
- document how a new service plugs in via graph, policy, and data adapters

Dependencies:

- M7.1

### Epic M7.3: Prototype a Second-Service Path

**Boundary:** `Repo`

Tasks:

- select one additional service as a proving case
- define a minimal scenario pack or topology to exercise the abstraction
- document the gaps that remain after the prototype

Dependencies:

- M7.2

## Milestone M8: Operational and Budget Integration Demonstrated

### Outcome

Extend the manpower platform into readiness, force generation, and cost-aware decision support.

### Epic M8.1: Add Cost and Budget Analysis Foundations

**Boundary:** `Repo`

Tasks:

- define pay, incentive, or training cost input models for at least one policy workflow
- add cost outputs to projection or optimization summaries
- validate cost assumptions and provenance documentation

Dependencies:

- M4 complete

### Epic M8.2: Add Operational Readiness and Force-Generation Views

**Boundary:** `Repo`

Tasks:

- define the first operational questions MSim should answer from manpower outputs
- connect readiness-linked outputs into force-generation style summaries
- add scenario comparisons that highlight operational consequences of manpower changes

Dependencies:

- M5 complete

### Epic M8.3: Define Live-Data Integration Strategy

**Boundary:** `Joint`

Tasks:

- assess which source adapters are worth building first
- define adapter boundaries between MSim and `gameplan.data`
- document a migration path from fixtures and synthetic inputs to authoritative feeds
- keep offline analytical operation possible even with live-data support added later

Dependencies:

- M5 complete

## Cross-Cutting Epic C1: Documentation and Decision Records

**Boundary:** `Repo`

Tasks:

- keep `docs/README.md`, `docs/current_state_vs_target_state.md`, and `docs/visuals.md` aligned with repo reality
- keep `docs/roadmap.md` and this backlog aligned as priorities change
- add ADRs when major semantic or architecture choices are made
- record checkpoints before large behavior shifts
- keep provenance notes current when platform boundaries move

## Cross-Cutting Epic C2: Testing and Validation Discipline

**Boundary:** `Joint`

Tasks:

- maintain app-level regression tests for user-visible behavior
- add shared-package tests for pure manpower algorithms
- add scenario validation assets for small, medium, and force-wide cases
- define performance checks for larger runs before scale-up work lands

## Cross-Cutting Epic C3: Packaging and Dependency Strategy

**Boundary:** `Joint`

Tasks:

- replace ad hoc import shims where practical with a cleaner dependency path
- define how this standalone repo consumes GamePlanOS packages during development and CI, building on the local bootstrap, verification, and validation scripts
- keep repo portability and local development ergonomics acceptable

## Recommended Next Backlog Slice

The next slice to execute from this backlog is:

1. Epic M5.2: deepen grouped authorization and vacancy workflows on the current scenario contract
2. Cross-Cutting Epic C1: keep `docs/session_handoff.md`, the latest checkpoint, and readiness docs aligned with actual behavior
3. Epic M3.4: continue validating and extending synthetic pack-backed scenarios only where they improve grouped analyst reporting
4. defer billet-level input design until there is a concrete schema and data plan worth committing to

That sequence keeps the app focused on credible analyst value on top of the current grouped model instead of jumping early into billet-level complexity.



