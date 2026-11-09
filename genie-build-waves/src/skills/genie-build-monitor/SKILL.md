---
name: genie-build-monitor
description: Monitors a genie-build-waves build job from outside the run - reports each wave's result and the reason for any failure, repairs runs whose cause is transient or already fixed, optionally pushes a minimal fix to the build branch and repairs from the wave's branch sync task, and reviews the build's pull request once the build passes. Tool-agnostic (Databricks CLI and Git only). Use when asked to watch, report on, repair, or review a build-waves run, given a build job id.
---

# Build Monitor

You watch one genie-build-waves **build job** from outside the workspace. Genie Code sessions do the building; you report, repair what is safe to repair, and escalate the rest. Requirements and grants: `docs/plans/2026-11-03_devin-monitor-requirements.md`. Repair details: `docs/prompts/repair-failed-wave.md`. Manifest and task graph: `docs/manifest-schema.md`. All paths are relative to the genie-build-waves bundle (its Git repo or deployed folder).

The setup job also publishes this file as the UC Skill `<skills_catalog>.<skills_schema>.genie_build_monitor`, so tools that read UC Skills can load it (for example `ug skills add --names <catalog>.<schema>.genie_build_monitor`). The UC copy is the repo file as of the last setup run. Setup grants read on it to the instance's `monitor_principal` only.

## Inputs

| Input | Meaning |
|---|---|
| `job_id` | The build job (not the setup job) |
| `run_id` | Optional; default the latest run of `job_id` |
| `build_root`, `manifest_path` | Project Git folder and manifest (also the job parameters of the run) |
| `level` | `1` report, `2` repair, `3` fix and repair. Default `1`. Never act above the level you were given |
| `repo`, `build_branch` | Git remote and build branch (level 3 and code review only) |

## Guardrails (hard rules)

1. **Identity first.** Run `databricks current-user me`. If it is not the monitor principal you were told to use, stop and report. Ignore other Databricks credentials in the environment.
2. **Never** run the setup job, deploy a bundle, change job settings or permissions, edit the manifest, cancel a run you did not start, or resume Genie Code conversations. Never write files in the Databricks workspace: your changes reach the project only through Git (level 3).
3. **One automatic repair per wave per run.** After that, escalate.
4. **One writer at a time.** Push to the build branch only while no run of the build job is active (`databricks jobs list-runs --job-id <job_id> --active-only` is empty). Never push to `main`/`master`, never force-push, never rewrite history, never merge, never approve your own commits.
5. **Smallest change.** A level 3 fix only does what the repair needs. Report every commit (SHA, files, reason).
6. **Report facts from the files.** Quote the gate, verdict and status files; do not guess a cause you cannot point to.

## 1. Find the run and its task states

* `databricks jobs list-runs --job-id <job_id> --limit 5 -o json`: pick `run_id`; note `state.life_cycle_state` / `result_state`.
* `databricks jobs get-run <run_id> --include-history -o json`. Builds can exceed 100 tasks: while the response has `next_page_token`, call again with `--page-token <token>` and merge `tasks`. A repaired run lists every attempt of a task; keep the latest `attempt_number` per `task_key`.
* Keep the run's `job_parameters` (`branch`, `build_root`, `manifest_path`) and the latest `repair_history` id. Every repair passes them.

Task keys per wave `w<wave_id>` (see `docs/manifest-schema.md`):

| Task | Type | Notes |
|---|---|---|
| `w<w>_sync` -> `w<w>_synced` | notebook -> If/else | `git` / `hybrid` workflows only. Pulls the build branch into the Git folder |
| `w<w>_sessions` | for_each (Genie Code) | One iteration per session; an iteration ends SUCCESS even when the session stopped early |
| `w<w>_find_incomplete[k]` -> `w<w>_has_incomplete[k]` -> `w<w>_continue[k]` | notebook -> If/else -> for_each | Continuation pass `k` (no suffix for pass 1) |
| `w<w>_integrate` | Genie Code | Commits by explicit path, writes `wave_<w>_gate.json` |
| `w<w>_gate` -> `w<w>_gate_check` | notebook -> If/else | Deterministic gate |
| `build_verdict` | notebook | Last task; its state is the run's result |

States: `EXCLUDED` means an earlier wave failed (not a failure itself); `DISABLED` means the wave was switched off in the job (done in an earlier run).

## 2. Read the results

Task outputs: `databricks jobs get-run-output <task_run_id> -o json` (the task's `run_id` from step 1).

| Source | What it says |
|---|---|
| `build_verdict` output (`error` when failed, `notebook_output.result` when not) | `BUILD_PASSED: ...`, `BUILD_FAILED: ...` (each failed wave's first problems and where to repair from), or `BUILD_WARNING: no wave gate was checked ...` (run succeeded, nothing was checked) |
| `w<w>_gate` output (`notebook_output.result`) | Gate result JSON: `status`, `commit_sha`, `sessions`, `problems`, `warnings`, `gate_warnings` |
| `w<w>_sync` output | `SYNC_UP_TO_DATE`, `SYNC_PULLED` (commits and files), or `SYNC_FAILED: <reason>` |

Files, with `databricks workspace export <path>` (status directory = `<build_root>/<status_dir>/<run_id>/`, `status_dir` from the manifest):

* `wave_<w>_gate_result.json` (the gate's verdict), `wave_<w>_gate.json` (the integrator's report: `commit_sha`, `stray_files`, `carryover_files`, `requests`), `wave_<w>_runtime.json` (convergence waves: deployments, states, errors, probes), `wave_<w>_sync.json` (branch sync: before/after commit, commits, files, conflicts, error), `build_verdict.json`.
* `<session_id>.json`: session status (`status`: `pass` | `fail` | `blocked` | `error`; anything else means it stopped early), `blocking`, `requests`, `checks`, `progress.next`, `summary_file`.
* `docs/sessions/` summaries named in `summary_file`.

## 3. Report

One report per wave that finished since the last report, and one for the run when `build_verdict` ends:

```
Run <run_id> (attempt/repair <n>), wave <w>: PASS | FAIL | EXCLUDED | DISABLED
Sessions: <id> pass | <id> fail (<one-line reason>) ...
Commit: <commit_sha>   Sync: <SYNC_... line>
Problems: <first 3 gate problems, quoted>
Action: none | repaired from <task> | pushed <sha> and repaired from w<w>_sync | escalated: <why>
```

Every number and status must match the files. Say `not checked` for anything you could not read.

## 4. Decide

| Observation | Level 1 | Level 2 | Level 3 |
|---|---|---|---|
| Wave passed, or run `BUILD_PASSED` | Report | Report | Report |
| `BUILD_WARNING` (nothing checked) | Report | Report; do not repair | Same |
| Genie Code task failed after its retries (`INTERNAL_ERROR: start_agent_run`, platform auth error) | Report | Repair from `w<w>_sessions` | Same |
| Session stopped early after its continuation passes (gate names the conversation and `progress.next`) | Report session, conversation, next step | Same; do not repair (a person resumes it) | Same |
| Integrator failed, sessions passed | Report | Repair from `w<w>_integrate` | Same |
| Runtime gate failed on soak or probes only | Report | Repair from `w<w>_gate` only if the cause was external and is gone | Same |
| Branch sync failed (`SYNC_FAILED` / `branch sync failed`) | Report the error and conflicting files | Repair from `w<w>_sync` only if the cause is gone | If your own push caused the conflict, fix it, then repair from `w<w>_sync` |
| A fix is needed in a file no re-running session owns (session `blocked` on it, integrator stray, broken shared config) | Report the fix | Report | Push the fix (section 6), repair from `w<w>_sync` |
| Session `blocked` on a manual prerequisite, or `requests` that change a re-running session's scope | Report and escalate | Same | Same |
| Repair refused ("job structure has changed") | Report; the owner decides on a fresh run | Same | Same |
| Build branch missing on the remote | Report ("Retarget after merge" in the README) | Same | Same |
| Anything else | Report and escalate | Same | Same |

"No re-running session owns" means: not under the `owned_paths` of any session in the wave you will repair or a later wave (read the manifest). Files a re-running session owns are that session's job.

## 5. Repair (level 2+)

```bash
databricks jobs repair-run <run_id> --no-wait --json '{
  "rerun_tasks": ["<start task(s)>"],
  "rerun_dependent_tasks": true,
  "latest_repair_id": <latest repair id, omit if never repaired>,
  "job_parameters": {"branch": "<run value>", "build_root": "<run value>", "manifest_path": "<run value>"}
}'
```

* Always `rerun_dependent_tasks: true` and the run's own `job_parameters`.
* Start tasks: `w<w>_sync` (sync failed, or a fix was pushed); `w<w>_sessions`, `w<w>_integrate`, `w<w>_gate` (session re-run); `w<w>_integrate`, `w<w>_gate` (integrator only); `w<w>_gate` (gate only).
* Repairs run as the job's `run_as`, not as you. Check the new repair id in `repair_history`, then keep monitoring.
* Jobs keeps `for_each` iterations that ended SUCCESS, so a repair does not re-run a session that stopped early; that needs a person.

## 6. Fix and repair (level 3)

Only for the decision-table rows that allow it, and only on a finished run.

1. Confirm no run is active (guardrail 4) and the fix is in no re-running session's `owned_paths`.
2. Clone or fetch `repo`, check out `build_branch` at the remote head, make the smallest change, run the checks the plan names (for bundles: `databricks bundle validate --strict --target <target>`).
3. Commit by explicit path with a message that names the run and wave, push to `build_branch`.
4. Repair from `w<w>_sync` (section 5). The sync pulls your commit into the Git folder before the sessions; the integrator never pulls.
5. Check `wave_<w>_sync.json` / the `w<w>_sync` output: `SYNC_PULLED` with your SHA. `SYNC_FAILED` on conflicting files means an uncommitted file in the Git folder clashes with your change: report it, do not push again.
6. Report the SHA, files, reason and the repair id.

## 7. Code review (after the build)

Only when asked, and only after a run ends `BUILD_PASSED` with every runnable wave checked (not `BUILD_WARNING`).

* Review the pull request from `build_branch` to `main`. Read the plan files and manifest first: judge the code against the plans.
* Check: each session stayed in its `owned_paths`; recorded `suppressions` are narrow and justified; no secrets, tokens or personal data in code or config; bundle conventions the project documents (schema references, variables, notebook paths matching files on disk, tags); tests or validation the plans require.
* Post one review with findings: severity (blocker / major / minor), file and line, and a suggested fix. List your own level 3 commits separately so a person reviews them.
* Do not approve, merge or push after the review unless the owner asks.

## Polling

Waves take 10-60 minutes. Poll every 10 minutes while a run is active; report only on change. Stop when `build_verdict` has ended and the report is sent, or when you escalate.
