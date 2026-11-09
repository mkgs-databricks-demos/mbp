# 2026-11-09: Build monitor skill

## Problem

The monitor requirements doc named a `genie-build-monitor` skill "to be written". The Devin end-to-end test (`devin-genie-build-waves-test`, plan step 2) needs it before Devin's first monitored run.

## Changes

* `src/skills/genie-build-monitor/SKILL.md` (new, generic, tool-agnostic: Databricks CLI and Git only):
  * Inputs (`job_id`, `run_id`, `build_root`, `manifest_path`, `level` 1-3, `repo`, `build_branch`) and guardrails (identity check, no setup/deploy/settings/permissions/manifest, one repair per wave per run, push only with no active run, never `main`, smallest change).
  * Reading a run: `jobs get-run --include-history` with `--page-token` for builds over 100 tasks, latest attempt per task, task keys per wave including `w<w>_sync`, task outputs and status-directory files with their real field names.
  * Report format, decision table (levels 1-3), repair command (`--no-wait`, `rerun_dependent_tasks`, `latest_repair_id`, the run's `job_parameters`), level 3 fix-and-repair via `w<w>_sync`, code review after `BUILD_PASSED`, polling.
* README: skill listed in the file table (not published to UC; setup publishes only the runner and integrator skills).
* Monitor requirements doc: Instructions section points at the skill.

## Verification

* Field names checked against the code: gate result (`status`, `commit_sha`, `sessions`, `problems`, `warnings`, `gate_warnings`), integrator gate file (`commit_sha`, `stray_files`, `carryover_files`, `requests`), session status fields, `build_verdict` raising its message, sync notebook exit messages.
* CLI flags checked with `--help` on v1.23.0: `jobs get-run --include-history --page-token`, `jobs repair-run --json --no-wait --latest-repair-id`.
* 167 tests pass (no code change).

## Files

`src/skills/genie-build-monitor/SKILL.md`, `README.md`, `docs/plans/2026-11-03_devin-monitor-requirements.md`, `docs/sessions/INDEX.md`.
