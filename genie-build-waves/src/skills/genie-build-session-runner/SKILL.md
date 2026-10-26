---
name: genie-build-session-runner
description: Runs one session of a project as an unattended Genie Code job task inside a for_each wave. Reads the session definition from a waves.json manifest, executes the referenced plan (editing files, running notebooks, configuring resources, or deploy-diagnose-fix convergence loops against a deployed app/job/pipeline), validates, and writes a machine-readable status file. Supports git, workspace, and hybrid workflow modes. Use when a job task passes session_id, wave, run_id, branch, build_root and manifest_path.
---

# Session Runner

You are one of several Genie Code sessions running **in parallel** on the same project (or, for a `converge` session, the only session in a sequential convergence wave). You run unattended with auto-approve, so the guardrails below are hard rules, not suggestions. Your job: complete exactly one session plan, within your ownership boundaries, then report.

## Inputs (from the job task parameters)

| Parameter | Meaning |
|---|---|
| `session_id` | Session to run, e.g. `01`, `06a`, `13` |
| `wave` | Wave id, e.g. `0`, `1`, `4a`, `4-1` |
| `run_id` | Job run id. Used to namespace status files |
| `branch` | Feature branch (for `git`/`hybrid` workflows; may be empty for `workspace` mode) |
| `build_root` | Absolute workspace path of the project |
| `manifest_path` | Absolute path of `waves.json` |

If any required parameter is missing or still looks like a `{{placeholder}}`, stop and write a status file with `status: "error"` (step 7) if you can, then end.

## Guardrails (hard rules)

Guardrails 1–3 apply based on the **workflow mode** (from `manifest.workflow.mode`, default `git`) and **session mode** (from session `mode`, default `edit`).

### Always apply (all modes)

1. **Read-only for shared docs.** Do not edit plan files (`plans_dir/**`), session index files (`sessions_dir/INDEX.md`), project memory files (`PROJECT_MEMORY.md`), collaboration folders (`hi_genie/**`), or the manifest (`waves.json`).
2. **Data and secrets.** Never write or print secret values. Never run DROP, TRUNCATE or DELETE on Unity Catalog or Lakebase objects that you did not create in this session.
3. **No scope creep.** Do only the `scope` text for your session. If the plan file and the manifest `scope` disagree, the manifest wins; note the conflict in your status file.
4. **Fail loud, not silent.** If you cannot finish, still write the summary and status file with what was done and what is blocking.

### Git guardrails (workflow `git` or `hybrid`)

5. **Git: read-only.** Never commit, push, pull, checkout, switch, merge, rebase, reset, stash or discard. Other sessions share this working tree; any of those would destroy their work. The wave integrator commits.
6. **Never touch `main`.** If `branch` is `main` or `master`, or the Git folder is not on `branch`, stop with `status: "error"`. Do not switch branches.

### Ownership guardrails (by session mode)

7. **`edit` mode (default):** Create, edit or delete files only if they match your session's `owned_paths` and do not match `exclude_paths` (globs relative to `build_root`). The two exceptions are your summary and status files (steps 6-7). Changes outside your paths go to `requests` in your status file.
8. **`execute` mode:** Run notebooks, SQL queries, SDK calls, or CLI commands as described in your plan. You may create output artifacts (tables, model versions, dashboard widgets) listed in `owned_assets`. Do not edit project source files unless they are also in your `owned_paths`.
9. **`configure` mode:** Configure Databricks resources (jobs, pipelines, endpoints, permissions, secrets) as described in your plan. Resources you modify should be listed in `owned_assets`.
10. **`converge` mode:** Same file ownership as `edit` (`owned_paths` enforced). In addition you may deploy and run **only** the `runtime_targets` named on your session, using each target's `bundle_root`, `bundle_target` and `deploy_commands`. You are the only session in your wave, so nobody else is editing the working tree while you deploy.

### Deploy and execute guardrails

11. **Deploys.** Only if your session has `allow_deploy: true` or is `converge` mode, and only with the target specified in `bundle_target` (or the runtime target's `bundle_target`). Never deploy or destroy anything on a target not listed. Never run `bundle destroy`, never delete or recreate an app, job or pipeline, and never rename a runtime target.
12. **Execution.** Only if your session has `allow_execute: true` (default for `execute`/`configure`/`converge` modes, false for `edit` mode). When executing notebooks or SQL, do not modify objects outside your `owned_assets` / `runtime_targets`.
13. **Fix causes, not symptoms.** Never make a build or gate pass by hiding the problem: deleting or skipping tests, excluding source files from compilation, blanket `any` / `@ts-ignore` / `# type: ignore` / lint-disable, swallowing exceptions at startup, or turning features off with flags. If a suppression is genuinely the right call (e.g. test files should not be in the production compile), make it narrowly and record it under `suppressions` in your status file with the reason. Unrecorded suppressions are a guardrail violation.

## Steps

### 1. Load your session

Read `manifest_path`. Find the wave whose `wave_id` equals `wave` and, inside it, the session whose `session_id` equals `session_id`.

Keep from the session: `title`, `plan_file`, `scope`, `mode` (default `edit`), `owned_paths`, `owned_assets`, `exclude_paths`, `allow_deploy`, `allow_execute`, `depends_on`, `runtime_targets`, `max_attempts` (default 5), `context_notes`.

Keep from the manifest top level: `workflow` (default `{"mode": "git"}`), `bundle_target`, `status_dir`, `plans_dir`, `sessions_dir`, `repo_root` (default: `build_root`), `context_files`, and the `runtime_targets` definitions named by your session.

Determine your effective mode:
- `workflow_mode` = `manifest.workflow.mode` or `"git"`
- `session_mode` = session `mode` or `"edit"`

If the session is not found, stop with `status: "error"`. If its wave has `"archived": true`, also stop with `status: "error"` (`blocking`: "wave is archived; re-run setup"): archived waves are earlier builds and never run.

**Archived dependencies.** A `depends_on` entry that names a session in an archived wave is already satisfied: that session finished in an earlier build, and its code is in the branch history. Never look for a `.build-status` (`status_dir`) file for it, in this run or any other, and never stop or warn because one is missing. Its summary in `sessions_dir` (step 3) is still useful context if it exists.

**Task retries.** The job retries a Genie Code task automatically when the agent fails to start or crashes (`max_retries` on the job task). If your status file for this `run_id` or a summary for your session from today already exists, you are a retry: read them and the current state of your `owned_paths` / `owned_assets`, and continue from where the previous attempt stopped (keep finished work). In steps 6-7, update that same summary and status file so they describe the combined result of all attempts.

### 2. Check the branch (git/hybrid only)

If `workflow_mode` is `git` or `hybrid`:
- Use the Git tooling read-only (status/current branch) on `repo_root`. It must be on the `branch` parameter. If not, or if `branch` is `main`/`master`, stop (guardrail 6).

If `workflow_mode` is `workspace`: skip this step entirely.

### 3. Read context, in this order

1. `repo_root/PROJECT_MEMORY.md` and, if present, `repo_root/hi_genie/` (read-only collaboration notes; follow any pending recommendation that applies to your session).
2. The project's plan index (`build_root/<plans_dir>/INDEX.md`): wave plan, dependency graph, hidden dependencies, shared-file table, resolved gaps.
3. Your plan file (`build_root/<plans_dir>/<plan_file>`): only the tasks named in `scope` apply.
4. Session summaries of your `depends_on` sessions in `build_root/<sessions_dir>/` (latest file whose name contains `-<dep_id>-`), to learn what they actually produced. For a dependency in an archived wave, a missing summary is fine: read the code it owned instead.
5. For `edit` sessions: the current contents of every file you are about to change.
6. For `execute`/`configure` sessions: the current state of every asset you will modify (read tables, inspect resources).

If the manifest contains a `context_files` list, read those too — they provide project-specific conventions, coding standards, data dictionaries, or architectural decisions.

If the session has `context_notes`, treat them as a hand-over from an interactive Genie Code session (known errors, log excerpts, decisions already made). Verify them against the current code and telemetry before relying on them; they may be stale.

### 4. Do the work

**Write a provisional status file first.** Before any work, write `build_root/<status_dir>/<run_id>/<session_id>.json` with `status: "in_progress"`, empty arrays for `files_changed`, `assets_changed`, `checks`, `assumptions`, `requests`, and a `progress` object: `{"done": [], "next": "<first step>", "attempt": null}`. This ensures the integrator can attribute files under your `owned_paths` to your session even if you run out of turns before writing the final status file (step 7).

**Record progress at milestones only.** Update the status file (including `files_changed` so far and `progress`) at these points and no others: the start and the end of each converge attempt (`attempt` = the attempt in flight, `null` between attempts), and after each major task in your plan for other modes. `done` lists the finished steps in a few words each; `next` is the next step a resumed session should take. Every write costs steps, and running out of steps is what this record is for, so do not update it after every small step. Replace it with the final version in step 7 (keep `progress` there; `next` empty when finished).

Based on your `session_mode`:

**`edit` mode:**
- Follow the existing code style; preserve comments.
- Use the workspace file tools for all edits; never use shell commands to write files.
- Parallel dependencies: if you import from a file another session in the **same wave** owns and it does not exist yet, code against the signature documented in its plan, and record it under `assumptions`.

**`execute` mode:**
- Create and/or run notebooks, SQL queries, or SDK scripts as described in your plan.
- Record outputs (table row counts, model metrics, query results) in your session summary.
- If execution fails, capture the error in your status file and mark `status: "fail"`.

**`configure` mode:**
- Create, update, or configure the Databricks resources described in your plan.
- Verify each resource reached its expected state.
- Record resource ids, endpoints, or URIs in your session summary for downstream sessions.

**`converge` mode** — a bounded loop. For attempt `n = 1 .. max_attempts`:

1. **Deploy.** First re-check the branch (step 2). If the Git folder is no longer on `branch` (it was switched mid-run), stop with `status: "error"` and say so; never deploy code from another branch. Then, for each of your `runtime_targets`, run its `deploy_commands` with the Databricks CLI from its `bundle_root` (default for apps: `bundle deploy --target <t>` then `bundle run <resource_key> --target <t>`; for dashboards and Genie spaces: `bundle deploy --target <t>` only, because deploy publishes the dashboard and writes the space). If a command itself fails (validation, permissions, resource conflict), that is the attempt's error.
2. **Wait for a terminal state.** Apps: poll the app (SDK `w.apps.get(name)` or CLI `apps get <name>`) until `active_deployment` / `pending_deployment` is no longer `IN_PROGRESS`, then until `app_status` leaves `DEPLOYING`/`STARTING`. Jobs: wait for the triggered run to terminate. Pipelines: wait for the update to reach `COMPLETED`/`FAILED` (or a few minutes of `RUNNING` for continuous). Dashboards: confirm the published revision (`w.lakeview.get_published(id).revision_create_time`) is newer than your deploy. Genie spaces: confirm `update_time` from `GET /api/2.0/genie/spaces/<id>` (raw API; the SDK model omits it) is newer than your deploy.
3. **Diagnose.** Collect evidence for *this* attempt only:
   - Apps: deployment status message, and the target's `telemetry.logs_table` filtered to the new deployment id (`attributes:['app.deployment_id']::string = '<id>'`, attribute key from `telemetry.deployment_id_attribute`). Build errors usually have `severity_text = 'UNKNOWN'`, so match `body::string` against `telemetry.error_patterns` (default `error TS\d+`, `Error building app`, `Unhandled`, `UnhandledPromiseRejection`, `FATAL`, `"level":"(error|fatal)"`) as well as `severity_text IN ('ERROR','FATAL')`, excluding `ignore_patterns` (default `App did not respect SIGTERM timeout`, `[ELIFECYCLE]`). Look at `BUILD` lines first, then runtime lines.
   - Apps with `probes`: run them the way the gate does, with the genie-build-waves module `src/notebooks/app_probes.py` (next to the gate notebook): `pw, probe_identity = probe_client(w, probe_auth, dbutils.secrets.get)` (returns `(client, identity_label)`), then `results, problems = run_app_probes(w, app_name, probes, probe_w=pw)` (returns `(results, problems)`; pass when `problems` is empty). `probe_client` raises `ValueError` when `probe_auth` is missing or a secret cannot be read; wrap both calls in `try/except` the way the gate does and treat that as `blocked` (an access problem). `run_app_probes` does not raise on bad credentials; it reports them in `problems`. `probe_auth` (target, else top-level) names the secret scope holding the service principal's OAuth client id and secret; never print secret values. Bad credentials (`invalid_client`), a redirect to sign-in or a 401/403 is an access problem, not a code bug: stop as `blocked` and name the service principal that needs `CAN_USE` on the app (or `READ` on the scope).
   - Traces, when the target has them: use them for diagnosis, not only the gate's count. OTel spans in `telemetry.traces_table` (`service_name` = app name, `time` since your deploy; spans with `status.code = 'STATUS_CODE_ERROR'` and their `status.message`, `name`, `attributes` locate failing requests). MLflow 3 traces in `telemetry.mlflow_experiment_id`: `mlflow.search_traces(locations=[id], filter_string="trace.timestamp_ms >= <deploy ms>", include_spans=False)`, then load spans only for traces in state `ERROR`. An agent that answers probes but records error traces is `unhealthy`.
   - Jobs: the run's task error and output. Pipelines: the update's event log errors; with `max_failed_records` / `max_dropped_records`, also the update's `flow_progress` `data_quality` (per-expectation `failed_records`, `dropped_records`), from the pipeline's UC event log table if it publishes one. Over budget is `unhealthy`: fix the transformation or the source data handling that produces the bad rows; do not loosen or remove the expectation unless the plan says the rule is wrong, and list any such change as a suppression.
   - Dashboards: run `EXPLAIN <query>` for every dataset in the draft's `serialized_dashboard` on the dashboard's warehouse (with the dataset's `catalog`/`schema` and default parameter values). An `EXPLAIN` whose result starts with `Error occurred during query planning` is a failure even though the statement `SUCCEEDED`; the error is on the next row. Table / metric view datasets (`asset_name`) must resolve in Unity Catalog.
   - Genie spaces: read the configuration with `w.genie.get_space(id, include_serialized_space=True)` (needs `CAN_EDIT`). Every `data_sources.tables[].identifier` must resolve in Unity Catalog, every `column_configs[].column_name` must still be a column of its table, and every `instructions.example_question_sqls[].sql` must pass `EXPLAIN` on the space's warehouse (same `Error occurred during query planning` rule). Stale `column_configs` after a table change are a real failure: fix the space definition, not the table, unless the table is yours.
   - Genie spaces with `probe_questions`: ask each one (`w.genie.start_conversation_and_wait(id, question)`). It must return a query attachment whose result (`get_message_attachment_query_result`) is `SUCCEEDED`. A text-only answer means Genie did not see the data it needs: improve the space's instructions, example SQL or table/column descriptions, never the question. In `probe_mode: fail` this is `unhealthy`; in `warn`, report it in your summary but it does not block `stable`.
4. **Classify** the attempt (dashboards: a dataset that fails `EXPLAIN` is `unhealthy`; Genie spaces: an unresolved table, stale column config or failing example SQL is `unhealthy`): `deploy_failed`, `build_failed`, `crashed` (app starts then goes `CRASHED`/`UNAVAILABLE`), `unhealthy` (running but error lines, missing `required_markers`, a failing probe, or error traces over `max_trace_errors`), or `stable`.
5. **Stop or fix.**
   - `stable`: confirm it holds for a short self-soak (about 3 minutes, same deployment id, still `RUNNING`, no new error lines), then leave the loop. The gate notebook runs the real soak.
   - Root cause inside your `owned_paths`: fix it (all errors you can see, not one at a time), then go to the next attempt.
   - Root cause outside your `owned_paths` (another bundle, a missing secret, infra, permissions): do not work around it. Record a `request` and stop with `status: "blocked"`.
   - Same errors two attempts in a row with no progress: stop with `status: "fail"`.
6. **Record** each attempt in `attempts` (status file, step 7): deployment/run/update id, classification, the distinct errors (short, de-duplicated), the fix applied and the files touched.

Stop early if fewer than ~15 minutes remain before the task timeout, so you still write the summary and status file.

**All modes:** Follow any project-specific conventions found in `context_files` or `PROJECT_MEMORY.md`.

### 5. Validate

Run every acceptance-criteria check from your plan. Typical checks by mode:

**`edit`:** `bundle validate --strict --target <bundle_target>` if you touched YAML. Language-specific checks (typecheck, lint, test) if available.
**`execute`:** Verify outputs exist and pass quality checks (row counts, schema matches, metric thresholds). If the wave's `runtime_gate` lists `type: table` targets you own, check them the way the gate will: the table resolves, has every `required_columns`, `COUNT(*) >= min_rows`, and (unless `require_fresh_deployment: false`) your run wrote it: a new `DESCRIBE HISTORY` commit, or a new refresh for a materialized view. Re-running an idempotent write that changes nothing still commits; skipping it does not.
**`configure`:** Verify resources are in expected state (running, active, accessible).
**`converge`:** The last attempt is classified `stable` for every runtime target, plus `bundle validate --strict` for each target's bundle. `status: "pass"` requires both. A deploy that succeeded earlier but not on the final code does not count.

Deploy-time checks only when `allow_deploy` is true. A check you did not run does not count as passed.

### 6. Write your session summary

Path: `build_root/<sessions_dir>/<YYYY-MM-DD>_w<wave>-<session_id>-<short-slug>.md`. Get the date from `datetime.now()`. Content: problems, root causes, changes, decisions, files modified or assets created, checks run with results, requests for other sessions. Do not edit `<sessions_dir>/INDEX.md`; the integrator does.

### 7. Write your status file

Path: `build_root/<status_dir>/<run_id>/<session_id>.json`. Exactly this shape:

```json
{
  "session_id": "03",
  "wave": "1",
  "run_id": "123456",
  "mode": "edit | execute | configure | converge",
  "status": "pass | fail | blocked | error",
  "summary_file": "docs/sessions/2026-10-21_w1-03-lakebase-migrations.md",
  "files_changed": ["server/migrations/migrate.ts"],
  "assets_changed": ["catalog.schema.my_table"],
  "checks": [{"name": "bundle validate --strict", "result": "pass | fail | skipped", "detail": ""}],
  "assumptions": [],
  "requests": [{"path": "package.json", "change": "add dependency x@1.2", "why": ""}],
  "suppressions": [{"path": "tsconfig.server.json", "kind": "compile-exclude | ts-ignore | lint-disable | test-skip | catch-swallow | feature-flag | other", "why": ""}],
  "attempts": [{"n": 1, "target": "app", "deployment_id": "", "result": "deploy_failed | build_failed | crashed | unhealthy | stable", "errors": ["server/x.ts(12,3): TS2345 ..."], "fix": "", "files_changed": []}],
  "runtime": {"app": {"deployment_id": "", "state": "RUNNING"}},
  "progress": {"done": ["migrations written", "attempt 1 deployed"], "next": "", "attempt": null},
  "blocking": ""
}
```

`progress` is the milestone record from the provisional status file (step 4). If the session stops early (step limit, crash), the gate quotes `progress.next` with the session's conversation id so it can be resumed.

`suppressions`, `attempts` and `runtime` are required for `converge` sessions (use empty values when not applicable) and optional otherwise.

`status` is `pass` only if the scope is complete and no check failed. `files_changed` lists files created/edited/deleted (relative to `build_root`). For `converge` sessions it must equal the union of every attempt's `files_changed` plus any **inherited** files: uncommitted changes in your `owned_paths` that an earlier run of this same session left behind (it failed its gate, and this is a new build run). Keep and build on those changes and list them in `files_changed`, but not in an attempt you did not change them in; the gate credits them from that earlier run's status file for your session. Any file you edit before attempt 1 goes in attempt 1's `files_changed`; a file in `files_changed` that neither an attempt nor an earlier run of your session lists fails the gate. `assets_changed` lists non-file assets created or modified (tables, notebooks, resources). Both exclude the summary and status files.

### 8. Final response

End with at most 5 lines: `session_id`, `mode`, `status`, number of files/assets changed, failed or skipped checks, and the status file path. This text becomes the task output.

## Edge cases

- **Session already done** (summary + status `pass` for an earlier `run_id`, and the outputs match the plan): re-validate, then write a new status file for this `run_id` with `status: "pass"` and note "already completed".
- **Manual prerequisite missing** (e.g. a dependency that requires work outside Genie Code): do what you can, mark `status: "blocked"`, and name the prerequisite in `blocking`.
- **Another session's output is broken**: do not fix it. Record it under `requests`.
- **Workspace mode with no Git folder**: skip all Git checks. Your working directory is `build_root` but you may create/modify assets anywhere within your `owned_assets`.
