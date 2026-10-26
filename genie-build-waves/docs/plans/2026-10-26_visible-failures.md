# Plan: make failed sessions and failed waves visible (low-risk version)

Status: **planned, on hold.** Do not start while other projects (AgenticTrading, Semantic Ground Truth) are running builds from the live `mbp` folder. The build jobs read the gate notebook and the workspace skill fallback from that folder, so any edit takes effect immediately.

Source: Semantic Ground Truth request, 2026-10-26 (build job 1079028753739581, run 110489694161084, waves 4-0..4-9), and the review that followed.

## Goals

* A run with a failed wave gate ends **FAILED**, so notifications and the run list show it.
* A session that stopped at the Genie Code step limit, or never wrote a final status, is reported by name with its conversation id and the next step.
* A stopped session leaves a useful partial record.
* A gate check that must run cannot be skipped silently.

## Prerequisites

1. Merge the inherited-files PR (branch `mg-genie-build-waves-inherited-files`, commit 578f3ac) after it has run in at least one real build (AgenticTrading w13a repair).
2. Start this work on a **new** branch from `main` (for example `mg-genie-build-waves-visible-failures`).
3. Do the edits in a separate Git worktree, or while no build is running, so live builds are not affected mid-run.
4. Finish or abandon any run you still need to repair. The setup rerun at the end changes the job structure, and Jobs then refuses to repair older runs.

## Changes

### 1. Gate raises when it fails (Bug 3)

* `src/notebooks/wave_gate_check.ipynb`: after setting the `gate_passed` task value, raise with the list of problems when the gate did not pass. The task then ends FAILED, the downstream waves become UPSTREAM_FAILED (still zero compute), and the run ends FAILED.
* Keep the `w<wave>_gate_check` condition tasks for now. With the gate failing, they do not run (upstream failed), and later waves are not started either way. Removing them is a later clean-up, not part of this change.
* Docs (README, `docs/prompts/repair-failed-wave.md`): a failed gate is now a FAILED task. Repair still means selecting `w<wave>_integrate` and later tasks yourself (Jobs' default repair selection only picks the failed gate).

### 2. Step-limit and incomplete-session detection in the gate (Bug 1, gate-level)

* New pure-Python helper (in `session_status.py`): `session_outcome(response, status)` returns `complete`, `step_limit`, `in_progress` or `missing`.
  * `step_limit`: the genie_task response matches the step-limit text ("I've reached the maximum number of steps for this turn").
  * `in_progress` / `missing`: the status file is still `in_progress` or does not exist.
* The gate notebook reads each session iteration's output from the Jobs API (`runs/get` on this run's `w<wave>_sessions` task for the iterations, then `runs/get-output` for `genie_task_output.conversation_id` and `agent_output.response`). Confirmed available on iteration 861320051785964.
* For any session that is not `complete`, the gate problem names the session, the conversation id and the next step: "session 33 hit the step limit (conversation 3614498846438467): resume that conversation, then repair from w4-1_integrate".
* Jobs API failures are a warning, not a gate failure; the existing status-file checks still apply.

### 3. Runner records progress as it goes (Bug 1, item 3)

* `src/skills/genie-build-session-runner/SKILL.md`: add a `progress` object to the status file (`done`: steps finished, `next`: next step, `attempt`: attempt in flight) and update it after every task and attempt, not only at the end.
* The integrator includes `progress` in the session table for a session that is `error` / `in_progress`, so the resumed or repaired session knows where to pick up.

### 4. Required gate checks (item 5)

* Manifest: a gate check may be marked `required: true`. Document it in `docs/manifest-schema.md` and validate it in `waves_manifest.py`.
* Integrator skill: report each required check by name in the gate file's `checks`.
* Gate notebook: fail when a required check is missing or has result `skipped`.
* Projects that need a toolchain (for example Node for tsc/vitest) put the setup in their own manifest `gate` text; the bundle does not install toolchains.

### 5. Documentation only

* **Planner fixes outside a session's paths (item 6):** commit them yourself before repairing; otherwise the integrator correctly reports them as strays.
* **Genie Code retries (Bug 2):** keep task-level retries (default 2). They exist for start-up failures (`INTERNAL_ERROR: start_agent_run`), where the 60-second interval works. Note in the README that `min_retry_interval` counts from the start of the failed attempt, so after a long failure the retry starts almost immediately (seen: 2 s after a 32-min failure). Raise the PrincipalContext error with Databricks (IDs below).
* **UC skill load (item 4):** no change. The skill-reading tool cannot load UC skills by full name, so sessions fall back to the workspace `SKILL.md`; not a permissions problem (checked 2026-10-24).

## Tests

* `session_outcome`: the step-limit response above with an `in_progress` status, the same response with a `pass` status, an `in_progress` status with a normal response, a missing status file, and a normal complete session.
* Gate failure message: contains the session id, conversation id and `repair from w<wave>_integrate`.
* Required checks: required + `skipped` fails, required + missing fails, not required + `skipped` passes.
* Task graph: unchanged except for what change 1 needs (existing `waves_manifest` tests still pass).

## Rollout

1. Implement and test on the new branch; `pytest tests` passes.
2. Open the PR; after merge, switch `mbp` back to `main`.
3. Rerun setup for each instance (setup job 818046072228128 and the other dev instances) to republish skills and regenerate the build jobs.
4. Watch the next failing wave: the run should end FAILED with the session and conversation named in the gate output.

## Deferred (revisit only if it happens again)

* **Per-session child job** for in-iteration detection and automatic relaunch. Untested (Genie Code task inside a child job), adds a second job per instance, moves the conversation into a separate run, and a relaunch is a new conversation that may hit the step limit again.
* **Setting Genie Code retries to 0** and retrying inside the build.
* **Toolchain install in the gate** (Node/pnpm).
* **`planner_files`** status field or planner commit file.
* **Removing the `w<wave>_gate_check` condition tasks.**
* **Planner guidance on smaller session scopes** (two sessions hit the step limit at 33–40 min).

## Support case details (Bug 2)

* Job 1079028753739581, run 110489694161084, session 35 (wave 4-3).
* Original iteration 341867750922089 failed after 31.9 min: "Scheduled Genie Code action failed: Something went wrong" (threadId 2544428900279823, sessionId 8fc94fc1b47e444295175a4f799fea9b, actionId cbb42384-91d4-4350-b50e-8d284fc6ebf5).
* Retries 920020760324326 (started 2 s later) and 803713897526006 (about 60 s after that) failed in 0–1 s: "Unexpected error starting Scheduled Genie Code: INVALID_ARGUMENT: INVALID_PARAMETER_VALUE: PrincipalContext must contain an account ID for login RPC auth".
* A manual repair later started normally (iteration 549584662064751).
