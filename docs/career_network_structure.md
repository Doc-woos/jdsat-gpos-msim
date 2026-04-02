# Career Network Structure Diagram

**Date:** 2026-03-26  
**Status:** Working structure view for the MSim career-flow model

## Purpose

![Career Network Structure Diagram](career_network_structure.svg)

This diagram shows the intended shape of the manpower career network that underlies MSim.

It is not a full service-specific topology. It is a structural view of how entry, promotion, lateral movement, convergence, cross-subgraph transitions, and exit should connect in the model.

## Career Network Structure

```mermaid
flowchart LR
    S1[SOURCE\nboot camp\nOCS\nlateral entry] --> E3A[Entry Cell A\n0311 / E3]
    S1 --> E3B[Entry Cell B\n0811 / E3]
    S1 --> E3C[Entry Cell C\n1721 / E3]

    E3A --> E4A[0311 / E4]
    E4A --> E5A[0311 / E5]
    E5A --> E6A[0311 / E6]

    E3B --> E4B[0811 / E4]
    E4B --> E5B[0811 / E5]
    E5B --> E6B[0811 / E6]

    E3C --> E4C[1721 / E4]
    E4C --> E5C[1721 / E5]
    E5C --> E6C[1721 / E6]

    E5A --> LM1[Lateral Move\n03xx to 0369]
    LM1 --> E5D[0369 / E5]
    E5D --> E6D[0369 / E6]

    E6A --> SENIOR[Senior Convergence\n8999 / E8-E9]
    E6B --> SENIOR
    E6C --> SENIOR
    E6D --> SENIOR

    E3A --> LOSS1[Loss Edge]
    E4A --> LOSS2[Loss Edge]
    E5A --> LOSS3[Loss Edge]
    E6A --> LOSS4[Loss Edge]
    E3B --> LOSS5[Loss Edge]
    E4B --> LOSS6[Loss Edge]
    E5B --> LOSS7[Loss Edge]
    E6B --> LOSS8[Loss Edge]
    E3C --> LOSS9[Loss Edge]
    E4C --> LOSS10[Loss Edge]
    E5C --> LOSS11[Loss Edge]
    E6C --> LOSS12[Loss Edge]
    E5D --> LOSS13[Loss Edge]
    E6D --> LOSS14[Loss Edge]
    SENIOR --> LOSS15[Retirement / Loss Edge]

    LOSS1 --> X[SINK / Exit]
    LOSS2 --> X
    LOSS3 --> X
    LOSS4 --> X
    LOSS5 --> X
    LOSS6 --> X
    LOSS7 --> X
    LOSS8 --> X
    LOSS9 --> X
    LOSS10 --> X
    LOSS11 --> X
    LOSS12 --> X
    LOSS13 --> X
    LOSS14 --> X
    LOSS15 --> X

    E3C --> PIPE[Training or Qualification Node]
    PIPE --> E4C

    E5A --> WO[Warrant or Special Program Path]
    WO --> X2[Cross-Subgraph Transition]
```

## Interpretation

### Entry

A source node feeds multiple entry cells. In a full model, these would represent accession channels such as recruit training, commissioning, or lateral entry.

### Vertical Flow

Most career movement is upward through a specialty-specific promotion chain.

### Horizontal Flow

Some cells connect laterally into new specialties, reclassifications, or feeder MOS structures.

### Convergence

Some specialties converge into broader senior leader or staff pathways rather than remaining isolated forever.

### Exit

Every cell can have one or more loss edges leading to exit states. That includes early attrition, steady-state losses, and retirement.

### Optional Intermediate Nodes

Training, qualification, or screening nodes can sit between career cells where the policy model needs them.

### Cross-Subgraph Paths

The full architecture should allow transitions into other subgraphs such as warrant, officer, or special program pathways. This matters because the GamePlanOS MSim vision treats generalization as a topology problem, not an engine rewrite.

## Why This Diagram Matters

This is the structural heart of MSim:

- the graph topology is the service-specific model
- the simulation engine operates on this graph rather than hardcoded career ladders
- policy rules attach to nodes and edges rather than replacing the graph model
- generalization across services should come primarily from new graph topologies and policy sets

## Near-Term Mapping to the Current Repo

The current repo only implements a very small version of this idea:

- career cells
- transitions
- source and sink pseudo-nodes
- graph validation and deterministic flow application

Not yet implemented:

- force-wide topology
- training or qualification nodes
- officer and warrant subgraphs
- explicit convergence patterns at scale
- service-configurable graph loading

