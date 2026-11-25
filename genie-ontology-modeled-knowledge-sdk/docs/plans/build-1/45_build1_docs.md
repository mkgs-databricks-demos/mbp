# Session 45: Build-1 Documentation & Observations

## Scope
Bring the project docs up to date with build 1 and consolidate the build-1 observations for build 2.

## Context
* Inputs: every build-1 session summary (`docs/sessions/2026-*_w1-*`), `examples/tpch/docs/tuning/tuning_summary.md`, `examples/tpch/docs/evaluation/report_simulation_results.md`, `docs/customer-path/run_report.md`, `docs/plans/build-2/REQUESTS.md`.
* mbp is customer-facing: no workspace hosts, user paths, resolved schema names, domain ids or space ids outside `docs/sessions/`. One exception agreed in plan 30: `examples/tpch/docs/registration/resolved_target.json`.

## Tasks
1. `docs/build-1-observations.md`: one row per skill gap, template fix or platform limit reported in sessions 18-44 (source session, observation, type, proposed build-2 change), plus owner/process items and the report-simulation backlog item if the score was below 80%.
2. `README.md`: install from the wheel, guided notebook, published skills, exhaustive tuning, report simulation; status.
3. `PROJECT_MEMORY.md`: status = build-1 complete (or where it stopped), decisions made during the build, next steps.
4. `CHANGELOG.md`: 0.1.0 entry complete.
5. L100 build-status section; `examples/tpch/README.md` (tuning and evaluation folders).

## Acceptance Criteria
- [ ] Gate checks `link_check` and `observations` pass; the identifier grep finds nothing (except the agreed file).

## Owned Paths
- `README.md`, `PROJECT_MEMORY.md`, `CHANGELOG.md`, `docs/build-1-observations.md`, `docs/design/L100-genie-ontology-modeled-knowledge-sdk.md`, `examples/tpch/README.md`

## Dependencies
- Session 44.
