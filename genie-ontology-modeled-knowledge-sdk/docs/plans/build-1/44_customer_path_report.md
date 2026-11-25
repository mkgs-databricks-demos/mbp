# Session 44: Customer Path Run Report & Interventions (R9)

## Scope
Read the finished child build (read-only) and turn it into evidence: the run report, the no-hand-edits diff, and every intervention closed as a documented prerequisite or a build-2 request.

## Context
* P1-6 is done: `.local/build-1.json` has `customer_path_root` (the child project's Git folder) and the child `.build-status` has a `build_verdict.json`.
* Read-only outside `build_root`: never write to the child project. Never copy its workspace-specific values into committed files (refer to it as "the child project").
* Code fixes found here are **requests** for build 2, not edits (this wave owns docs only).

## Tasks
1. Read the child verdict, gate files, session summaries and the intervention log the owner/Devin kept in `docs/customer-path/run_plan.md` (or the child's own log).
2. Diff the child's `docs/plans/` and `waves.json` against a fresh `/tmp` scaffold of the child's `sdk_config.json`; only rendered tokens may differ.
3. `docs/customer-path/run_report.md`: verdict, waves and outcomes, tuning curve and asymptote result, report-simulation score (if the child got that far), the diff result, and the intervention log with a closing link per entry.
4. Each intervention: a documented prerequisite (edit `docs/usage.md` or `templates/run/README.md`) or a request in `docs/plans/build-2/REQUESTS.md` (same format as build-1 REQUESTS: problem, evidence, change, files, acceptance criteria).

## Acceptance Criteria
- [ ] Gate checks `customer_path_verdict`, `no_hand_edits`, `interventions_closed` pass.

## Owned Paths
- `docs/customer-path/**`, `docs/usage.md`, `templates/run/README.md`, `docs/plans/build-2/**`

## Dependencies
- Session 43 and owner prerequisite P1-6.
