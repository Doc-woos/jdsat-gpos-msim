# Readiness Linkage Diagram

**Date:** 2026-03-26  
**Status:** Working readiness linkage view for MSim

## Purpose

![Readiness Linkage Diagram](readiness_linkage_diagram.svg)

This diagram shows how manpower projections should connect to billet fill, unit manning, readiness, and operational capability questions.

It is a Horizon 2 style view: beyond the current MVP, but directly connected to the roadmap and platform vision. The repo now has a small bridge toward this space: app-local readiness pressure signals plus grouped authorization/fill summaries for pack-backed scenarios, using explicit authorization counts when a pack provides them and falling back to demand only when it does not. The projection summary now also exposes which basis was used so the analyst-facing view stays honest. That is not billet fill yet, but it gives analysts an early view of where readiness pressure concentrates and which communities or force elements are underfilled.

## Readiness Linkage

```mermaid
flowchart LR
    A[Projected Inventory\nby specialty\nby grade\nby year] --> B[Map Inventory to Billets]
    C[Force Structure Demand\nauthorizations\nunit billets\nrequired skills] --> B

    B --> D[Billet Fill Results\nfilled\nunfilled\nmismatched skill or grade]
    D --> E[Unit Manning Picture]

    E --> E1[Critical shortages]
    E --> E2[Leadership gaps]
    E --> E3[Special skill shortages]
    E --> E4[Overages or misalignment]

    E1 --> F[Readiness Assessment]
    E2 --> F
    E3 --> F
    E4 --> F

    G[Training Pipeline Output\nnew qualified personnel\nreclassification throughput] --> E
    H[Retention and Loss Dynamics] --> E
    I[Assignment Policy\nfill priorities\ndeployment sourcing rules] --> E

    F --> J[Capability Effects\nunit can perform\nunit degraded\nunit unavailable\nrisk increased]
    J --> J2[Operational Demand Context\ntheater requirements\nmission assumptions\nforce generation pressure]
    J2 --> K[Decision Support]

    K --> K1[Change accession targets]
    K --> K2[Adjust retention incentives]
    K --> K3[Shift assignment priorities]
    K --> K4[Expand training capacity]
    K --> K5[Accept risk and document tradeoff]
```

## Interpretation

- inventory projection alone is not enough
- readiness emerges when projected people are mapped against actual demand
- shortages matter differently depending on billet criticality, unit type, and skill concentration
- training, assignment policy, retention, and losses all feed the readiness picture
- the value of MSim increases materially when it can explain not just inventory gaps, but readiness consequences
- operational meaning sits downstream of billet fill and readiness, not parallel to them



