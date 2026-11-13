# 2026-11-09: Build monitor skill

## Problem

The monitor requirements doc named a `genie-build-monitor` skill "to be written". The Devin end-to-end test (`devin-genie-build-waves-test`, plan step 2) needs it before Devin's first monitored run.

## Changes

* `src/skills/genie-build-monitor/SKILL.md` (new, generic, tool-agnostic: Databricks CLI and Git only):
  * Inputs (`job_id`, `run_id`, `build_root`, `manifest_path`, `level` 1-3, `repo`, `build_branch`) and guardrails (identity check, no setup/deploy/settings/permissions/manifest, one repair per wave per run, push only with no active run, never `main`, smallest change).
  * Reading a run: `jobs get-run --include-history` with `--page-token` for builds over 100 tasks, latest attempt per task, task keys per wave including `w<w>_sync`, task outputs and status-directory files with their real field names.
  * Report format, decision table (levels 1-3), repair command (`--no-wait`, `rerun_dependent_tasks`, `latest_repair_id`, the run's `job_parameters`), level 3 fix-and-repair via `w<w>_sync`, code review after `BUILD_PASSED`, polling.
* README: skill listed in the file table.
* UC publishing (owner request: same job that publishes the other skills): setup notebook gets a `monitor_skill_id` widget (default `genie_build_monitor`, empty skips) and a `ROLE_DIRS` map; the monitor joins `SKILLS`, so the existing create / upload / finalize loop publishes it to `<skills_catalog>.<skills_schema>.genie_build_monitor`. No automation uses it (automations name their skill keys explicitly). New bundle variable `monitor_skill_id` passed by `setup_build_waves.job.yml`; README variables line and `manifest-schema.md` Skills object updated; the skill names its UC id.
* Monitor requirements doc: Instructions section points at the skill.

## Verification

* Field names checked against the code: gate result (`status`, `commit_sha`, `sessions`, `problems`, `warnings`, `gate_warnings`), integrator gate file (`commit_sha`, `stray_files`, `carryover_files`, `requests`), session status fields, `build_verdict` raising its message, sync notebook exit messages.
* CLI flags checked with `--help` on v1.23.0: `jobs get-run --include-history --page-token`, `jobs repair-run --json --no-wait --latest-repair-id`.
* 167 tests pass; `bundle validate --strict --target dev` OK with the new variable.
* Not run: the setup job with the monitor skill (first run: the `devin-genie-build-waves-test` instance setup). A manual publish was not done; the owner wants it published only by setup.

## Files

`src/skills/genie-build-monitor/SKILL.md`, `src/notebooks/setup_build_waves_job.ipynb`, `resources/setup_build_waves.job.yml`, `databricks.yml`, `README.md`, `docs/manifest-schema.md`, `docs/plans/2026-11-03_devin-monitor-requirements.md`, `docs/sessions/INDEX.md`.
