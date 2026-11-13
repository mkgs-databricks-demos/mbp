# Plan: continuation pass for sessions that stop before finishing

Status: **implemented 2026-11-03, not yet run with real Genie Code sessions.** Branch `mg-genie-build-waves-continuation` (from `main`). Adds tasks to every wave, so it needs a setup rerun per instance after merge (see Rollout).

Implementation notes (where it differs from or adds to the plan below):

* **Chaining.** Jobs Excludes a task when all of its dependencies are Excluded. So pass k+1's `find_incomplete` depends on pass k's `find_incomplete` (never Excluded) and `continue`, both ALL_DONE, and the integrator depends on the last pass's `find_incomplete` and `continue`. Pass 1 keys have no suffix; later passes add the number (`w4-1_find_incomplete2`).
* **Gate mapping.** The run's `for_each_task.inputs` for a continue task shows the unresolved `{{tasks...values.incomplete}}` reference, not the list, and iteration runs do not show resolved `{{input.*}}` parameters either. The gate reads the list from the find task's task value and maps iteration index to session id (`session_status.map_iterations`). Iterations that started before the latest find attempt (kept by a repair) are not matched, the latest attempt that was not Excluded is used, and the pass count comes from the run's task keys (`passes_in_run`), not the live manifest. Each of these cases is a gate warning.
* **One completion rule.** `session_outcome` is shared by the find task and the gate: only `pass`, `fail`, `blocked`, `error` are final; unreadable files (bad JSON or not an object) and any other status are continued.
* **Runner parameters.** `RUNNER_PARAMS` / `INTEGRATOR_PARAMS` live in `waves_manifest.py`; first-run sessions get `continuation: "0"`, and a test checks the generated parameters equal the prompt placeholders. The runner keeps an existing status file (retry or continuation) and records each converge attempt when it ends; a cut-off attempt is recorded as `interrupted` and counts toward `max_attempts`.
* **Limits.** Wave-level `continuation_passes` overrides the top level. `validate_manifest` fails when the job would exceed 1,000 tasks.
* **Repair.** Not changed to start from `w<w>_find_incomplete`: Jobs keeps `for_each` iterations that ended SUCCESS on repair, so a repair cannot be relied on to re-run a continuation. The docs keep resume-by-hand plus repair from `w<w>_integrate` for a session that stops again.
* **Smoke (fake sessions).** A one-time `runs/submit` of the generated graph with notebook stand-ins for the Genie Code tasks (2 waves, `continuation_passes: 2`; one session `in_progress` until continuation 2) ended SUCCESS: both continue passes ran for that session only, the second wave's continue tasks were Excluded and its integrator still ran, and the gate reported the session complete at continuation 2 with the continuation iteration's run id. A second smoke after the review fixes added a session with status `running` (continued once, then complete) and a wave with `continuation_passes: 0` (no continue tasks), and ended SUCCESS. Not covered: real Genie Code sessions resuming from `progress.next`.

## Problem

A Genie Code session that runs out of steps still ends its `for_each` iteration SUCCESS. Its status file stays `in_progress` (or was never written), the integrator credits its partial files, and the gate fails the wave. Recovery today is manual:

1. Read the gate problem (`session_problem` names the session, conversation and `progress.next`).
2. Resume the conversation in Genie Code until the session writes its final status.
3. Repair the run from `w<wave>_integrate`.

Repairing `w<wave>_sessions` does not help: Jobs does not re-run an iteration that already ended SUCCESS, so the parent finishes in about a second and the gate fails again.

The runner can already resume. It writes a provisional `in_progress` status with `progress.next` before any work, and a session that finds its own status file for the same `run_id` treats itself as a retry and continues from where the earlier attempt stopped. Nothing starts that second attempt automatically.

## Goal

Each wave re-runs, once and automatically, only the sessions that did not finish, before the integrator runs. Sessions that finished (any final status, including `blocked` and `fail`) are never re-run. No clock checks, no external service, and it works the same for every build-waves user.

## Design

### Task graph (per runnable wave)

Today: `w<w>_sessions` -> `w<w>_integrate` -> `w<w>_gate` -> `w<w>_gate_check`.

New, between sessions and integrate:

| Task key | Type | Depends on | Does |
|---|---|---|---|
| `w<w>_find_incomplete` | notebook, `run_if: ALL_DONE` | `w<w>_sessions` | Reads `<status_dir>/<run_id>/<session_id>.json` for every session in the wave. Sets task values `incomplete` (JSON list of `{session_id, title}`, the same shape as the `w<w>_sessions` inputs) and `has_incomplete` (`"true"` / `"false"`). |
| `w<w>_has_incomplete` | condition task | `w<w>_find_incomplete` | `{{tasks.<find_incomplete>.values.has_incomplete}} == "true"`. |
| `w<w>_continue` | `for_each` | `w<w>_has_incomplete` (outcome `true`) | Inputs `{{tasks.<find_incomplete>.values.incomplete}}`. Inner task `w<w>_continue_session`: the same runner configuration and parameters as `w<w>_session`, plus `continuation=1`. Same concurrency rule and timeout as the sessions task. |

`w<w>_integrate` then depends on `w<w>_continue` and `w<w>_find_incomplete`, still `run_if: ALL_DONE`. When nothing is incomplete, `w<w>_continue` is Excluded and uses no compute; Excluded counts as done for `ALL_DONE` (the same rule `build_verdict` relies on).

`for_each` inputs may be a task-value reference (up to 48 KB resolved), so the list can be built at run time: [For each task](https://docs.databricks.com/aws/en/jobs/tasks/for-each/). Task-value references to keys with `-` must be backtick-escaped: use `ref_ident()`.

### Which sessions are incomplete

Use the existing `session_outcome(response, status)` from `src/notebooks/session_status.py` with `response=None` (the decision only needs the status file):

* `missing` (no status file) or `in_progress` -> continue.
* `complete` (any final status: `pass`, `fail`, `blocked`, `error`) -> do not continue. `blocked` needs a person; `fail` and `error` are real results.
* Sessions in archived waves are never listed (they generate no tasks today).

Keep the selection logic in a pure helper (e.g. `incomplete_sessions(wave_cfg, status_dir_for_run)`) so it is unit-tested like the other gate helpers. The notebook only reads files, calls the helper and sets the task values.

### Manifest

* New optional top-level and wave-level `continuation_passes` (integer, default `1`, `0` disables, maximum `3`). Wave-level overrides top-level.
* `0` generates exactly today's graph (no new tasks), so a manifest can opt out.
* Passes above 1 chain the three tasks again (`w<w>_find_incomplete2`, `w<w>_has_incomplete2`, `w<w>_continue2`, ...), each reading the previous pass's results. The integrator depends on the last pass.
* Validation: non-negative integer, at most 3; error otherwise.

### Runner skill (`src/skills/genie-build-session-runner/SKILL.md`)

* Add `continuation` to the inputs table (optional; `0` or empty = first attempt).
* Under "Task retries", state that `continuation >= 1` means the same thing as a retry, explicitly: read the status file and summary for this `run_id`, keep finished work, start from `progress.next`, and never start over or redo `progress.done` steps.
* Converge sessions: attempts already recorded count toward `max_attempts`; continue numbering from the last attempt.
* No change to how often the runner writes `progress` (milestones only).

### Gate and integrator

* The gate already fails on `in_progress` / missing status files, so a session that is still incomplete after the last pass fails the wave exactly as today.
* The gate reads iteration outputs (conversation id, step-limit text) from `w<w>_sessions`. Extend it to also read `w<w>_continue` (and later passes) and use the **latest** iteration per session, so the problem text names the continuation's conversation, not the first one.
* `session_problem` text: when a continuation also stopped, say so ("stopped again after a continuation pass") and keep the existing next-step advice (resume, then repair from `w<w>_integrate`).
* Integrator: no logic change. Its session table can note which sessions were continued (read from the `incomplete` task value or the status file's attempt history).
* `build_verdict`: unchanged (it only looks at `_gate` task keys).

### Repair

The continuation pass also fixes the repair gotcha. After fixing a cause, repair from `w<w>_find_incomplete` (with `rerun_dependent_tasks=True` and the original `job_parameters`): any session whose status is still incomplete runs again, while finished sessions are left alone. Update `docs/prompts/repair-failed-wave.md`:

| What failed | `rerun_tasks` |
|---|---|
| A session stopped before finishing | `w<w>_find_incomplete` (continuation runs, then integrate and gate) |
| A session's code, plan or manifest was fixed | `w<w>_sessions` and onward, as today |

Resuming the conversation by hand stays documented as the fallback when `continuation_passes` is `0` or every pass ran out.

## Code changes

* `src/notebooks/waves_manifest.py`: `generate_wave_tasks` adds the tasks above; `validate_manifest` checks `continuation_passes`; `manifest_summary` can mention the pass count.
* `src/notebooks/session_status.py`: `incomplete_sessions(...)` helper.
* New notebook `src/notebooks/find_incomplete_sessions.ipynb` (verify the extension on disk before referencing it, and keep it consistent with `wave_gate_check.ipynb`).
* `src/notebooks/wave_gate_check.ipynb`: read continuation iterations; latest iteration per session wins.
* `src/notebooks/setup_build_waves_job.ipynb`: pass the new notebook path to `generate_wave_tasks` (same pattern as the gate and verdict paths).
* `src/skills/genie-build-session-runner/SKILL.md`: `continuation` input and resume rule.
* Docs: README (four-phase pattern becomes "sessions, continuation, integrator, gate, gate check"), `docs/manifest-schema.md`, `docs/prompts/repair-failed-wave.md`, `examples/*.json` (no change needed; default 1 applies).

## Tests

* `tests/test_waves_manifest.py`:
  * default manifest: each wave has the three new tasks; integrate depends on `w<w>_continue` with `ALL_DONE`; `w<w>_continue` depends on the condition with outcome `true`; inputs reference the find task's value with `ref_ident` escaping for keys like `w4-1_find_incomplete`;
  * `continuation_passes: 0`: graph identical to today's (backwards compatibility);
  * `continuation_passes: 2`: two chained passes, integrate depends on the second;
  * deploying waves keep concurrency 1 in the continuation `for_each`;
  * archived waves still generate nothing;
  * validation rejects negative, non-integer and values above 3.
* `tests/test_session_status.py`: `incomplete_sessions` for missing, `in_progress`, `pass`, `blocked`, `fail`, `error`, and malformed files.
* Existing `examples/` manifests still validate.
* Smoke: a two-session wave where one session's plan is deliberately too long for one turn (or a stub that writes `in_progress` and stops). Expect `w<w>_continue` to run only that session and the gate to pass.

## Rollout

* The change adds tasks, so each instance needs a setup rerun after merge, and Jobs then refuses to repair runs started before it. Finish or abandon runs that still need a repair first.
* The build jobs read notebooks and the workspace skill fallback from the live `mbp` folder. Merge only when no build is running from it, and do the code edits in a separate worktree or while no build is running.
* Instances that do not want the extra tasks set `continuation_passes: 0` before rerunning setup.

## Open questions

* Default of 1 pass is a guess. Measure how often a single continuation finishes the session before raising it.
* Cost: a session that is stuck (not just out of steps) uses one more full session per pass. The cap and `0` opt-out bound this.
* Whether the continuation should get a short extra instruction in its prompt (beyond the skill) to prioritise writing the final status. Prefer keeping it in the skill so every entry point behaves the same.
