# Plan: make failed sessions and failed waves visible (low-risk version)

Status: **planned, on hold.** Do not start while other projects (AgenticTrading, Semantic Ground Truth) are running builds from the live `mbp` folder. The build jobs read the gate notebook and the workspace skill fallback from that folder, so any edit takes effect immediately.

Source: Semantic Ground Truth requests, 2026-10-26 (build job 1079028753739581, run 110489694161084, waves 4-0..4-9; and "runtime freshness check fails when a converge session's deploy is a no-op"), and the reviews that followed.

## Goals

* A run with a failed wave gate ends **FAILED**, so notifications and the run list show it.
* A session that stopped at the Genie Code step limit, or never wrote a final status, is reported by name with its conversation id and the next step.
* A stopped session leaves a useful partial record.
* A gate check that must run cannot be skipped silently.
* A no-op deploy of a Genie space or dashboard that already matches its source passes the runtime gate, and probe questions run and are reported even when freshness fails.

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

### 6. Runtime freshness: accept content that matches the source (no-op deploys)

Problem: `check_genie_space` fails when the space's `update_time` is before the run start, and `check_dashboard` fails when the published revision predates it. A converge session whose `bundle deploy` has nothing to change (normal under the new-run recovery path) leaves those timestamps alone, so the gate fails on freshness. Any problem also skips the probe questions (`"static checks failed"`), so the space's answers are never tested.

Rule (Genie spaces and dashboards):

* **fresh**: updated after the build run started (today's rule), or
* **current**: the deployed definition equals the bundle source file after normalisation.
* Fail when the resource is missing, the id does not match the target's `id`, or the content differs from the source (report the first few differing paths).
* If the source file cannot be located or read, keep today's timestamp rule and say why in the basis.

Not adopted: "deploy evidence" from the session's status file (it trusts the session's own claim, which the gate exists to check) and "no source files changed in this run" (weak, and unnecessary once content is compared).

Changes:

* New pure-Python helpers (in a gate helper module next to `session_status.py`): `normalise_genie_space`, `normalise_dashboard`, `content_diff(source, deployed, limit)`.
  * Genie space normalisation, confirmed on the Semantic Ground Truth space `01f1ceb0506f1c5d9f2024bfc5f95943` against `ground_truth_ops.geniespace.json` (identical after these three steps): join string arrays (the server splits text into line arrays); merge `data_sources.metric_views` into `data_sources.tables`; sort lists of objects by `id`, `identifier`, `column_name` or `name`.
  * Dashboard normalisation: **not yet tested** against a real dashboard (the Operations dashboard name lookup found nothing). Compare the draft `serialized_dashboard` with the `.lvdash.json` source; work out server-added fields from a real deployed dashboard before implementing. Ship the dashboard half separately if needed.
* Locating the source: new optional runtime target field `source_file` (path relative to `bundle_root`). If absent, read `file_path` for `resource_key` under `resources.genie_spaces` / `resources.dashboards` in the bundle's resource YAML (relative to that YAML file). Dashboard targets need `source_file` or `resource_key` to get content matching. Document in `docs/manifest-schema.md`; validate in `waves_manifest.py`.
* Freshness is its own entry in the target's runtime result: `{"result": "pass|fail", "basis": "fresh: updated after run start | current: content matches source | stale: content differs (<n> paths) | timestamp only: <why no source>"}`, plus `differences` when stale. The problem string references it.
* Probe questions run whenever the space is readable and the table and example-SQL checks passed, regardless of freshness. If freshness failed, probe results are reported but stay advisory (as with `probe_mode: "warn"`). Probe time is already budgeted in the gate timeout.
* `require_fresh_deployment: false` keeps its meaning (skip freshness entirely).
* Out of scope: app, job and pipeline targets (a deploy or run always creates a new deployment / run / update), and `table` targets ("written during this run" is intentional).

## Tests

* `session_outcome`: the step-limit response above with an `in_progress` status, the same response with a `pass` status, an `in_progress` status with a normal response, a missing status file, and a normal complete session.
* Gate failure message: contains the session id, conversation id and `repair from w<wave>_integrate`.
* Required checks: required + `skipped` fails, required + missing fails, not required + `skipped` passes.
* Task graph: unchanged except for what change 1 needs (existing `waves_manifest` tests still pass).
* Freshness (change 6): no-op deploy whose content matches the source passes (`current: content matches source`); content differs with an old `update_time` fails with the differing paths; space missing or id mismatch fails; normal deploy that updates the space passes unchanged (`fresh`); freshness fails but probe questions still run and are reported; Genie normalisation on an anonymised copy of the space compared above (line arrays, `metric_views`, reordered `sample_questions`); missing source file falls back to the timestamp rule.

## Rollout

1. Implement and test on the new branch; `pytest tests` passes.
2. Open the PR; after merge, switch `mbp` back to `main`.
3. Rerun setup for each instance (setup job 818046072228128 and the other dev instances) to republish skills and regenerate the build jobs.
4. Watch the next failing wave: the run should end FAILED with the session and conversation named in the gate output.

## Recovery today: instance stuck at the freshness check (no framework change, no setup)

1. In the project's `waves.json`, set `require_fresh_deployment: false` on the stuck runtime target. The gate reads the manifest at run time; this field changes neither the task graph nor the gate timeout. With freshness off and the static checks passing, probe questions run.
2. Commit that `waves.json` change to the build branch yourself, or the next wave's integrator reports it as a stray and fails that wave's gate.
3. Repair the run from `w<wave>_gate` (re-runs the gate, the gate check and all later waves). The session passed and the integrator already committed, so they do not need to rerun.
4. Do not run setup before the repair (it changes the job structure and Jobs then refuses to repair the run). Optionally set the flag back to `true` after the wave passes.

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
