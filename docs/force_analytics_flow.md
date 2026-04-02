# Force Analytics Flow

**Date:** 2026-03-26  
**Status:** Working end-to-end force analytics view for MSim

## Purpose

![Force Analytics Flow](force_analytics_flow.svg)

This diagram shows the larger MSim force analytics loop from inputs and policy levers through personnel flow, billet assignment, and decision-support outputs.

It sits above the current deterministic MVP and below the broader platform vision. The intent is to show the force-management problem MSim is growing into, not just the mechanics currently implemented in this repo.

## Force Analytics Flow

```mermaid
flowchart LR
    A[Policy Inputs\naccessions\nretention\npromotion policy\nlateral entry\nincentives] --> Q[MSim Simulation and Analytics Core]
    P[Source Data\ninventory snapshots\nhistorical rates\nforce structure\ntraining data] --> Q
    N[Force Structure Demand\nbillets\nauthorizations\nunit needs] --> Q
    O[Training Pipeline Capacity\nschool seats\nwashout\nthroughput] --> Q

    Q --> B[Entry Sources\nrecruiting\ncommissioning\nlateral entry]
    B --> C[Initial Training and Screening]
    C --> D[Classification and Specialty Assignment]
    D --> E[Inventory by Specialty and Grade]

    E --> I[Promotion Flow]
    E --> J[Retention and Reenlistment]
    E --> K[Lateral Move and Reclassification]
    E --> L[Loss and Separation Processes]

    I --> E2[Future Inventory State]
    J --> E2
    K --> E2
    L --> E2
    E --> E2

    C --> C1[Training Washout]
    C --> C2[Medical or Administrative Separation]
    D --> D1[Reclassification Feedback]
    D --> D2[Post-Training Separation]

    C1 --> L
    C2 --> L
    D1 --> K
    D2 --> L

    E2 --> F[Assignment to Billets and Units]
    F --> G[Deploy and Operate]
    G --> H[Readiness and Capability Outcomes]

    L --> L1[End of Active Service]
    L --> L2[Retirement]
    L --> L3[Involuntary Separation]
    L --> L4[Medical Loss]
    L --> L5[Disciplinary Loss]

    L1 --> M[Exit]
    L2 --> M
    L3 --> M
    L4 --> M
    L5 --> M

    Q --> R[Projected Inventory]
    Q --> S[Projected Gaps and Overages]
    Q --> T[Readiness and Training Risks]
    Q --> U[Policy Comparison\nSensitivity\nOptimization]
```

## Interpretation

- MSim is not only a projection engine. It is the analytical core that connects policy inputs, source data, force demand, and training capacity into future force outcomes.
- Inventory is an intermediate state, not the final answer. The real value appears when projected inventory is mapped to billets, readiness, and capability effects.
- The same force flow should support deterministic projection, comparison, sensitivity analysis, and optimization rather than separate disconnected workflows.
- Training, losses, and reclassification are first-class parts of the force lifecycle, not side calculations.

## Near-Term Mapping to the Current Repo

The current standalone app implements only a subset of this flow:

- scenario inputs and policy tables
- deterministic projection
- baseline-versus-variant comparison
- export and local record saving

Not yet implemented in this repo:

- training pipeline modeling
- billet assignment and readiness linkage
- sensitivity analysis
- optimization workflows
- live or authoritative data adapters

