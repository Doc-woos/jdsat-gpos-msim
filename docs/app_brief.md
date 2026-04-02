# MSim App Brief

**Date:** 2026-03-25  
**Status:** MVP seed

## Brief

MSim is a standalone GamePlanOS-based force analytics application for manpower projection and policy analysis. The first slice proves a deterministic, inspectable, testable projection path using `gameplan.graph` and `gameplan.engine` before expanding toward richer force analytics.

## Users

| Role | Need |
|------|------|
| Force planner / manpower analyst | Run a small projection and inspect projected inventory |
| Analyst engineer | Validate flow logic and result contract |

## First Slice

One analyst submits a small scenario to the backend and receives a structured projection result summarizing inventory and metrics for a short horizon.

## Non-Goals

- full ESM parity
- frontend workbench
- realtime or multiplayer
- AI orchestration
- persistence
- organization-level billet modeling

## Success Metrics

- deterministic projection runs end to end
- graph construction is explicit and validated
- result contract is stable and tested
- standalone repo has no monorepo-only imports
