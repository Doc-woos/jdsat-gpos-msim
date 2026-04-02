# Simulation Policy Data Separation Diagram

**Date:** 2026-03-26  
**Status:** Working architecture boundary view for MSim

## Purpose

![Simulation Policy Data Separation Diagram](simulation_policy_data_separation.svg)

This diagram shows the separation MSim should maintain between data inputs, service-specific policy, the career-network model, and the execution engine.

It is also the clearest package-boundary visual for this repo: use GamePlanOS packages for shared substrate concerns, keep manpower-specific domain logic portable, and keep app orchestration and product outputs local to MSim.

## Separation Diagram

```mermaid
flowchart TD
    A[Authoritative or Scenario Data\ninventory\nauthorizations\nhistorical rates\ntraining capacity\npolicy inputs] --> B[Data Normalization Layer]

    B --> C[Service Policy Layer\nUSMC-specific rules\npromotion logic\nretention assumptions\nloss categories\naccession policy]
    B --> D[Career Network Configuration\nnodes\nedges\ntransition topology\nentry and exit structure]
    B --> E[Scenario Assembly\nhorizon\nresolution\ndeterministic vs stochastic\ncomparison setup]

    C --> F[MSim Domain Logic\nportable manpower algorithms\npolicy application\nflow calculations]
    D --> F
    E --> F

    F --> G[Simulation Runtime\ngameplan.engine\nexecution orchestration\nstate updates]
    F --> H[Graph Analysis\ngameplan.graph\nvalidation\nreachability\nbottlenecks]
    F --> I[Analytics Layer\ngameplan.analytics\nsensitivity\noptimization\nstatistics]
    B --> L[Data and Persistence Layer\ngameplan.data or repo-local adapters]

    G --> J[Result Aggregation]
    H --> J
    I --> J
    L --> J

    J --> K[Product Outputs\nrepo-local APIs\nprojections\ncomparisons\nreadiness summaries\nexports\nAI-grounded explanations]
```

## Interpretation

- Data should be normalized before it touches policy or simulation code.
- Service-specific behavior should live in policy and graph configuration, not in the engine.
- The career graph expresses structural pathways.
- The domain logic applies policy to those pathways.
- `gameplan.engine`, `gameplan.graph`, and `gameplan.analytics` should remain reusable substrate concerns rather than becoming app-specific logic hosts.
- Persistence is a separate adapter boundary, whether this repo remains file-backed for now or later migrates toward `gameplan.data`.
- Product outputs should depend on stable internal boundaries rather than direct coupling to raw data shapes.

