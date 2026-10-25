# Session Summaries — genie-build-waves

## 2026-10-25

| Session | Summary |
|---|---|
| [inherited-files-gate](2026-10-25_inherited-files-gate.md) | Gate and integrator credit files a rerun converge session inherits from its earlier run's status file (`session_status.py`): `files_changed` = inherited + union of attempts, inherited files must be owned; recorded as `kind: "inherited"` carryover and committed with the session. 9 new tests (41 pass); verified on AgenticTrading 35a. |

## 2026-10-24

| Session | Summary |
|---|---|
| [jobs-api-2-2-archived-waves](2026-10-24_jobs-api-2-2-archived-waves.md) | All Jobs calls on API 2.2 with full `next_page_token` paging (`jobs_api.py`), so jobs with more than 100 tasks reset safely. Wave-level `"archived": true` + `build` label (`waves_manifest.py`): validated, no tasks, archived dependencies satisfied, `<build>-<n>` wave ids with backtick-escaped gate_check references. Skills, gate, docs and 32 unit tests updated. |

## 2026-10-23

| Session | Summary |
|---|---|
| [planning-guidance](2026-10-23_planning-guidance.md) | Batch C from consumer feedback: planner now enforces one runtime_targets entry per converge session with attempt-budget guidance; migrations tip requires convergence after schema-touching edit waves; integrator checks branch exists on remote before first wave; retarget-after-merge docs in repair prompt and README. |
| [session-resilience](2026-10-23_session-resilience.md) | Batch B from consumer feedback: setup notebook now updates job parameter defaults during jobs/reset (repair_run no longer falls back to wrong values); repair prompt and README add job_parameters; runner writes provisional in_progress status file before work starts; integrator credits files to incomplete sessions instead of flagging them as strays. |
| [gate-accuracy-improvements](2026-10-23_gate-accuracy-improvements.md) | Batch A from consumer feedback: dropped ELIFECYCLE from DEFAULT_ERROR_PATTERNS, added DEFAULT_IGNORE_PATTERNS for redeploy SIGTERM/ELIFECYCLE noise, tagged error samples with match reason (severity vs pattern), added JSON level error pattern for AppKit logs. Updated runner skill, manifest schema, converge example. |
| [generic-prompt-examples](2026-10-23_generic-prompt-examples.md) | Removed project-specific `agenticTrading-follow-up-build.md`. Added three generic copy-paste prompt templates in `docs/prompts/`: `new-project.md` (initial build planning), `follow-up-build.md` (convergence waves after completed build), `repair-failed-wave.md` (re-starting from a failed wave with `repair_run` and fresh-run fallback). Updated README with a "Prompt examples" section linking to all three. |

## 2026-10-22

| Session | Summary |
|---|---|
| [runtime-gate-phases-4-7](2026-10-22_runtime-gate-phases-4-7.md) | Phases 5, 4, 6, 7. Live job runs showed Apps reject a job's own credential (302 even with `CAN_MANAGE`), so `probe_auth` is now required; the smoke checks Genie `CAN_EDIT`. Genie `probe_questions` (pass = SQL generated and ran, `warn` by default). Pipeline `max_failed_records` / `max_dropped_records` from the UC event log table or the API. New `table` target (columns, rows, freshness by type). Open: an accepted SP request needs a `CAN_USE` grant or a fresh secret. |
| [genie-space-static-checks](2026-10-22_genie-space-static-checks.md) | Phase 3: `genie_space` runtime target. Gate checks `update_time` (raw API; SDK model lacks it), warehouse, tables / metric views, stale `column_configs` (found in 2 of 10 real spaces), example SQL `EXPLAIN`. Name lookup must match exactly one space. |
| [app-probes-min-traces](2026-10-22_app-probes-min-traces.md) | Phase 2 of runtime target extensions: authenticated app `probes` (HTTP / MCP `initialize`) and `min_traces` (SERVER spans by default, because idle apps emit CLIENT export spans) in the gate notebook; shared `app_probes.py`; new smoke task `app_probe_check` proves app auth from a job (job-identity fallback later removed: Apps reject it; see runtime-gate-phases-4-7). |
| [dashboard-target-validate-bundles](2026-10-22_dashboard-target-validate-bundles.md) | Phase 1 of runtime target extensions: `dashboard` runtime target (published in this run, every dataset passes `EXPLAIN` or `LIMIT 1` with `execute_datasets`; `EXPLAIN` errors come back as SUCCEEDED rows, so the plan text is inspected) and wave `validate_bundles` (integrator validates each bundle, gate notebook checks coverage). Phases 2–4 (app probes, `genie_space`, probe questions in `warn` mode) recorded in `docs/design/runtime-target-extensions.md`. |
| [pitch-document-polish](2026-10-22_pitch-document-polish.md) | Rebuilt hero animation as Genie Code → Lakeflow Job → Genie Code three-act narrative. Replaced columnar job view with animated Gantt-style run timeline (bars fill left-to-right, parallel iterations, attempt counting, soak window). Fixed dark-mode product logos via `<picture>` + white lockup variants. Scoped `.bp-list > li` so nested bullets no longer get numbered circles. Made deploy steps 4–5 actionable with real CLI commands. Fixed `-p` → `--params` smoke-test flag in pitch and README. |

## 2026-10-21

| Session | Summary |
|---|---|
| [retries-carryover-repair](2026-10-21_retries-carryover-repair.md) | Automatic `max_retries` on Genie Code tasks for transient `INTERNAL_ERROR: start_agent_run` (manifest `task_retries`). Integrator classifies files left by earlier runs as `carryover_files` instead of strays (summaries committed, code left for its owner, unclaimed code fails the last wave). README repair guidance with `rerun_dependent_tasks`. Converge sessions re-check the branch before each deploy. |
| [converge-mode-runtime-gate](2026-10-21_converge-mode-runtime-gate.md) | Follow-up builds: sequential `converge` sessions (deploy, read OTel logs, fix, redeploy) plus a deterministic `runtime_gate` in the gate notebook, so a passing stable build is part of the pass criteria. Manifest validation (single-writer deploys), per-task timeouts, capability probe, automation leak fix, `instance_suffix` for one deployment per project. |
| [param-placeholder-fix](2026-10-21_param-placeholder-fix.md) | Root cause: automation `user_prompt` must contain `{{param}}` placeholders for Genie Code runtime substitution. Without them, agents never see resolved parameter values. Also: nonce-based smoke test for verifying the full `{{input.*}}` → `parameters` → `{{param}}` chain. |
| [if-else-cascade-and-deploy-pattern](2026-10-21_if-else-cascade-and-deploy-pattern.md) | Replaced raise-on-failure with If/else condition tasks for zero-compute cascade. Researched all six `run_if` options. Added `outcome: "true"` for condition task dependencies. Adopted `--var` deploy pattern. Enriched `for_each` inputs with session titles. |

## Commit History (branch `mg-genie-build-waves-init`)

| # | Commit | Description |
|---|---|---|
| 1 | `775a7ab` | Initial bundle: 16 files, full architecture |
| 2 | `8a23ef7` | Schema auto-creation, SDK skill publish, automation API fixes |
| 3 | `7225bb7` | `genie_task.context` → `parameters` (Jobs API field name) |
| 4 | `25aa240` | If/else gate checks for zero-compute cascade |
| 5 | `973ed14` | Add `outcome` to If/else condition task dependency |
| 6 | (refactor) | `--var` flags instead of editing `databricks.yml` |
| 7 | (fix) | Restore example placeholders in target variables |
| 8 | (feat) | Session titles in `for_each` inputs and task descriptions |
| 9 | (feat) | Nonce-based smoke test for parameter resolution |
| 10 | (fix) | `{{param}}` placeholders in automation prompts — the real root cause |
| 11 | `7df5ade` | Lava glow on hover for hero CTA buttons |
| 12 | `7836ab9` | Lava text-shadow glow on ghost button hover |
| 13 | `12459a3` | Lava glow on hover for hero product strip logos |
| 14 | `cf23dcb` | Replace static hero wave diagram with animated Genie Code session |
| 15 | `eedc294` | Hero animation: Genie Code → Lakeflow Job → Genie Code narrative |
| 16 | `efc0ae2` | Lakeflow Job run view becomes animated run timeline |
| 17 | `b20fa0d` | White product lockups in dark mode for Why Genie Code cards |
| 18 | `9f21771` | Nested bullets in Best Practices no longer get numbered circles |
| 19 | `8fc83dc` | Deploy steps 4-5 actionable; fix `-p` → `--params` smoke-test flag |
