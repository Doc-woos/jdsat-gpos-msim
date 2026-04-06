# MSim Roadmap

**Date:** 2026-03-27  
**Status:** Working roadmap for the standalone app and the broader MSim platform direction

## Purpose

This roadmap translates the larger MSim platform vision into a phased build plan for this standalone repository.

It is grounded in:

- the current repo structure and MVP slice
- the local reference docs in this repo
- the currently available GamePlanOS package structure under `C:\dev\jdsat-gameplan-os`
- local roadmap, checkpoint, and provenance notes in this repo

Note: the previously referenced GamePlanOS files `C:\dev\jdsat-gameplan-os\apps\msim\docs\08-platform-vision.md` and `C:\dev\jdsat-gameplan-os\apps\msim\docs\09-platform-reuse-plan.md` are not present in the current checkout.

This document distinguishes:

- what should be built in this repo now
- what should move into shared GamePlanOS packages
- what should be deferred until the simulation and data model are stronger

## Strategic Goal

MSim is intended to evolve from a deterministic manpower projection MVP into a force analytics platform that:

- models the personnel lifecycle across recruit, train, assign, deploy, retain, promote, lateral move, and separate
- connects manpower flows to force structure, readiness, and capability
- uses reusable GamePlanOS packages for simulation, graph, analytics, data, and AI
- keeps service-specific policy separate from generic simulation mechanics
- generalizes beyond USMC after the architecture is proven

## Current State

A concise implementation-to-vision summary now lives in `docs/current_state_vs_target_state.md`.

This repo currently implements a narrow but useful foundation:

- deterministic manpower projection
- app-local manpower domain types and deterministic projection logic under `backend/domain/`
- app-local result envelopes layered over that local manpower seam
- direct use of `gameplan.engine` and `gameplan.graph`
- FastAPI endpoints for run, compare, export, compact summary export, export catalog, and local library persistence
- static analyst workbench served by FastAPI
- decomposed manifest-backed scenarios and reusable synthetic force packs
- app-local grouped reporting by `occfld`, `community`, and `force_element`
- grouped authorization/fill summaries and readiness pressure signals for named pack-backed scenarios
- analyst takeaway strings, ranked watchlists, and explanation trails in API and export summaries
- fixture-based tests that define the current stable contract
- restart-oriented documentation including `docs/session_handoff.md` and the latest dated checkpoint

This is still an early platform slice, not billet-level readiness modeling or the full platform.

## Roadmap Principles

- Build in this repo unless a capability is clearly a reusable GamePlanOS package concern.
- Reuse `gameplan.*` and `@gameplan/*` capabilities before introducing new infrastructure.
- Keep manpower algorithms pure and portable.
- Keep app orchestration, API wiring, and product-specific UX in this repo.
- Do not lead with AI, realtime, or frontend complexity before the simulation model is credible.
- Treat data provenance, validation, and testability as first-class requirements.

## Workstreams

The roadmap spans four parallel workstreams:

- Domain: manpower algorithms, policy rules, career graph semantics, readiness and training concepts
- Platform: reuse and extension of shared GamePlanOS packages
- Product: analyst workflows, API contracts, scenario management, exports, UI, and explanation layers
- Data: fixtures, calibration, adapters, persistence, and provenance

## Phase 1: Harden the Projection Foundation

### Goal

Turn the current MVP into a durable projection foundation with clearer boundaries and fewer app-local shortcuts.

### Build in this repo

- stabilize the current scenario and result contracts
- cleanly separate pure manpower logic from API and orchestration code
- tighten provenance, versioning, and validation semantics
- reduce coupling between tests and incidental file layouts
- prepare current persistence and scenario loading for later `gameplan.data` migration

### Reuse from GamePlanOS

- `gameplan.engine` for simulation runtime
- `gameplan.graph` for career-flow validation and topology
- `gameplan.guides.app_structure_guide` patterns for code placement

### Deliverables

- clarified domain boundary between `backend/domain` and `backend/core`
- stronger scenario versioning and metadata guidance
- documented persistence migration path
- expanded validation coverage for projection semantics and artifact stability

### Dependencies

- current repo documentation baseline established
- none beyond the current repo and the GamePlanOS reference source

### Exit Criteria

- projection, comparison, export, and library flows remain stable
- app-specific orchestration is distinct from pure manpower logic
- current tests remain the semantic baseline for the MVP

## Phase 2: Establish a Reusable Manpower Domain Core

### Goal

Create a clean extraction boundary for a shared manpower domain package while keeping this app functional.

### Build in this repo

- refactor current manpower rules toward package-friendly pure functions
- define interfaces for policy inputs, graph construction, and projection calculations
- keep the standalone app functional until a shared package actually exists
- consume the shared package once it exists without breaking the standalone app

### Build in GamePlanOS

- create and harden `gameplan.domains.manpower`
- keep pure manpower algorithms and neutral schemas there
- maintain package docs and pure-domain tests following existing domain-package patterns

### Candidate Shared Algorithms

- career graph builder
- loss model
- accession model
- promotion model
- retention model
- lateral move model
- cohort-flow helpers
- policy schema helpers

### Keep in this repo

- FastAPI routes
- scenario file conventions
- app-specific orchestration
- product-specific summaries and exports
- final app-facing result envelopes such as `ProjectionResult` and `ProjectionComparison`
- analyst workbench behavior

### Dependencies

- completion of Phase 1 boundary cleanup

### Exit Criteria

- a shared manpower package exists and the extraction boundary is documented concretely in `docs/manpower_extraction_plan.md`
- this repo consumes shared manpower algorithms without copied code
- pure domain tests can run independently of API tests

## Phase 3: Scale to Full Enlisted-Force Projection

### Goal

Move from compact demonstration fixtures to a credible full enlisted-force projection model.

### Build in this repo

- scenario loaders and configuration structures for force-wide runs
- orchestration for larger graphs and longer horizons
- reporting suitable for force-wide outputs
- synthetic or public-data-calibrated scenario packs

### Reuse from GamePlanOS

- `gameplan.engine` execution model
- `gameplan.graph` topology and analysis
- `gameplan.analytics` where summary metrics or diagnostics already fit

### Build in shared packages if needed

- graph or analytics helpers that are clearly reusable beyond MSim

### Deliverables

- force-wide scenario shape documented in `docs/force_wide_scenario_shape.md`
- full enlisted career graph representation
- policy-capable projection across the enlisted force
- stable reporting by specialty and grade at force-wide scale
- validation scenarios for key communities such as infantry and cyber

### Dependencies

- Phase 2 manpower core or an equivalent app-local boundary that can later be extracted

### Exit Criteria

- run a multi-year full enlisted-force projection
- compare baseline and variant policy cases without code changes
- demonstrate that the architecture scales beyond toy fixtures

## Phase 4: Add Uncertainty, Sensitivity, and Optimization

### Goal

Extend MSim from deterministic projection to decision-support analytics.

### Build in this repo

- scenario-level Monte Carlo orchestration if shared support is not yet sufficient
- analyst-facing uncertainty summaries and comparison workflows
- optimization workflow wiring for manpower questions

### Reuse from GamePlanOS

- `gameplan.analytics` for sensitivity analysis, optimization primitives, and statistics
- `gameplan.engine` analytical execution patterns where applicable

### Candidate Use Cases

- which policy levers drive the most variance in fill rates
- what accession plan minimizes shortages under constraints
- what retention mix best improves a target community

### Dependencies

- credible force-wide model and stable policy inputs from Phase 3

### Exit Criteria

- analysts can evaluate uncertainty, not just point estimates
- sensitivity outputs identify the highest-leverage policy drivers
- at least one optimization workflow is demonstrable end to end

## Phase 5: Connect to Force Structure, Billets, and Readiness

### Goal

Connect projected inventory to the force that must be manned.

### Build in this repo

- app-specific readiness views and APIs
- readiness-oriented summaries and scenario workflows
- training and pipeline orchestration where product-specific behavior is needed

### Extend in GamePlanOS

- `gameplan.organization` conventions or fields for specialty and grade-aware billet modeling
- any reusable readiness or manning metrics that belong in shared packages

### Deliverables

- inventory versus authorization views
- billet fill and vacancy metrics
- training pipeline throughput and bottleneck analysis
- readiness-oriented outputs by unit or force-structure grouping

### Dependencies

- Phase 3 force-wide manpower projection
- organization-model alignment in shared packages or app conventions

### Exit Criteria

- MSim can explain not only inventory levels, but where the force is underfilled
- training constraints and readiness impacts are visible in analysis outputs

## Phase 6: Add AI-Native Analyst Workflows

### Goal

Support natural-language scenario exploration backed by real simulation and analytics tools.

### Build in this repo

- domain-specific analysis tools over scenario creation, projection, comparison, sensitivity, and optimization
- app-specific AI orchestration and explanation prompts
- analyst workflow UX for asking and reviewing what-if questions

### Reuse from GamePlanOS

- `gameplan.ai` provider abstraction and orchestration patterns
- domain AI tool conventions from existing GamePlanOS packages
- optional `gameplan.catalog` registration for discoverable tools

### Defer Until This Phase

- free-form chat interfaces without tool grounding
- MCP transport layers beyond thin wrappers over existing functions

### Dependencies

- stable simulation semantics
- reliable scenario schemas
- useful sensitivity and comparison outputs from earlier phases

### Exit Criteria

- AI can execute grounded what-if workflows against actual tools
- outputs remain auditable and reproducible
- analyst trust is supported by structured inputs, not opaque reasoning

## Phase 7: Integrate Officer, Warrant, and Cross-Service Generalization

### Goal

Prove that the architecture generalizes by changing policy and graph topology rather than rewriting the engine.

### Build in this repo

- app-specific service configuration and scenario packaging
- combined-force reporting and product workflows

### Build or extend in GamePlanOS

- shared abstractions for service-specific policy modules
- shared manpower graph and policy helpers where reusable

### Deliverables

- officer subgraph support
- warrant pathways
- enlisted-to-officer and warrant transitions
- service configuration abstraction
- at least one additional-service prototype path

### Dependencies

- strong shared manpower core
- clear policy/data/engine separation from earlier phases

### Exit Criteria

- a new service model is primarily a new graph, policy set, and data adapter
- the engine and product shell do not require major rewrites

## Phase 8: Add Operational and Budget Integration

### Goal

Connect manpower outcomes to broader force-generation, readiness, and cost questions.

### Build in this repo

- product-specific operational and cost analysis workflows
- scenario and reporting UX for downstream decision support

### Reuse or extend in GamePlanOS

- analytics primitives
- data-layer capabilities
- AI-assisted integration workflows

### Candidate Outcomes

- force generation and deployment-to-dwell analysis
- cost implications of policy changes
- integration with operational planning assumptions
- support for streaming or near-real-time data when justified

### Dependencies

- readiness linkage from Phase 5
- stronger live-data strategy than the current fixture-first model

### Exit Criteria

- MSim supports force-management questions that connect people, readiness, and cost
- operational integration is additive, not a distortion of the manpower core

## Repo vs Shared Package Boundaries

### Keep in this repo

- app APIs
- scenario fixtures and analyst workflows
- product-specific result contracts
- exports and workbench UX
- app orchestration and deployment choices
- repo-local docs, ADRs, and checkpoints

### Move to shared GamePlanOS packages when mature

- pure manpower algorithms
- reusable policy abstractions
- reusable organization and readiness helpers
- reusable analytics helpers that are not specific to MSim outputs
- reusable AI tool schemas and domain packages where they benefit multiple apps

### Avoid rebuilding from scratch

- ECS runtime
- graph abstraction
- optimization primitives
- generic persistence infrastructure
- generic AI provider wrappers
- generic realtime or session infrastructure before it is actually needed

## Near-Term Priorities

The next practical sequence for this repo is:

1. use `docs/session_handoff.md` and the latest checkpoint as the restart baseline
2. keep billet-level modeling out until there is a concrete schema and data plan
3. deepen analyst reporting and interpretation on top of the current grouped authorization/fill/readiness model
4. continue scaling and validating synthetic pack-backed scenarios as needed
5. add uncertainty and sensitivity workflows only after the grouped analyst model is fully credible

This sequence keeps the roadmap aligned to the platform vision without pretending billet-level readiness exists before the data model is ready.

## Milestones

- M1: Stable deterministic projection foundation with explicit provenance and a recorded hardening checkpoint
- M2: Reusable manpower domain core established
- M3: Full enlisted-force projection demonstrable
- M4: Sensitivity and optimization workflows available
- M5: Billet and readiness linkage in place
- M6: AI-grounded scenario exploration available
- M7: Officer, warrant, and service generalization proven
- M8: Operational and budget integration demonstrated

## Risks and Watchouts

- allowing app-local manpower logic to calcify instead of extracting it
- over-investing in UI before the force model is credible
- introducing AI workflows before tool grounding and provenance are strong
- coupling too tightly to file-backed persistence and demo fixtures
- trying to generalize across services before proving the USMC architecture

## Decision Guidance

When choosing work, prefer items that improve one of these:

- correctness of manpower semantics
- separation between engine, policy, and data
- portability into shared GamePlanOS packages
- analyst usefulness without creating avoidable infrastructure debt

If a task does not improve one of those, it is probably not on the critical path yet.


