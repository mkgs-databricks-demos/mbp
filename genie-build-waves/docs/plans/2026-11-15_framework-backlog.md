# genie-build-waves framework backlog

**Status:** open backlog, not scheduled. Each item has a proposed decision (adopt / defer / drop) for the owner to confirm.
**Date:** 2026-11-15 (items first reported 2026-10-31 by a consumer project's fourth build; see `docs/sessions/2026-11-15_framework-backlog.md` for the source)
**Scope:** framework changes found by running real builds. Each item is independent; pick and order them.

State on `main` is as of the date above.

## Summary

| # | Item | State on `main` | Proposed | Before a new level 4 project? |
|---|---|---|---|---|
| 1 | Freshness is measured from the run start | Planner rule done 2026-11-15; gate change open | Adopt | Done (planner) |
| 2 | Tracked gate waivers and gate preconditions | Planner guidance done 2026-11-15; `waivers` block open | Adopt (planner guidance now, `waivers` block later) | Done (planner) |
| 3 | Owner-interactive steps | Planner list done 2026-11-15; `owner_steps` field open | Adopt (planner list now, `owner_steps` field later) | Done (planner) |
| 4 | Sessions cannot edit dashboard objects | Open | Adopt (planner guidance) | Only if the project has dashboards |
| 5 | One request schema and routing to later sessions | Schema and grouping done 2026-11-15; warn/fail option open | Adopt | Done (schema) |
| 6 | Non-standard session status values | Partly | Adopt (small) | Optional |
| 7 | Failed or blocked sessions end SUCCESS | Documented; design note; monitor handles it with fresh runs (2026-11-25) | **Adopt** (raised 2026-11-25 after a consumer build: biggest remaining monitor-autonomy gap) | No, but next framework build |
| 8 | Error patterns that match the redaction placeholder | Open | Adopt (planner note) | Only if telemetry gates are used |
| 9 | Tooling versions (CLI, Node) | Partly | Defer | Only for JS projects |
| 10 | Owner decisions recorded in Git (added 2026-11-25) | Open | Adopt (design) | No |
| 11 | Machine-checked wave preconditions (added 2026-11-25) | Open | Adopt (design) | No |

## 1. Freshness is measured from the run start

`src/notebooks/wave_gate_check.ipynb` compares app deployments, job runs, pipeline updates and table commits with the build run's start (`check_app`, `check_job`, `check_pipeline`, `check_table`, all take `run_start`). A fresh run started with `only` (README "Fresh runs") fails every `require_fresh_deployment` target that was deployed or written in the earlier run and not again in the fresh one, even when the data is minutes old. Repairing the original run passes.

This matters more now that the level 4 monitor starts fresh runs (monitor skill section 8 step 4). A fresh run from the failed wave re-runs that wave's sessions, so targets they redeploy are fresh. Targets deployed by an earlier wave, or written only by an outside schedule, are not.

Proposed:

* **Now (planner):** a runtime target with `require_fresh_deployment: true` must be deployed or written by a session in the same wave. Otherwise set `require_fresh_deployment: false` and check something else (row counts, columns, a recent timestamp column).
* **Later (gate):** measure freshness from the wave start (first `w<wave>_sync` or `w<wave>_sessions` task start in this run), or add a per-target `fresh_since` (`run_start` | `wave_start` | ISO timestamp). Document the repair-the-original rule in the README until then.

## 2. Gates that depend on outside conditions

Some gate lines cannot be met for reasons outside the code: data that only exists under a business condition (for example no rows because nothing happened today), a span emitted only on one branch of the logic, a job that has never succeeded. The only way through today is hand-editing a status file under `.build-status/<run>/` (not in Git) and noting it in the manifest. A level 4 monitor cannot do that (manifest and plan edits are stop conditions), so every such line becomes an escalation.

Proposed:

* **Now (planner):** write the precondition into the gate line ("if X, then Y; otherwise evidence Z") and a fallback evidence path in the plan. Never gate on a job with no known-good run.
* **Later:** a manifest `waivers` block (`wave`, `gate_line` or target, `waived_by`, `reason`, `request_id`, `expires`) that the gate applies and reports as `waived`, not `pass`, in the gate file and the build verdict.

## 3. Owner-interactive steps

Unattended Genie Code tasks are refused for some operations: creating an app and some app updates (`Invalid delegation claim`), `bundle run` of jobs that change grants, account group changes, `bundle destroy`, file and folder deletes. Each costs a repair cycle when a session discovers it at run time. The planner skill's "Owner-only steps" tip covers only destroy and deletes.

Proposed:

* **Now (planner):** list the known-refused operations; plan them as `manual_prereqs` (before the wave) or as owner steps with exact commands and a verification, never as session work.
* **Later:** a session field such as `owner_steps: [{when: before|after, commands: [...], verify: ...}]` that setup renders into the plan header and the integrator checks for evidence before failing the session.

## 4. Sessions cannot edit dashboard objects

A `.lvdash.json` stored as a dashboard workspace object cannot be edited as a file, and a Lakeview API write replaces the whole definition.

Proposed (planner): dashboard edits are owner steps, or one dedicated session with an approved API path. The integrator notes requests that target a dashboard object.

## 5. One request schema and routing to later sessions

The runner skill's status example uses `{path, change, why}` for `requests`; the integrator skill's gate file uses `{from, path, change}`. Sessions also wrote other shapes (`{to, path, ask}`, `{to, what}`, `{to, text}`). A request addressed to a later session reaches it only if a person edits that session's plan, which a level 4 monitor may not do.

Proposed:

* **Now:** one schema in both skills: `{from, to, path, change, why, priority}`.
* **Later:** the integrator lists open requests per target session in the wave summary, and warns (or fails, by manifest option) when a request names a later session whose plan or `context_notes` does not mention it. Requests against files no session may edit (for example the project memory file) are listed separately for the owner.

## 6. Non-standard session status values

Sessions sometimes write `done` or `completed`. Only `pass`, `fail`, `blocked` and `error` are final (`session_outcome` in `session_status.py`); anything else counts as incomplete, so a continuation pass re-runs the session, and if it is still not final the gate reports it as `error`. That is safe but costs a session run.

Proposed: the runner skill states the allowed values explicitly next to its status example; optionally the integrator names the fix ("use `pass`") when it sees `done` or `completed`.

## 7. Failed or blocked sessions end SUCCESS

A session that writes `fail` or `blocked` still ends its `for_each` iteration SUCCESS, so repairing `w<wave>_sessions` re-runs nothing. README "Why not repair?" documents it, the level 4 monitor starts a fresh run instead (monitor skill section 8 step 4), and `2026-11-15_failing-session-iterations-design.md` describes how to make such iterations fail.

Proposed (updated 2026-11-25): **adopt**, as the next framework change after the current consumer build finishes. Evidence from that build: a gitignored overrides file was fixed by the owner, the owner asked for a repair from `w<w>_sessions`, and the monitor had to stop and ask because that repair would rerun nothing; the fix cost a round trip with the owner even though the cause was gone. The 2026-11-25 monitor rules (fresh run for owner fixes outside Git, goal over mechanism) work around it; making a `blocked` / `fail` iteration end FAILED would let a plain repair rerun the session and remove the repair-versus-fresh-run distinction for people and monitors.

Before building, decide from the design note:

* **How the iteration fails.** The Genie Code task itself cannot set its own outcome, so either a small per-iteration check task (for_each inner task becomes runner + check) or `find_incomplete` treats `blocked` / `fail` as incomplete and routes them to the continuation pass.
* **Cascade.** A failed iteration must still let the integrator and gate run (`run_if` on the integrator, or the If/else pattern already used after the gate) so the wave reports why it failed.
* **Budget.** Repairs that now rerun sessions count against the monitor's `max_repairs` exactly like fresh runs do.
* **Test it** with a scratch instance (a second genie-build-waves instance on a test manifest), since the job graph changes.

## 8. Error patterns that match the redaction placeholder

A project's telemetry error pattern such as `api_token=[A-Za-z0-9]{8,}` also matches the redacted form `api_token=REDACTED`, so every redacted line is a false positive. `DEFAULT_IGNORE_PATTERNS` in the gate notebook does not have the problem (it only ignores app shutdown noise).

Proposed (planner and examples): use a negative lookahead, for example `api_token=(?!REDACTED)[A-Za-z0-9]{8,}`, or add the placeholder to `ignore_patterns`.

## 9. Tooling versions

An integrator once ran a Databricks CLI older than the bundle's fields required (`workspace.sync_mode` needs v1.23.0), and downloading a newer CLI was blocked. On serverless, `npm` and `npx` were broken symlinks; a working route was `pip install nodejs-wheel-binaries` plus `npm-cli.js`. The smoke job's `capability_probe` checks CLI access, not its version.

Proposed: defer. When picked up, add the CLI version (and, for JS projects, a working Node route) to `capability_probe`, and a planner note on toolchain setup.

## 10. Owner decisions recorded in Git

An owner decision that changes a wave's outcome (defer a blocked session, accept a gate line, waive a check) is applied today by hand-editing `.build-status/<run>/<session>.json` in the workspace. An external monitor never writes workspace files (guardrail 2), so every such decision needs a person or an agent with workspace access, and the change is invisible in Git history. In a 2026-11-25 consumer build, deferring a UC Pages session (no Discover domain) needed a workspace edit by another agent before the monitor could repair.

Proposed:

* A tracked file, by default `<plans_dir>/owner_decisions.json`, next to the monitor grants file: entries `{wave, session_id, decision: "pass_deferred" | "waive_gate_line" | "waive_check", gate_line or check, reason, decided_by, request_id, expires_build}`.
* The monitor may commit an entry only when the owner states the decision in their reply (quoted in the commit message), never on its own; an `authorization_policy` switch (`monitor_may_record_decisions`) turns this on.
* The integrator and gate apply entries for the current build: a deferred session counts as `pass` with `deferred: true`; a waived line is reported as `waived`, not `pass`, in the gate file and the build verdict (folds in item 2's `waivers` block).
* `validate_manifest` checks the file's shape; setup prints the active decisions.
* With this, the monitor repairs from `w<w>_sync` (the sync pulls the decision) instead of waiting for a workspace edit.

## 11. Machine-checked wave preconditions

`manual_prereqs` are prose. When one is not met, the wave's sessions discover it at run time, after 5-10 minutes per session, and end `blocked`. In the 2026-11-25 consumer build two waves stopped that way: no Discover domain for a UC Pages session, and an agents bundle's overrides file naming a schema that did not exist (it was created by an earlier wave under another name).

Proposed:

* An optional per-wave `preconditions` list of machine checks, each `{name, check, hint}`, where `check` is one of a small set: `uc_object_exists` (catalog / schema / table / volume name), `discover_domain_exists` (name or id), `file_exists` (relative to `build_root`, gitignored files included), `json_value_matches` (file, key, `uc_object_exists` of its value), `bundle_validates` (bundle path, target).
* A `w<w>_preconditions` notebook task between `w<w>_synced` and `w<w>_sessions` (like the sync task: never raises, writes `wave_<w>_preconditions.json`, sets a task value). A failed check excludes the wave's sessions and `build_verdict` reports `PRECONDITION_FAILED: <name>: <hint>` within seconds.
* The monitor's decision table gets a row: a failed precondition is an owner step (escalate with the hint), or, when the owner then fixes it, a repair from `w<w>_preconditions` (no session ran, so a repair is enough).
* Values that must not be committed (catalog names, schema names) are read from the files the check names, so manifests stay workspace-neutral.

## Done when

The owner has confirmed adopt / defer / drop for each item, with a branch or plan for the adopted ones.
