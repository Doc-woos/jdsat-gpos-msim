# Analyst Workflow Diagram

**Date:** 2026-03-26  
**Status:** Working analyst workflow view for MSim

## Purpose

![Analyst Workflow Diagram](analyst_workflow_diagram.svg)

This document visualizes the intended analyst workflow for MSim at a detailed but product-oriented level.

It reflects the larger platform direction described in the MSim vision while staying compatible with the current standalone app structure. It is a target-state workflow, not a claim that every branch is already implemented in this repo.

## Analyst Workflow

```mermaid
flowchart TD
    A[Analyst Starts Question\nWhat force outcome or policy issue\nneeds to be understood?] --> B[Choose Analysis Mode\nBaseline projection\nPolicy comparison\nReadiness analysis\nOptimization question\nWhat-if exploration]

    B --> C[Assemble Scenario Inputs]

    C --> C1[Load baseline force structure\nauthorizations\nbillets\ndemand targets]
    C --> C2[Load workforce state\ninventory by specialty and grade\nhistorical rates\ncurrent assumptions]
    C --> C3[Load policy package\npromotion rules\nretention assumptions\naccessions\nlateral entry\nincentives]
    C --> C4[Choose time horizon and resolution\nannual or monthly\ndeterministic or stochastic]

    C1 --> D[Validate and Normalize Scenario]
    C2 --> D
    C3 --> D
    C4 --> D

    D --> D1{Scenario valid?}
    D1 -->|No| D2[Return validation issues\nmissing references\ninvalid policy windows\nconflicting assumptions]
    D2 --> C
    D1 -->|Yes| E[Build Career Network]

    E --> E1[Construct graph nodes\nspecialty-grade career cells\ntraining nodes\nentry and exit nodes]
    E --> E2[Construct graph edges\npromotion\nlateral move\nretention\nloss\naccession\ntraining transitions]
    E --> E3[Run graph checks\nmissing paths\ninvalid topology\ncycles where prohibited\nbottlenecks]

    E1 --> F[Prepare Simulation Context]
    E2 --> F
    E3 --> F

    F --> F1[Attach policy tables and overrides]
    F --> F2[Attach force structure demand and billet context]
    F --> F3[Attach training capacity assumptions]
    F --> F4[Select execution scale\ncurrent repo: deterministic cohort-style flow\nfuture: Monte Carlo\nfuture: agent simulation\nfuture: optimization model]

    F1 --> G[Execute Analysis]
    F2 --> G
    F3 --> G
    F4 --> G

    G --> G1[Run deterministic projection]
    G --> G2[Run comparison\nbaseline vs variant]
    G --> G3[Run Monte Carlo\nif uncertainty needed]
    G --> G4[Run sensitivity analysis\nif lever prioritization needed]
    G --> G5[Run optimization\nif target outcome and constraints are defined]

    G1 --> H[Aggregate Outputs]
    G2 --> H
    G3 --> H
    G4 --> H
    G5 --> H

    H --> H1[Inventory outputs\nby specialty\nby grade\nby year]
    H --> H2[Gap outputs\ninventory vs demand\ninventory vs authorization]
    H --> H3[Flow outputs\naccessions\npromotions\nlosses\nlateral moves\ntraining throughput]
    H --> H4[Risk outputs\nshortages\nbottlenecks\nreadiness impacts\ncapability concerns]
    H --> H5[Decision outputs\npolicy deltas\nsensitivity ranking\noptimization recommendations]

    H1 --> I[Analyst Review Layer]
    H2 --> I
    H3 --> I
    H4 --> I
    H5 --> I

    I --> I1[Inspect dashboards and tables]
    I --> I2[Inspect comparison narratives\nrule changes\npolicy deltas\nkey drivers]
    I --> I3[Inspect uncertainty bands\nand confidence limits]
    I --> I4[Inspect readiness and billet effects]
    I --> I5[Optionally ask AI-guided what-if questions\nagainst grounded simulation tools]

    I1 --> J{Enough confidence to brief\nor decide?}
    I2 --> J
    I3 --> J
    I4 --> J
    I5 --> J

    J -->|No| K[Refine assumptions or scenario]
    K --> C

    J -->|Yes| L[Produce Decision Artifact]

    L --> L1[Export run or comparison artifacts]
    L --> L2[Save scenario and results\nwith provenance metadata]
    L --> L3[Prepare analyst summary\nforce outcome\npolicy tradeoffs\nrisks\nrecommendation]

    L1 --> M[Decision Support Output]
    L2 --> M
    L3 --> M

    M --> M1[Planner review]
    M --> M2[Leadership brief]
    M --> M3[Further policy iteration]
    M --> M4[Input to readiness\ntraining\nor operational analysis]
```

## Workflow Layers

### 1. Question Framing

The analyst begins with a force-management question, not a technical input format. MSim should support questions such as:

- what does the force look like in five years under current policy
- what happens if cyber accessions increase while end strength remains fixed
- where do shortages appear if retention falls in a target community
- what policy lever matters most for a readiness outcome

### 2. Scenario Assembly

This layer combines:

- inventory state
- force structure demand
- policy assumptions
- timeframe and execution mode

In the current app, this is still mostly a scenario payload plus local fixture loading. In the larger platform, it expands into richer data adapters and reusable scenario artifacts.

### 3. Network and Simulation Preparation

The central modeling move is to build a career-flow network and attach policy and demand context to it. This is where generic simulation mechanics and service-specific policy begin to separate.

### 4. Execution

Different analyst questions should route to different execution modes:

- deterministic projection for baseline force outlook
- comparison mode for policy deltas
- Monte Carlo for uncertainty
- sensitivity for lever ranking
- optimization for constrained planning problems

In this repo today, only deterministic projection and baseline-versus-variant comparison are implemented directly.

### 5. Review and Iteration

MSim should support an iterative loop rather than a one-shot run. The analyst reviews outputs, identifies weak assumptions or unacceptable risks, adjusts the scenario, and runs again.

### 6. Decision Artifacts

The end product is not only a chart. It is a reusable, auditable analytical artifact with:

- scenario definition
- provenance metadata
- result outputs
- comparison drivers
- optionally a recommendation or policy tradeoff summary

## Near-Term Mapping to the Current Repo

The current standalone app only implements a subset of this workflow:

- scenario assembly via inline payloads or named fixtures
- validation through Pydantic models
- career graph construction
- deterministic execution
- baseline-versus-variant comparison
- export and local record saving
- thin workbench for basic analyst interaction

Not yet implemented in this repo:

- force-structure and billet linkage
- training pipeline modeling
- Monte Carlo and sensitivity workflows
- optimization workflows
- AI-guided what-if exploration
- readiness and capability integration

## Suggested Next Visuals

Useful follow-on diagrams would be:

- career network structure diagram
- data architecture diagram
- simulation engine versus policy layer separation diagram
- readiness linkage diagram
- AI-assisted scenario exploration workflow

