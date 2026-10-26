# 2026-10-26: Visible failures (plan 2026-10-26_visible-failures, PRs A+B+C as one PR)

Branch: `mg-genie-build-waves-visible-failures-plan` (from `main` cb8b1c5).

## Problems

From the Semantic Ground Truth build (job 1079028753739581, run 110489694161084, waves 4-0..4-9):

* A run whose wave gate failed ended SUCCESS: no notification, nothing in the run list.
* Sessions that hit the Genie Code step limit or never wrote a final status were reported only as `in_progress` / missing, without the conversation to resume.
* A stopped session left no record of where it stopped.
* A gate check the wave needed (tsc / vitest without Node) could be reported `skipped` and the wave still passed.
* A converge session whose `bundle deploy` was a no-op failed the Genie space freshness check (old `update_time`), and the failure also skipped the probe questions.

## Root causes and decisions

* **Do not raise in the gate.** Jobs runs `run_if: ALL_DONE` tasks whatever the upstream state, including `UPSTREAM_FAILED`. A raising gate would let the next wave's integrator and gate run. Kept the If/else Exclusion cascade and added a final `build_verdict` notebook task (`ALL_DONE`, depends on every `w<w>_gate`) that fails the run. Excluded gates are ignored; a gate task not ending SUCCESS, a missing result file, or a `fail` result fails it.
* Session outcomes come from the Jobs API: the wave's for_each run, each iteration's latest attempt (`iteration #<i>` in the run name maps to `inputs[i].session_id`), and `runs/get-output` (`genie_task_output.conversation_id`, `agent_output.response`). Confirmed on iteration 861320051785964. API errors are warnings; the status-file checks still apply. Step limit after a final `pass` status = complete + warning.
* Runner `progress` (`done`, `next`, `attempt`) is written at milestones only (converge attempt start/end, after each major task) because every write costs steps.
* Required checks are a wave field `required_checks: string[]` (the `gate` list is free text, so a per-check flag does not fit).
* Genie freshness: pass when updated after run start (`fresh`) or the deployed space equals the bundle source after normalisation (`current`). Source from `source_file` or `resource_key` (looked up through `databricks.yml` includes). No source: timestamp rule (`timestamp only: <why>`). Probe questions run when only freshness failed (advisory). Normalisation (join line arrays, merge `metric_views` into `tables`, sort object lists) confirmed on both the Semantic Ground Truth and AgenticTrading spaces. Dashboards not done (normalisation untested).

## Changes

* `src/notebooks/gate_helpers.py` (new): gate result path and `GATE_FAILED` message, `latest_task_states`, `build_verdict`, `verdict_message`, `required_check_problems`, `normalise_genie_space`, `content_diff`, `find_bundle_source`, `locate_genie_source`, `genie_freshness`.
* `src/notebooks/session_status.py`: `session_outcome`, `session_problem`, `iteration_index`, `latest_by_index`.
* `src/notebooks/wave_gate_check.ipynb`: session outcomes from the Jobs API, required checks, Genie freshness by content, probes after freshness-only failures, `GATE_FAILED` message, `wave_<w>_gate_result.json`, `gate_warnings`; docs cell updated. Still never raises.
* `src/notebooks/build_verdict.ipynb` (new): run verdict, `BUILD_FAILED` / `BUILD_PASSED`, `build_verdict.json` in the run's status dir.
* `src/notebooks/waves_manifest.py`: `build_verdict` task (`VERDICT_TASK_KEY`, `make_verdict_task`, `verdict_notebook_path`), `required_checks` and `source_file` validation, warning for a `genie_space` target without a source.
* `src/notebooks/setup_build_waves_job.ipynb`: task-graph comment.
* Skills: runner `progress` object and milestone rule; integrator copies `progress` for error / in_progress sessions and reports `required_checks` by exact name.
* Docs: README (verdict task, failure reading, repair selection incl. `build_verdict`, `only` must include `build_verdict`, retry interval counts from attempt start, PrincipalContext error, commit fixes outside session paths), `docs/manifest-schema.md` (`required_checks`, `source_file`, `resource_key`, freshness rule), `docs/prompts/repair-failed-wave.md`, plan status.
* Tests: `tests/test_gate_helpers.py` (new, 12), `test_session_status.py` (+3), `test_waves_manifest.py` (+9 incl. parametrised, 2 updated counts). 65 pass.

## Checks

* `pytest tests`: 65 passed.
* Code cells of the gate, verdict and setup notebooks parse.
* All example manifests and the AgenticTrading, AgenticTrading app and Semantic Ground Truth manifests validate with no errors and generate `build_verdict` last (depends on 2..11 gates). New warning for AgenticTrading `genie_trade_analysis` and `examples/converge-waves.json` `ops_genie_space` (no `source_file` / `resource_key`).
* Not run end to end: needs a setup rerun and a build run (see rollout).

## Rollout

One PR. The gate notebook changes are backwards compatible (a job without `build_verdict` still works, the run just stays SUCCESS on a failed gate as before). The verdict task and the skill changes need, after merge and with no run left to repair: setup rerun for each instance (setup job 818046072228128 and the other dev instances). Then check: a failing wave ends the run FAILED with `BUILD_FAILED`; a no-op converge deploy passes with `current: content matches source`; the next step-limited session is named with its conversation id.

## Follow-ups

* AgenticTrading `waves.json`: add `resource_key: trade_analysis` (and `bundle_root`) to `genie_trade_analysis`.
* Dashboard half of change 6 once normalisation is tested on a real deployed dashboard.
* Support case for the PrincipalContext retry error (details in the plan).
