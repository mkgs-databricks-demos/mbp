# waves.json Manifest Schema

The manifest is the single source of truth for a project. It defines the workflow mode, waves, sessions, ownership boundaries, gate checks, concurrency, and (for follow-up builds) the runtime targets that must deploy and run stably. Every Genie Code session (runner and integrator) and the deterministic gate notebook read it at runtime.

## Build Phases

A project typically goes through two phases. Both use the same manifest format and job; they differ in session mode and gate type.

| Phase | Session mode | Wave shape | Gate | Pass means |
|---|---|---|---|---|
| **Initial build** | `edit` / `execute` / `configure` | Wide, parallel, disjoint `owned_paths` | Static (`gate` text: validate, file checks) | Files exist, bundle validates |
| **Convergence** (follow-up) | `converge` | One session per wave, sequential | Static `gate` + deterministic `runtime_gate` | The target deploys, runs, and stays stable; logs are clean |

The initial build gets breadth quickly; convergence makes it actually work. A deployed resource has one live state, so deploy-fix-redeploy loops must never run in parallel. Convergence waves are therefore single-session by rule (enforced by the setup notebook).

Append convergence waves to the existing manifest (keep the earlier waves for history; run the build with `only` set to the new wave task keys, or start a new run once earlier waves are already committed — passing sessions are idempotent and re-validate as "already completed").

## Workflow Modes

The manifest supports three workflow modes that control how sessions operate and how integration works:

| Mode | Sessions write to | Integrator commits | Use for |
|---|---|---|---|
| `git` (default) | Files in a Git folder | Yes, by explicit path to a feature branch | Building DABs bundles, app code, any Git-tracked project |
| `workspace` | Notebooks, queries, tables, dashboards, UC objects | No Git — status collection and gates only | Data engineering, ML pipelines, migrations, infra setup, analysis |
| `hybrid` | Mix of file edits and workspace operations | Commits file edits only; workspace sessions skip Git | Projects that combine code authoring with notebook execution or SQL work |

## Top-Level Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `version` | integer | Yes | Schema version. Currently `1`. |
| `description` | string | No | Human-readable description of this project. |
| `workflow` | Workflow | No | Workflow mode and Git settings. Defaults to `{"mode": "git"}`. |
| `repo_root` | string | No | Absolute workspace path of the Git folder root. Only used in `git`/`hybrid` modes. Defaults to `build_root` if omitted. |
| `bundle_root` | string | No | Absolute workspace path of the project root. Informational; the job parameter `build_root` is the runtime authority. |
| `branch` | string | No | Default feature branch. Only used in `git`/`hybrid` modes. Informational; the job parameter `branch` is the runtime authority. |
| `bundle_target` | string | No | The DABs target for validation and deploy checks (e.g. `dev`). Required for `git`/`hybrid` modes when sessions touch bundle YAML. |
| `status_dir` | string | Yes | Directory for status and gate files, relative to `build_root`. Convention: `.build-status`. Never committed to Git. |
| `plans_dir` | string | Yes | Directory containing plan files, relative to `build_root`. Convention: `docs/plans`. |
| `sessions_dir` | string | Yes | Directory for session summaries, relative to `build_root`. Convention: `docs/sessions`. |
| `context_files` | string[] | No | Extra files (relative to `build_root`) for sessions to read before working. Project memory, coding standards, architecture docs, data dictionaries, model cards. |
| `skills` | object | No | Overrides for skill locations. See Skills section. |
| `task_retries` | object | No | Automatic retries for Genie Code tasks (sessions and integrators), for transient agent start-up errors such as `INTERNAL_ERROR: start_agent_run`. Keys: `max_retries` (default `2`; `0` disables), `min_retry_interval_seconds` (default `60`). Timeouts are never retried. Gate notebooks are not retried. |
| `runtime_targets` | map<string, RuntimeTarget> | No | Deployable things (apps, jobs, pipelines, dashboards, Genie spaces) that `converge` sessions deploy and `runtime_gate` checks. Keyed by a short target name. See RuntimeTarget. |
| `probe_auth` | ProbeAuth | No | Default service principal for app `probes` (a target's own `probe_auth` overrides it). See Probe Object. |
| `waves` | Wave[] | Yes | Ordered list of waves. Executed sequentially; sessions within a wave run in parallel. |

## Wave Object

| Field | Type | Required | Description |
|---|---|---|---|
| `wave_id` | string | Yes | Unique identifier (e.g. `0`, `1`, `4a`, `4-1`): 1-60 letters, digits, `_` or `-`. Used in task keys (`w<wave_id>_sessions`, ...) and file names. For manifests that span several builds, use `<build>-<n>` (see Archived waves). |
| `name` | string | No | Human-readable wave name. |
| `archived` | boolean | No | `true` = an earlier build's wave, kept as history. Validated (ids, duplicate session ids, modes, runtime target references) but gets **no** job tasks, skips the single-writer rule, and its sessions count as done for `depends_on`. Default `false`. See Archived waves. |
| `build` | string | No | Informational build label (e.g. `"4"`; an integer is accepted too). Not used by the runtime. |
| `concurrency` | integer | No | Max parallel sessions. Defaults to the number of sessions. |
| `manual_prereqs` | ManualPrereq[] | No | Sessions that must be done outside Genie Code before this wave runs. |
| `gate` | string[] | Yes | List of checks the integrator runs after all sessions finish. Plain text descriptions; the integrator interprets them. |
| `runtime_gate` | string[] | No | Names of `runtime_targets` the **gate notebook** checks deterministically after the integrator commits (deployment succeeded in this run, running, soak-stable, clean logs). Required on any wave with a `converge` session. A failing runtime gate fails the wave regardless of what the Genie Code tasks reported. |
| `validate_bundles` | BundleValidation[] | No | Bundles the **integrator** must run `bundle validate --strict` on for this wave, each from its own root and target: `[{"root": "infra", "target": "dev"}, {"root": "app", "target": "dev"}]`. `root` is absolute or relative to `build_root`. Results go in the gate file's `bundle_validations`; the gate notebook fails the wave if any entry is missing or not `pass`. Use this instead of free-text validate lines in `gate` when a wave touches more than one bundle. See Multiple bundles in one manifest. |
| `required_checks` | string[] | No | Names of gate checks that must run and pass, e.g. `["tsc", "vitest"]`. The integrator reports each in the gate file's `checks` under exactly this `name`; the gate notebook fails the wave when one is missing or its result is not `pass` (so `skipped` fails). Describe how to run each check (and any toolchain setup, such as installing Node) in the wave's `gate` text; the bundle does not install toolchains. |
| `timeout_minutes` | integer | No | Default task timeout for this wave's sessions. Defaults: 60 (`edit`/`execute`/`configure`), 180 (`converge`). |
| `sessions` | Session[] | Yes | Sessions in this wave. |

## Session Object

| Field | Type | Required | Description |
|---|---|---|---|
| `session_id` | string | Yes | Unique identifier (e.g. `01`, `06a`). Used in task keys and file names. |
| `title` | string | Yes | Human-readable session title. |
| `plan_file` | string | Yes | Plan file name relative to `plans_dir` (e.g. `01_bundle_scaffold.md`). |
| `scope` | string | Yes | What to do. If the plan file and this field disagree, this field wins. |
| `mode` | string | No | Session mode: `edit` (default), `execute`, `configure`, or `converge`. See Session Modes. |
| `owned_paths` | string[] | Conditional | Glob patterns (relative to `build_root`) of files this session may create/edit/delete. **Required** for `edit` and `converge` sessions in `git`/`hybrid` workflows. Not used in `workspace` mode or `execute`/`configure` sessions. |
| `owned_assets` | string[] | No | Asset identifiers this session may create or modify (e.g. notebook paths, table names, dashboard ids). For `execute`/`configure` sessions. Informational — the runner uses them for self-auditing. |
| `exclude_paths` | string[] | No | Glob patterns to exclude from `owned_paths`. |
| `allow_deploy` | boolean | No | Whether the session may run `bundle deploy`. Defaults to `false`. |
| `allow_execute` | boolean | No | Whether the session may execute notebooks or run SQL. Defaults to `false` in `edit` mode, `true` in `execute`/`configure` mode. |
| `depends_on` | string[] | No | Session ids that must be done before this session. Enforced by wave ordering, not runtime — all deps should be in prior waves (setup warns otherwise). Sessions in archived waves count as already done: no task dependency and no `.build-status` check. |
| `runtime_targets` | string[] | Conditional | **Required** for `converge`. Names of top-level `runtime_targets` this session deploys and must make stable. It may deploy only these. |
| `max_attempts` | integer | No | `converge` only. Max deploy-diagnose-fix iterations before giving up with `status: "fail"`. Default `5`. |
| `timeout_minutes` | integer | No | Task timeout for this session. Overrides the wave default. |
| `context_notes` | string | No | Free-text findings handed over from an interactive Genie Code session (known errors, log excerpts, decisions). The runner reads it as context; `scope` still wins. |

## Session Modes

| Mode | What the session does | Ownership | Git tracking |
|---|---|---|---|
| `edit` (default) | Creates, modifies, or deletes files in the project | `owned_paths` (enforced) | Files committed by integrator |
| `execute` | Runs notebooks, SQL queries, SDK calls, or CLI commands | `owned_assets` (advisory) | Not committed — output is the deliverable |
| `configure` | Configures Databricks resources (jobs, pipelines, endpoints, permissions) | `owned_assets` (advisory) | Not committed — resource state is the deliverable |
| `converge` | Deploys its `runtime_targets`, reads deployment status and telemetry, fixes code within `owned_paths`, and redeploys until stable or `max_attempts` | `owned_paths` (enforced) + `runtime_targets` | Files committed by integrator, same as `edit` |

`converge` implies `allow_deploy: true` and `allow_execute: true` for its own `runtime_targets` only.

## RuntimeTarget Object

Describes how to deploy, run, and observe one deployable resource. Used by `converge` sessions (how to deploy and where to look) and by the gate notebook (what "stable" means).

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | string | Yes | `app`, `job`, `pipeline`, `dashboard`, `genie_space`, or `table`. |
| `name` | string | Conditional | Deployed resource name as it appears in the workspace (app name, or job/pipeline/dashboard display name or Genie space title, including any dev-mode prefix). Used by the gate to look it up; a lookup that matches zero or several resources fails. Required for apps; otherwise `name` or `id`. |
| `id` | string | No | Job id, pipeline id, dashboard id, or Genie space id. Preferred over `name` lookup; strongly recommended for Genie spaces (titles are not unique, setup warns without it). |
| `bundle_root` | string | No | Absolute workspace path of the bundle that defines the resource. Defaults to `build_root`. |
| `bundle_target` | string | No | Target to deploy. Defaults to top-level `bundle_target`. |
| `resource_key` | string | No | Bundle resource key (e.g. `trading_agent_app`), used for `bundle run <resource_key>`. For `genie_space` targets also used to find the space's source file (`resources.genie_spaces.<resource_key>.file_path` in the bundle YAML that `databricks.yml` includes) for the freshness content match. |
| `source_file` | string | No | `genie_space` only. The space's bundle source file (`*.geniespace.json`), relative to `bundle_root`. Overrides the `resource_key` lookup. Without either, a no-op deploy fails freshness (setup warns). |
| `deploy_commands` | string[] | No | Databricks CLI commands (without the `databricks` prefix) run from `bundle_root`, in order, to deploy and start the target. Default for apps: `bundle deploy --target <t>` then `bundle run <resource_key> --target <t>` (plain deploy does not redeploy app code when config is unchanged). Default for dashboards and Genie spaces: `bundle deploy --target <t>` only. |
| `telemetry` | Telemetry | No | Where logs land and how to judge them. Strongly recommended for apps. |
| `stability` | Stability | No | Soak and error budget. |
| `require_fresh_deployment` | boolean | No | Gate requires the active deployment / run / update / published dashboard revision / Genie space `update_time` to be after the build job run started. Default `true`. Genie spaces: fresh = `update_time` after the run started, **or** current = the deployed space equals its bundle source (`source_file` / `resource_key`) after normalisation, so a no-op deploy passes. Without a source to compare, an old `update_time` fails the gate; a source that uses per-target `${var...}` substitution never matches (use `false` for such a space). |
| `warehouse_id` | string | No | `dashboard`: warehouse for the dataset checks (defaults to the published dashboard's). `genie_space`: the warehouse the space must use; the gate fails on a mismatch. |
| `check_example_sql` | boolean | No | `genie_space` only. `EXPLAIN` every example SQL (`instructions.example_question_sqls`) on the space's warehouse. Default `true`. Parameterized examples are reported `skipped`. |
| `sql_timeout_seconds` | integer | No | `genie_space` only. Per-statement timeout for example SQL. Default `120`. |
| `required_columns` | string[] | No | `table` only. Columns that must exist (case-insensitive). |
| `min_rows` | integer | No | `table` only. Minimum `COUNT(*)`. Unset = not counted. |
| `probe_questions` | string[] | No | `genie_space` only. Questions the gate asks after the static checks pass, each in a new conversation, one retry. Pass = Genie generated SQL and it ran (`SUCCEEDED`); the answer itself is never judged. Use questions the space should always be able to answer ("How many bookings were there in total?"). The conversations stay in the build identity's Genie history. |
| `probe_mode` | string | No | `genie_space` only. `warn` (default): failing questions are recorded under `warnings` in the gate output and `wave_<N>_runtime.json` without failing the wave. `fail`: they fail it. |
| `probe_timeout_seconds` | integer | No | `genie_space` only. Per-question wait. Default `120`. Each question adds `2 × timeout` to the gate task timeout. |
| `execute_datasets` | boolean | No | `dashboard` only. `false` (default): validate each dataset query with `EXPLAIN` (no data scanned). `true`: run `SELECT * FROM (<query>) LIMIT 1`, which also catches runtime errors. |
| `dataset_timeout_seconds` | integer | No | `dashboard` only. Per-dataset statement timeout. Default `120`. |
| `probes` | Probe[] | No | `app` only. Authenticated HTTP requests the gate sends at the start of the soak, as the `probe_auth` service principal. Use for custom agents and MCP servers, where `RUNNING` alone does not prove the agent answers. |
| `probe_auth` | ProbeAuth | No | `app` only. Service principal for this target's probes. Overrides the top-level `probe_auth`. |

Dashboards deploy with `bundle deploy` alone (deploy publishes them), so `deploy_commands` defaults to `bundle deploy --target <t>` and `resource_key` is not needed.

### Telemetry Object

| Field | Type | Description |
|---|---|---|
| `logs_table` | string | UC table with OpenTelemetry logs (e.g. the app's `telemetry_export_destinations` logs table). Expected OTel columns: `time`, `date`, `severity_text`, `body` (variant), `attributes` (variant). |
| `deployment_id_attribute` | string | Attribute key holding the app deployment id. Default `app.deployment_id`. |
| `log_source_attribute` | string | Attribute key distinguishing build vs runtime logs. Default `app.log_source` (values seen: `BUILD`, `SYSTEM`, `APP`). |
| `error_patterns` | string[] | Regexes (matched against `body`) that count as errors in addition to `severity_text IN ('ERROR','FATAL')`. Default: `error TS\\d+`, `Error building app`, `Unhandled`, `UnhandledPromiseRejection`, `FATAL`, `"level":"(error|fatal)"`. |
| `ignore_patterns` | string[] | Regexes for known-benign lines to exclude from the error count. Default: `App did not respect SIGTERM timeout`, `[ELIFECYCLE]` (old-deployment shutdown noise during redeploy). Add project-specific lines (e.g. `Updated file:`). |
| `required_markers` | string[] | Regexes that must each match at least one runtime log line for the active deployment (e.g. `listening on`, `pollers started`). |
| `traces_table` | string | UC table with OpenTelemetry spans (columns `time`, `date`, `service_name`, `kind`, `trace_id`, `status.code`), e.g. the app's `*_otel_spans` table. A trace source for `min_traces` / `max_trace_errors`. |
| `mlflow_experiment_id` | string | MLflow 3 experiment the app (or agent) logs traces to. The other trace source: counted with `mlflow.search_traces` on trace metadata only (`trace.timestamp_ms >=` probe time, no span download). Error traces = state `ERROR`. |
| `mlflow_trace_filter` | string | Extra MLflow trace filter ANDed onto the time filter (e.g. `tags.app = 'my-agent'`), for experiments shared by several apps. |
| `trace_service_name` | string | `service_name` of the app's spans. Default: the app name. |
| `trace_span_kinds` | string[] | Span kinds that count toward `min_traces`. Default `["SPAN_KIND_SERVER"]` (inbound requests). Apps also emit periodic `SPAN_KIND_CLIENT` spans for their own telemetry export, so counting every kind passes an app that served nothing. `[]` counts all kinds. |

### Stability Object

| Field | Type | Description |
|---|---|---|
| `soak_minutes` | integer | How long the gate watches the target after it is up. During the soak the app must stay `RUNNING` with the same active deployment. Default `10`. |
| `max_errors` | integer | Error-line budget for the active deployment. Default `0`. |
| `min_traces` | integer | `app` only. Minimum traces since the probes ran (or since the deployment, without probes), in each configured trace source (`telemetry.traces_table` and/or `telemetry.mlflow_experiment_id`). OTel spans carry no deployment id, so they are scoped by `trace_service_name` and time. Pair with `probes`: an idle app emits no request spans. |
| `max_trace_errors` | integer | `app` only. Error-trace budget over the same window and sources: OTel traces with any span `status.code = STATUS_CODE_ERROR` (any kind), MLflow traces in state `ERROR`. Unset = errors are reported in `wave_<N>_runtime.json` but don't fail the gate. |
| `traces_wait_minutes` | integer | How long after the soak the gate keeps polling for `min_traces` (span ingestion lag). Default `5`. |
| `max_failed_records` | integer | `pipeline` only. Budget for expectation violations in the checked update: the sum of `failed_records` over every expectation (`expect` warnings and `expect_or_drop` drops; `expect_or_fail` already fails the update). Failing expectations are listed by name in the gate output and `wave_<N>_runtime.json`. Unset = not checked. |
| `max_dropped_records` | integer | `pipeline` only. Budget for records dropped by `expect_or_drop` in the checked update. Unset = not checked. |

### Probe Object

| Field | Type | Description |
|---|---|---|
| `path` | string | Required. Path on the app, starting with `/` (e.g. `/api/health`). The host always comes from `w.apps.get(name).url`; a full URL is rejected by setup. |
| `method` | string | `GET` (default), `POST` or `HEAD`. |
| `json` | object | Optional JSON request body. |
| `expect_status` | integer or integer[] | Accepted status codes. Default `200`. |
| `response_regex` | string | Regex the response body must match. |
| `mcp_initialize` | boolean | Send an MCP JSON-RPC `initialize` (POST, `Accept: application/json, text/event-stream`). Passes when the reply (JSON or SSE) has `result.serverInfo`. |
| `timeout_seconds` | integer | Per-request timeout. Default `30`. |

### ProbeAuth Object

| Field | Type | Description |
|---|---|---|
| `secret_scope` | string | Databricks secret scope holding the service principal's OAuth credentials. |
| `client_id_key` | string | Key of the SP's application (client) id. |
| `client_secret_key` | string | Key of the SP's OAuth secret. |

Probes authenticate as that service principal (OAuth M2M: a `WorkspaceClient(client_id, client_secret)` and its `config.authenticate()` headers). The SP needs `CAN_USE` on the app; the build job's run-as identity needs `READ` on the scope. Setup fails if the scope or either key is missing (it lists key names only, never values). `probe_auth` is **required** for probes (setup fails without it): Apps accept only OAuth tokens, and a job's own credential is redirected to sign-in even when that identity has `CAN_MANAGE` on the app (verified from job runs). Redirects are not followed: a redirect to sign-in is reported as "credentials not accepted" (in practice: the SP has no `CAN_USE`, which also returns a redirect, not a 403), a 401/403 as missing access, a rejected client secret as `invalid_client` before any request. A failing probe is retried once after 10 seconds (cold start). The smoke job's `app_probe_check` task runs the same probes with the same `probe_auth` from a job and checks that every configured trace source is readable and that the job can read every `genie_space` target's configuration (`CAN_EDIT`; a space not created yet is `skipped`), so run `setup_build_waves` with `run_smoke=true` once the app is up, before relying on probes in a build.

### What the runtime gate checks

| Type | Checks |
|---|---|
| `app` | Active deployment `SUCCEEDED` and (if fresh required) created after the build run started; no pending deployment; `app_status` `RUNNING` and `compute_status` `ACTIVE`; unchanged through the soak; error lines for the active deployment ≤ `max_errors`; every `required_markers` regex matched. With `probes`: every probe passes at the start of the soak. With `min_traces` / `max_trace_errors`: enough traces, and no more error traces than allowed, since the probes ran, in the OTel spans table and/or MLflow 3 experiment. |
| `job` | Latest run started after the build run started is `TERMINATED` / `SUCCESS`. |
| `pipeline` | Latest update started after the build run started is `COMPLETED` (or `RUNNING` for continuous pipelines through the soak). With `max_failed_records` / `max_dropped_records`: the update's `flow_progress` data quality metrics, summed over flows and micro-batches, stay within the limits. Metrics come from the pipeline's Unity Catalog event log table when it publishes one (`event_log` in the pipeline spec; the build identity needs `SELECT` on it), else from the events API. |
| `dashboard` | Published, with the published revision created after the build run started; a warehouse is set; every dataset resolves. Query datasets: `EXPLAIN` (default; a plan containing `Error occurred during query planning` fails even though the statement succeeds) or `LIMIT 1` execution with `execute_datasets`, using the dataset's `catalog`/`schema` and default parameter values. Datasets with multi-value or range parameters are reported as `skipped`. Table / metric view datasets (`asset_name`) must resolve in Unity Catalog. No soak. |
| `genie_space` | Static checks first. Freshness: `update_time` after the build run started (`fresh`), or the deployed serialized space equals the bundle source after normalisation (`current`: line arrays joined, `data_sources.metric_views` merged into `tables`, object lists sorted by `id` / `identifier` / `column_name` / `name`); otherwise `stale` with the first differing paths, or `timestamp only` when no source is found. The result is in the target's `freshness` entry. A warehouse attached and existing (equal to `warehouse_id` if set); at least one table; every table / metric view in `data_sources.tables` resolves in Unity Catalog; every `column_configs` column still exists in its table (catches configs left behind by renamed or dropped columns); every example SQL passes `EXPLAIN` on the space's warehouse. SQL snippets (measures, filters) are fragments and are only counted. Reading the configuration needs `CAN_EDIT` on the space for the build job's identity. Then `probe_questions`, if set (skipped when a static check other than freshness failed; when only freshness failed they still run and are reported, advisory): Genie must generate SQL that runs; an off-topic answer with no SQL, a failed query or a timeout fails the question. No soak. |
| `table` | `name` (`catalog.schema.table`) resolves in Unity Catalog (table, view, materialized view, streaming table, metric view, foreign table); every `required_columns` exists; `COUNT(*) >= min_rows`; with `require_fresh_deployment` (default `true`), written during this run: last Delta commit (`DESCRIBE HISTORY`) for tables and streaming tables, last refresh for materialized views. Views, metric views and foreign tables have no data commits: freshness is skipped. Not deployed: an `execute` session writes it, so a `table` target can sit in any wave's `runtime_gate`, without a `converge` session. Replaces free-text gate lines like "table has > 0 rows". No soak. |

### Multiple bundles in one manifest

One root-level manifest can drive several bundles (for example an infra bundle and an app bundle in the same repo):

* Static gates: list each bundle in the wave's `validate_bundles` with its own `root` and `target`. The integrator validates each one; the gate notebook checks every entry was reported as `pass`.
* Deploys: give each runtime target its own `bundle_root` and `bundle_target`. A `converge` session deploys each target from that target's bundle.
* Deploy order across bundles is wave order: put the infra target's `converge` wave before the app's.

## ManualPrereq Object

| Field | Type | Required | Description |
|---|---|---|---|
| `session_id` | string | Yes | Identifier for the prerequisite. |
| `title` | string | Yes | Description. |
| `plan_file` | string | No | Reference plan file. |
| `done_when` | string | Yes | Condition the integrator checks to verify completion (e.g. "file X exists on the branch"). |

## Workflow Object

| Field | Type | Required | Description |
|---|---|---|---|
| `mode` | string | No | `git` (default), `workspace`, or `hybrid`. Controls Git guardrails and integration behavior. |

When omitted, the entire `workflow` object defaults to `{"mode": "git"}`.

## Skills Object (optional)

Overrides the default skill locations. If omitted, the setup notebook uses its own bundled skills.

| Field | Type | Description |
|---|---|---|
| `catalog` | string | UC catalog for publishing skills. |
| `schema` | string | UC schema for publishing skills. |
| `runner` | `{skill_id, folder}` | Runner skill: UC skill id and workspace folder containing `SKILL.md`. |
| `integrator` | `{skill_id, folder}` | Integrator skill: UC skill id and workspace folder containing `SKILL.md`. |

## Design Rules

1. **No path overlap within a wave.** In `git`/`hybrid` modes, two `edit`-mode sessions in the same wave must not have overlapping `owned_paths`. This prevents merge conflicts when sessions run in parallel.
2. **No asset overlap within a wave.** In any mode, two sessions in the same wave should not modify the same assets. Use `owned_assets` to document boundaries.
3. **Dependencies across waves only.** `depends_on` references sessions in prior waves. The wave ordering is the enforcement mechanism.
4. **Scope is king.** If `scope` and the plan file disagree, `scope` wins. The runner notes the conflict in its status file.
5. **Gates are human-readable.** Gate check descriptions are interpreted by the integrator Genie Code session. Write them as clear assertions (e.g. "bundle validate --strict --target dev passes", "table X has >0 rows", "notebook Y ran without errors").
6. **Status dir is ephemeral.** `.build-status/` is per-run. In `git`/`hybrid` modes, add it to `.gitignore`.
7. **Deploys are single-writer.** A wave that contains a `converge` session, or any session with `allow_deploy: true`, must contain exactly one session. The setup notebook rejects manifests that break this and forces `concurrency: 1`.
8. **Runtime gates are deterministic.** Every wave with a `converge` session must list its targets in `runtime_gate`. The gate notebook checks them itself; it does not trust session or integrator reports.
9. **Don't put the build job in the bundle being converged.** If a `converge` session deploys a bundle that also defines the build-waves job, the deploy resets the running build job. Keep orchestration in the genie-build-waves bundle.
10. **Archive finished builds instead of deleting them.** When a manifest gets a new build, mark the previous build's waves `"archived": true`. See Archived waves.

## Archived waves

A manifest can keep every build's waves as history. Mark finished waves `"archived": true` and add the next build's waves after them:

```json
{"wave_id": "3-6", "build": "3", "archived": true, "sessions": [...]},
{"wave_id": "4-0", "build": "4", "sessions": [{"session_id": "25", "depends_on": ["24"], ...}]}
```

* **Wave ids:** `<build>-<n>` (build number, then wave number within the build), so task keys are `w<build>-<n>_sessions`, `w<build>-<n>_integrate`, `w<build>-<n>_gate`, `w<build>-<n>_gate_check`, and status files are `wave_<build>-<n>_gate.json`. Session ids stay unique across all builds.
* **Setup:** archived waves generate no tasks. The first runnable wave starts the run (no upstream dependency), so a long history never pushes the build job toward the Jobs task limit. Setup prints `Manifest OK: N waves (A archived, R runnable), S sessions, T runtime targets`. A manifest where every wave is archived is rejected.
* **Validation:** archived waves still need unique wave ids and session ids, valid modes, and `runtime_gate` / converge `runtime_targets` that exist. The single-writer rule and the `owned_paths` warning are skipped.
* **Dependencies:** a `depends_on` entry naming an archived session is satisfied. Runners, the integrator and the gate notebook never expect `.build-status` files for archived sessions.
* **First / last wave:** the integrator's remote-branch check runs on the first **runnable** wave, and the unclaimed-carryover rule applies to the last **runnable** wave.
* Manifests without `archived` behave exactly as before.

## Use Case Examples

| Use Case | Workflow Mode | Session Modes | Example Gate |
|---|---|---|---|
| Build a DABs bundle | `git` | `edit` | `bundle validate --strict` passes |
| Build a Databricks App | `git` | `edit` + `configure` | App starts without crash |
| Make an app build/deploy stable | `git` | `converge` | `runtime_gate`: app RUNNING, soak-stable, no error logs |
| Data engineering pipeline | `workspace` | `execute` | All target tables have >0 rows |
| ML model training | `workspace` | `execute` | Model logged to MLflow with accuracy > 0.85 |
| Platform migration | `hybrid` | `edit` + `execute` | Source and target row counts match |
| Infrastructure setup | `workspace` | `configure` | All schemas, volumes, and grants exist |
| Documentation generation | `git` | `edit` | All markdown files pass lint |
| Testing campaign | `workspace` | `execute` | All test notebooks pass |
