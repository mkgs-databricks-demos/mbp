# Runtime Target Extensions

Design record for extending `runtime_targets` beyond `app | job | pipeline`. Origin: a request from another Genie Code session using the framework (2026-10-22). Decisions below were made by the framework owner.

## Status

| Phase | Scope | Status |
|---|---|---|
| 1 | `dashboard` type; wave `validate_bundles` | **Implemented** (2026-10-22) |
| 2 | `app` probes (HTTP, MCP initialize) as a `probe_auth` service principal + OTel / MLflow 3 traces (`min_traces`, `max_trace_errors`) | **Implemented** (2026-10-22); live SP auth proof to be run by a consumer project |
| 3 | `genie_space` type, static checks | **Implemented** (2026-10-22) |
| 4 | `genie_space` probe questions | **Implemented** (2026-10-22) |
| 5 | Live proof and smoke coverage: `probe_auth` service principal from a real job run; Genie space `CAN_EDIT` in the smoke job | **Implemented** (2026-10-22); accepted-SP pass path needs a `CAN_USE` grant or fresh secret |
| 6 | Pipeline data quality: expectation failures, dropped records | **Implemented** (2026-10-22) |
| 7 | `table` type: data assertions (exists, rows, columns, freshness) | **Implemented** (2026-10-22) |

Execution order: 5, 4, 6, 7. Phase 5 first because it closes the open risk in shipped work (Phases 2 and 3). Each phase is committed and pushed on its own.

## Decisions

| Question | Decision |
|---|---|
| Dashboard dataset check default | `EXPLAIN` (no data scanned). Option `execute_datasets: true` runs `SELECT * FROM (<query>) LIMIT 1`. |
| Per-wave `bundle_target` vs structured list | Structured wave field `validate_bundles: [{root, target}]` instead of a per-wave override. Runtime targets already carry `bundle_root` / `bundle_target`. |
| Genie probe questions default | `probe_mode: warn`. `fail` is opt-in. |
| Custom agents | Stay `type: app`; probes add agent-level health without a new type. Agents run only on Databricks Apps, not Model Serving, so there is no `serving_endpoint` type (owner decision, 2026-10-22). |
| Genie space / dashboard deploy default | `bundle deploy --target <t>` only, no `bundle run`. |

## Phase 1 (implemented)

**`dashboard`.** Gate notebook `check_dashboard`: published revision created after the build run started (`require_fresh_deployment`), warehouse set (target `warehouse_id` or the published one), every dataset resolves. Query datasets use the dataset's `catalog`/`schema` and single-value default parameters; multi-value/range parameters are reported `skipped`. `asset_name` datasets (tables, metric views) must resolve via `w.tables.get`. No soak; gate timeout adds 10 minutes per dashboard target.

Verified behavior that shaped the design: `EXPLAIN` on a query with an analysis error returns `SUCCEEDED` with a first row `Error occurred during query planning:` and the error on row 2 (both `spark.sql` and the Statement Execution API). A status-only check would pass broken dashboards; the gate inspects the plan text. Tested against workspace dashboards: a real stale column (`run_timestamp`) was caught in both modes.

**`validate_bundles`.** The integrator runs `bundle validate --strict --target <target>` from each entry's `root` and reports `bundle_validations` in the gate file. The gate notebook fails the wave if any declared entry is missing or not `pass` (roots compared after resolving against `build_root`). The setup notebook rejects entries without `root` and `target`.

## Phase 2 (implemented): app probes for custom agents

**As built.** Shared module `src/notebooks/app_probes.py` (used by the gate and the smoke job). Gate `check_app` runs probes after the deployment/state checks, at the start of the soak, then `check_app_traces` after the logs check. New smoke task `app_probe_check` (notebook, not Genie Code) runs every app target's probes, default `GET /`, as the job's run-as identity and fails on auth or probe failure; `skipped` when no app is running. Setup validates probe paths (no hosts), `min_traces` needs `traces_table`, and adds probe and trace-wait time to the gate timeout.

Findings that changed the plan:

* Spans carry no deployment id (resource attributes: `app.id`, `app.name`, `service.name`, `workspace.id`, process/host only). Traces are scoped by `service_name` + time since the probes.
* An idle app still emits `SPAN_KIND_CLIENT` spans every 5 minutes (its own telemetry export): 26 in 2 hours on a dev Databricks App with no traffic and zero SERVER spans. Counting every kind would pass an app that served nothing, so `trace_span_kinds` defaults to `["SPAN_KIND_SERVER"]`.
* Ad hoc HTTP to app URLs from an interactive assistant session is blocked by policy, and interactive success would not prove the job identity anyway. The smoke task is the proof.

**Revision (owner decision, same day).** Probes authenticate as an explicit service principal, not the job's run-as identity: `probe_auth: {secret_scope, client_id_key, client_secret_key}` (target or top-level) holds its OAuth M2M credentials, and the probe client is `WorkspaceClient(client_id, client_secret, auth_type="oauth-m2m")`. Setup checks that the scope and keys exist (names only). Bad credentials fail at `config.authenticate()` with `invalid_client`, which the probe reports before any request. A consumer project with a provisioned SP runs the live proof.

Trace sources: both Unity Catalog OTel spans (`traces_table`) and MLflow 3 traces (`mlflow_experiment_id`, counted with `mlflow.search_traces(locations=[id], filter_string="trace.timestamp_ms >= <ms>", include_spans=False)`, which needs no span download: under 1 s for 100 traces, versus roughly 0.5 s per trace when spans are downloaded). `max_trace_errors` adds an error budget: OTel traces with a `STATUS_CODE_ERROR` span, MLflow traces in state `ERROR`. Verified on real data: OTel SERVER 0 / all kinds 26 / 1 error span in 30 days; MLflow 100 of 200 traces after the midpoint timestamp, matching a client-side count.

Original plan:

Fields on `app` targets:

```json
"probes": [
  {"path": "/api/health", "method": "GET", "expect_status": 200, "response_regex": "ok"},
  {"path": "/mcp", "mcp_initialize": true}
],
"telemetry": {"traces_table": "cat.sch.my_app_otel_spans"},
"stability": {"min_traces": 1}
```

* ~~Probes run from the gate notebook with the build job's identity~~ (superseded: the job's credential is not an OAuth token and is redirected; see Phase 5).
* ~~Prerequisite: extend `capability_probe` to prove an authenticated app request works under a job run-as identity~~ (done as the `app_probe_check` smoke task; see Phase 5).
* Run probes at the start of the soak, then require `min_traces` spans for the deployment **since the probe time**. An idle agent emits no traces, so a trace floor without probe traffic would fail healthy apps.
* MCP: POST a JSON-RPC `initialize` with `Accept: application/json, text/event-stream`; pass = a result with `serverInfo`.

## Phase 3 (implemented): `genie_space` static checks

**As built.** Gate `check_genie_space`: `update_time` after the build run started (`require_fresh_deployment`), warehouse attached and existing (and equal to target `warehouse_id` if set), at least one table, every `data_sources.tables[].identifier` resolves via `w.tables.get` (metric views included), every `column_configs[].column_name` still exists in its table, every `instructions.example_question_sqls` passes `EXPLAIN` on the space's warehouse (`check_example_sql`, default on; parameterized examples `skipped`). SQL snippets (measures, filters) are only counted: they are fragments with no table context. Setup accepts the type, warns without `id`, validates `check_example_sql`, warns that `soak_minutes` is ignored, and adds 10 minutes to the gate timeout.

Findings:

* The SDK `GenieSpace` model has no timestamps (only `etag`), but the raw `GET /api/2.0/genie/spaces/<id>` returns `create_time` and `update_time`. On a scratch space (created, then trashed), `update_time` moved on a `serialized_space` update, a description-only update and an identical re-write. So it reliably means "written since"; a wave that may not re-write the space needs `require_fresh_deployment: false`.
* `serialized_space` requires `CAN_EDIT` (SDK docstring). The gate reports a missing grant as such.
* Titles are not unique in practice (two "Healthcare Encounter Analytics" spaces in this workspace). **Deviation:** instead of requiring `id`, a `name` must match exactly one title (paged `list_spaces`), as for dashboards; setup warns without `id`.
* The `column_configs` check found real drift in 2 of 10 workspace spaces (configured columns that no longer exist, confirmed with `DESCRIBE TABLE`). Example SQL on metric views (`MEASURE(...)`) passes `EXPLAIN`: 15/15 and 4/4 on two real spaces; a wrong measure name and an unknown column fail with the planner's suggestion.
* Open: the smoke job's capability probe does not yet check `CAN_EDIT` on the manifest's spaces.

Original plan:

* Require `id` (space titles are not unique; a name lookup must match exactly one).
* Checks: warehouse attached, every referenced table and metric view resolves in UC.
* "Deployed in this run": needs a reliable timestamp on the space. Verify what the Genie space API exposes before committing to this check; fall back to `require_fresh_deployment: false` if it has none.
* Deploy default: `bundle deploy` only.

## Phase 4 (implemented): `genie_space` probe questions

**As built.** `check_genie_space` asks each `probe_questions` entry after the static checks pass (skipped otherwise) via `start_conversation_and_wait`, one retry in a new conversation. Pass = message `COMPLETED`, a query attachment, and `get_message_attachment_query_result` reports `SUCCEEDED`. `warn` failures go to the target's `warnings` (printed, and in the gate result and `wave_<N>_runtime.json`); `fail` adds them to the problems. Setup validates the fields and adds `2 × probe_timeout_seconds` per question to the gate timeout.

Findings (a real dev Genie space):

* A data question took 13 to 25 s and produced a `MEASURE()` query over the metric view; the attachment carries `statement_id` and `query_result_metadata.row_count`, and the result endpoint returns `SUCCEEDED`.
* An off-topic question completes in about 5 s with status `COMPLETED` and only a text attachment. Status alone would pass it, so the query attachment is required.
* A short timeout raises `TimeoutError` (`current status: ASKING_AI`), reported as a failure.
* Deleting probe conversations was not attempted by the gate: it is a destructive call, and leaving them is harmless (they are in the build identity's history only).

Original plan:

```json
"probe_questions": ["How many orders last week?"],
"probe_mode": "warn",
"probe_timeout_seconds": 120
```

* Pass = the Conversation API produced a SQL query and it ran successfully within the timeout. Never judge answer correctness (LLM output is not deterministic).
* One retry per question. `warn` records failures in `wave_<N>_runtime.json` without failing the wave; `fail` fails it.
* Add each question's timeout to the gate task timeout.

## Phase 5 (implemented): live proof and smoke coverage

**As built.** Smoke `app_probe_check` also checks each `genie_space` target (`pass` / `fail` on no `CAN_EDIT` / `skipped` if not created yet) and only probes apps that have `probes` or `probe_auth`. `probe_auth` is now required for probes: `probe_client` raises without it, and setup rejects `probes` without it. Secret read errors are cut to one line.

Live proof, one-time serverless job runs of `app_probe_check` against a dev Databricks App (manifests kept in the git-ignored `.scratch/`):

| Case | Result |
|---|---|
| Job identity (`CAN_MANAGE` on the app), no `probe_auth` | 302 to sign-in. **The job-identity fallback cannot work**: Apps accept only OAuth tokens, a job's runtime credential is not one. Fallback removed. |
| SP with valid OAuth secret, no `CAN_USE` | Token issued, then 302 to sign-in (not 403). Message now names both causes. |
| SP whose stored secret was rotated | `invalid_client` before any request |
| Missing secret key | One-line `Secret does not exist` error |
| Genie space by id, by title; space not created yet | pass, pass, skipped |
| App without probes; OTel traces and logs tables | pass (not probed); both readable |

Open: an accepted request (200) as a service principal. The only scoped SP with `CAN_USE` on a running app has a stale secret; proving it needs a `CAN_USE` grant to a scoped SP or a fresh secret (owner's call).

Original plan:

* Run the smoke job for real with a manifest whose app target has `probes` and `probe_auth`, and record the result (pass, or the exact failure and fix).
* Smoke `app_probe_check` also checks every `genie_space` target: the space resolves, and `get_space(include_serialized_space=True)` works as the job identity (the gate needs `CAN_EDIT`). `fail` on a missing grant, so the build doesn't discover it at the gate.

## Phase 6 (implemented): pipeline data quality

**As built.** `check_pipeline` reads the checked update's `flow_progress` data quality (only when a limit is set) through `_pipeline_data_quality`: from the pipeline's UC event log table if `spec.event_log` is set (parameterized SQL on `origin.update_id`), else `list_pipeline_events(filter="update_id = '...'")`. It sums `dropped_records`, `warned_records` and per-expectation `failed_records`, and lists failing expectations by count. Setup validates the limits.

Findings (28 pipelines in the workspace):

* The events API filter rejects `event_type = ...` and `event_type IN (...)` ("operation not allowed"); `update_id = '...'` works. Event type is filtered client-side.
* Pipelines that publish their event log to UC returned no events from the API and no updates from `list_updates` (old updates), while their tables keep full history. The table is the durable source.
* `data_quality` is `{dropped_records, warned_records, expectations?}`; `expectations` appears only on flows that define them. Batch flows report once, on the `COMPLETED` event, so summing is correct.
* `warned_records` counts rows, `failed_records` counts rule hits: one flow had 29 warned rows and 131 failed records across 5 rules. The budget is on `failed_records`.
* Real update (`ncpdp_segments_etl`, warn-only expectations): 145 failed records over 11 expectations, equal to an independent `explode` sum. `max_failed_records: 0` fails with the top rules named; `200` passes.
* Not verified: an events API update that contains expectation metrics (no such update in this workspace).

Original plan:

Fields on `pipeline` targets, under `stability`:

```json
"stability": {"max_failed_records": 0, "max_dropped_records": 100}
```

* Read the checked update's `flow_progress` events from the pipeline event log: `data_quality.dropped_records` and `data_quality.expectations[].failed_records`, summed per flow and expectation. Only checked when a limit is set.
* Report per-expectation counts in `wave_<N>_runtime.json`, so the converge session sees which rule failed. `expect_or_fail` violations already fail the update.

## Phase 7 (implemented): `table` data assertions

**As built.** `check_table`: `w.tables.get`, `required_columns` against UC columns, `COUNT(*)` on the notebook's serverless Spark (no warehouse needed, unlike the plan), and freshness from `_table_last_write`. Setup validates `catalog.schema.table`, `required_columns`, `min_rows`; gate timeout +10 min. `examples/workspace-waves.json` now gates its tables with `runtime_gate` instead of free-text "> 0 rows" lines.

Findings (one object of each type in this workspace):

| Type | `DESCRIBE HISTORY` | Freshness source used | `COUNT(*)` |
|---|---|---|---|
| `MANAGED` (Delta) | works | last commit | 3 s / 42K rows |
| `STREAMING_TABLE` | works (`STREAMING UPDATE`) | last commit | under 1 s |
| `MATERIALIZED_VIEW` | fails ("is a view") | `DESCRIBE EXTENDED ... AS JSON` `refresh_information.last_refreshed_at` | under 1 s |
| `VIEW`, `METRIC_VIEW` | fails ("is a view") | none: skipped | works (metric view: 50K rows) |
| `FOREIGN` (Postgres) | fails (Delta only) | none: skipped | 8 s |

* History timestamps read through `unix_millis(timestamp)` match UC `updated_at` to the second, so no time zone drift.
* 11 cases pass as expected: fresh and stale for Delta, streaming table and MV against two run starts; view and metric view freshness skipped; missing column; `min_rows` too high; table not found.

Original plan:

For `workspace`-mode builds, whose output is tables rather than deployments. Replaces free-text gate lines like "table has > 0 rows".

```json
"features": {"type": "table", "name": "cat.sch.features", "min_rows": 1,
             "required_columns": ["customer_id", "score"], "require_fresh_deployment": true}
```

* Resolves via `w.tables.get` (tables, views, materialized views, streaming tables). `required_columns` must be present. `min_rows` runs `COUNT(*)` on a warehouse (`warehouse_id` required when set). Freshness: the last Delta commit (`DESCRIBE HISTORY ... LIMIT 1`) after the build run started; views have no history, so freshness is skipped for them.
* Not deployed by `bundle deploy`: an `execute` session writes it. Usable in `runtime_gate` of any wave, without a converge session.

## Files touched by each new type

`VALID_TARGET_TYPES` and validation (setup notebook), a `check_<type>` function and the `checkers` map (gate notebook), deploy/wait/diagnose defaults (runner skill), capability probe, `manifest-schema.md`, README, an example.
