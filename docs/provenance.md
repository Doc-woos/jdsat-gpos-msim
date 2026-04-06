# Provenance

This repo is seeded from GamePlanOS references, not copied as a monorepo app.

## Reference Sources

- `C:\dev\jdsat-gameplan-os\CLAUDE.md`
- `C:\dev\jdsat-gameplan-os\gameplan\CLAUDE.md`
- `C:\dev\jdsat-gameplan-os\apps\CLAUDE.md`
- `C:\dev\jdsat-gameplan-os\gameplan\guides\app_build_playbook.md`
- `C:\dev\jdsat-gameplan-os\gameplan\guides\app_structure_guide.md`
- `C:\dev\jdsat-gameplan-os\apps\msim\docs\app_brief.md`
- `C:\dev\jdsat-gameplan-os\apps\msim\docs\first_slice.md`
- `C:\dev\jdsat-gameplan-os\apps\msim\docs\09-platform-reuse-plan.md`
- `C:\dev\jdsat-gameplan-os\gameplan\domains\space\__init__.py`
- `C:\dev\jdsat-gameplan-os\gameplan\graph\__init__.py`
- `C:\dev\jdsat-gameplan-os\gameplan\graph\labeled.py`

## Borrowed Patterns

- Standalone app planning packet structure adapted from `apps/msim/docs/*`
- Pure domain package pattern adapted from `gameplan.domains.space`
- Career-flow graph modeled with `gameplan.graph.LabeledGraph`
- Simulation orchestration intentionally composes from `gameplan.engine`
- FastAPI-served thin workbench approach chosen to preserve standalone portability without adopting monorepo frontend tooling
- Analyst workbench visual styling adapted from `C:\dev\RRL Content Automation Engine\app\globals.css`, `C:\dev\RRL Content Automation Engine\app\layout.tsx`, and `C:\dev\RRL Content Automation Engine\app\page.tsx`

## Visual Provenance Notes

- The MSim workbench borrows visual direction only: dark navy gradient background, translucent top bar, cyan accent controls, Segoe UI typography, and glassy dark panel treatment
- No application logic, routing, or product-specific content was copied from the RRL app
- The adaptation was applied only to `backend/web/index.html` and `backend/web/static/styles.css`

## Deliberate Deviations

- No `apps.msim...` imports
- No monorepo folder assumptions
- No copy of GamePlanOS package code into this repo
- No `@gameplan/*` frontend package adoption in the MVP because the first useful UI is a static workbench served directly by FastAPI
- Local pure manpower logic remains app-local until a real `gameplan.domains.manpower` package exists

## Current Provenance Boundary

- Canonical scenario fingerprint, UTC timestamp, filename slugging, and timestamp-token helpers now live in `backend/core/provenance.py`.
- API routes consume provenance helpers; they do not define provenance rules.
- Simulation orchestration consumes the same helpers so run metadata and saved-record metadata are derived from one source of truth.
- Persistence and export adapters now share the same naming helpers, which keeps filenames and saved record paths aligned across JSON records and portable export artifacts.
- Named comparison export and save paths now preserve app-local grouped deltas for pack-backed scenarios, so community and force-element comparison context survives in exported and persisted artifacts.
- Repo-local analyst takeaways now live in `backend/core/summary.py` and are intentionally derived after simulation completes, so explanation wording remains outside any shared neutral manpower package boundary.
- Repo-local watchlists and explanation trails also live in `backend/core/summary.py` and are derived after simulation completes, which keeps ranking and analyst interpretation outside the neutral manpower seam.
- Compact projection and comparison summary CSVs now preserve watchlists, explanations, and takeaways through `backend/core/exporter.py`, which keeps grouped interpretation portable without moving analyst wording into shared algorithms.




