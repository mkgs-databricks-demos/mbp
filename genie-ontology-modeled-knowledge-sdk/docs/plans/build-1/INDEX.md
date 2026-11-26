# Build-1 Plan Index

## Overview

Build 1 turns the build-0 SDK into something a customer can install and run, and makes tuning exhaustive. It merges the owner-accepted [requests R1-R9](REQUESTS.md) with the [build-0 observations](../../build-0-observations.md) and adds an exhaustive tuning protocol and an independent final evaluation (owner request, 2026-11-25).

* **Manifest:** [`docs/plans/waves.json`](../waves.json). Build-0 waves `0-0`..`0-10` stay as history with `"archived": true`; build-1 waves are `1-0`..`1-17` plus `1-2b` with `"build": "1"`, sessions `18`-`45` plus `23b`. `validate_manifest` and `validate_authorizations`: 0 errors, 0 warnings (172 job tasks).
* **Workflow:** `hybrid`; `build_root` = this SDK folder; top-level `branch` = the build-1 feature branch.
* **Executor:** Devin as the external monitor at **level 4, as autonomous as possible** (owner, 2026-11-25). The manifest is written so Devin rarely needs the owner: every side effect a session needs is an explicit owner `authorizations` entry, `authorization_policy.monitor_may_authorize` lets Devin grant `jobs.run_now`, `bundle.deploy`, `volume.write`, `workspace.write`, `sql.ddl` and `uc_skills.publish` on a session's own `owned_assets`, accuracy thresholds are recorded rather than gated where a miss is not a defect, and conditional tuning waves avoid manifest edits. Devin still stops on the monitor skill's stop conditions and on the `manual_prereqs` below.
* **SDK schema (owner decision 2026-11-25):** the SDK itself is set up as a bundle at `build_root` with a **schema resource**. SDK setup asks which catalog and schema to use and recommends a new schema the bundle creates. That single schema holds the published skills, the `sdk_wheels` volume and build-only `scratch_*` pattern-check views. Session 18 deploys it in wave 1-0; later sessions resolve it with `databricks bundle summary -t dev` at `build_root`.
* **Workspace-specific values** live only in gitignored files and in `docs/sessions/`: the SDK bundle overrides (`sdk_catalog`, `sdk_schema`, `sdk_consumer_group`, `warehouse_id`), the TPC-H overrides, and `.local/build-1.json` (`pages_domain_id`, later `customer_path_root`).

## Wave Map

| Wave | Name | Sessions (mode) | Requests / observations closed |
|---|---|---|---|
| 1-0 | CI, dependency floor & SDK bundle bootstrap (deploy) | 18 (edit, allow_deploy) | R5, R7, R7a (SDK bundle with schema + `sdk_wheels` volume); obs "08: /tmp pytest copy skips validate_manifest" |
| 1-1 | Library & template defects, benchmark library | 19, 20, 21, 22 (edit) | R4.1-R4.4; obs 8 (helper), 21, 22, 24, 25, 27, 28, 29, 31; obs "06: warehouse_id unused" |
| 1-2 | Wheel & reconciled skills | 23, 24, 25, 26 (edit) | R2 (entry points), R7a (code: versioning, SDK bundle `artifacts`, wheel-first templates, opt-in vendoring, CI on the installed wheel), R8; obs 1-20, 23, 26 |
| 1-2b | SDK wheel publish (deploy) | 23b (edit, allow_deploy) | R7a (deploy the SDK bundle: wheel built and uploaded to the UC volume, `sdk_smoke` run) |
| 1-3 | Skills publishing | 27 (edit) | R1 |
| 1-4 | Run kit & guided setup notebook | 28, 29 (edit) | R3, R6; obs "09: gate grep", "09: main default"; owner item "run approvals" |
| 1-5 | TPC-H metric view refresh (deploy) | 30 (edit, allow_deploy) | R7a dogfood (TPC-H on the wheel, identical DDL), obs 30, R4.4 |
| 1-6 | TPC-H draft Pages & benchmark authoring | 31, 32, 33, 34 (edit) | owner item "Pages need a domain" (13); exhaustive benchmark |
| 1-7 | Tuning baseline (deploy) | 35 (edit, allow_deploy) | exhaustive tuning |
| 1-8 | Tuning iteration 1 (deploy) | 36 | tuning plan 01 |
| 1-9 | Tuning iteration 2 (deploy) | 37 | tuning plan 02 |
| 1-10 | Tuning iteration 3 (deploy) | 38 | tuning plan 03 (third required plan) |
| 1-11 | Tuning iteration 4, conditional | 39 | runs only until the asymptote |
| 1-12 | Tuning iteration 5, conditional | 40 | runs only until the asymptote |
| 1-13 | Tuning iteration 6, conditional + asymptote gate | 41 | asymptote must be reached |
| 1-14 | Independent report simulation (final evaluation) | 42 (edit) | owner request |
| 1-15 | Customer path preparation | 43 (edit) | R9 |
| 1-16 | Customer path run report | 44 (edit) | R9 (after the owner-run child build) |
| 1-17 | Build-1 docs & observations | 45 (edit) | wrap-up |

Waves run in order; sessions in one wave run in parallel. Deploying waves (1-0, 1-2b, 1-5, 1-7..1-13) have exactly one session (single-writer rule).

### Why this order

The owner's priority order is R1..R9. Build order follows dependencies, as in the [REQUESTS sequencing table](REQUESTS.md#sequencing):

1. R5 + R7 first: lint, types and the SDK floor are needed to build and test everything else (R7's floor must include the skills API that R1 uses).
2. R4 next, with the benchmark library: R2 and R4 both change `scaffold.py` and the metric-views template.
3. R2 + R7a (wheel distribution, owner decision 2026-11-25: ship both, wheel by default, vendoring opt-in) in parallel with R8; R7a needs R5 and R7 from wave 1-0. A single-session wave 1-2b then publishes the wheel, so every later install (skills publisher, guided notebook, TPC-H, the R9 child project) uses it. R1 must publish the reconciled skills, so R8 comes before R1.
4. R1, then R3 + R6, which consume R1 (skill ids) and R4 (resolved target).
5. TPC-H refresh, exhaustive tuning and the report simulation use the fixed SDK.
6. R9 last, on a second domain, through the run kit that now contains the exhaustive tuning protocol.

## Exhaustive tuning protocol (owner request)

Defined in `skills/ontology-tuning` and `docs/design/tuning-protocol.md` (session 26), implemented in `benchmark.py` (session 22), used by sessions 32-41 and shipped in the run kit (session 28).

| Rule | Value |
|---|---|
| Benchmark size per agent | 100-498 questions (Genie allows 500 benchmark questions per agent) |
| Coverage | every metric view >= 12 questions; every measure and every dimension at least once; >= 25% of questions need two or more metric views; question types `simple`, `breakdown`, `time`, `filter`, `ratio`, `synonym`, `edge`, `cross_view` |
| Expectations | every question has tokenized `expected_sql` (`MEASURE()` over the metric views) that ran `SUCCEEDED` |
| Holdout | a deterministic 20% split (`benchmark.assign_splits`, hash of the question id); tuning sessions never read holdout failures |
| Evaluation | Genie benchmark evaluation runs (`/api/2.0/genie/spaces/{id}/eval-runs`) with the questions loaded into the agent's benchmarks; fallback: `benchmark.run_benchmark` with bounded concurrency and 429 backoff |
| Fix ladder (MV-first) | 1 metric view `comment`; 2 `synonyms`; 3 `display_name`; 4 `format`; 5 measure/dimension expression or `FILTER`; 6 new measure or dimension; 7 join fix or moving a measure to the right-grain view; 8 glossary term + draft UC Page. Only after all apply-able steps are recorded as tried for that failure: 9 one agent text instruction; 10 one example SQL (multi-step questions only). Never an instruction that restates metric view metadata |
| Tuning plans | each iteration applies `tuning_plan_<k>.md` and writes `tuning_plan_<k+1>.md`; at least three plans (01-03) must be applied |
| Stop rule (asymptote) | after >= 3 applied plans: tuning-split accuracy gained < 1.0 percentage point in each of the last 2 iterations, or reached 100%; and holdout accuracy is within 2.0 points of its best. Iterations 4-6 run only until the rule is met; wave 1-13 fails if it is not met by iteration 6 (owner decides whether to append iterations) |
| Final evaluation | session 42, independent of tuning: 4-5 report personas, 8-15 turns each in one Genie conversation, graded against pre-registered ground truth on the **source tables**. Target 80% overall, recorded (below target becomes a backlog item) |

## Cross-session contracts

| Contract | Producer | Consumers |
|---|---|---|
| SDK schema: the SDK bundle's schema resource (catalog and schema from SDK setup; dev-prefixed in development mode), resolved with `bundle summary`; holds the six skills, the `sdk_wheels` volume and `scratch_*` views | owner answers (P1-8), 18 (deploy) | 23, 23b, 25, 27, 29 |
| `.local/build-1.json` (gitignored): `pages_domain_id`; later `customer_path_root` | owner (P1-2, P1-6) | 31, 36-41, 44 |
| `resolved_target.json`: `{"catalog", "schema", "warehouse_id", "source": "bundle_summary", "resolved_at"}`; written by `targets.resolve_target(bundle_dir, target)` | 21 (code), 30 (TPC-H file at `examples/tpch/docs/registration/`) | 19 (`geniespace render --params`), 28, 29, 35 |
| `geniespace.build_space(..., benchmarks=...)` / `validate_space` accept a benchmarks section of at most 500 questions in the serialized-space format (verify the field names on an exported space) | 19 | 22 (`benchmark.to_space_benchmarks` returns that shape), 35 |
| `benchmark` API: `load_question_set(dir)`, `coverage(questions, mv_yaml_paths) -> CoverageReport`, `assign_splits(questions, holdout=0.2)`, `to_space_benchmarks(questions)`, `run_eval(space_id, ws, question_ids=None)`, `score(results)` (adds `unit_mismatch`), `append_history(path, entry)`, `asymptote(history) -> {reached, reason, ...}`; constants `MIN_QUESTIONS=100`, `MAX_QUESTIONS=498`, `MIN_PER_VIEW=12`, `MIN_CROSS_VIEW_SHARE=0.25`, `HOLDOUT_SHARE=0.2`, `MIN_FIX_ITERATIONS=3`, `ASYMPTOTE_DELTA_PP=1.0`, `ASYMPTOTE_WINDOW=2`, `HOLDOUT_TOLERANCE_PP=2.0`, `MAX_FIX_ITERATIONS=6` | 22 | 26, 28, 32-42 |
| Benchmark question YAML: `{id, question, expected_sql, expected_answer?, tags: [type:<t>, view:<mv>..., measure:<m>..., dimension:<d>...], split?}`; ids prefixed by file (`s`, `f`, `x`) | 32, 33, 34 | 35-41 |
| `accuracy_history.json`: list of `{iteration, label, eval_run_id, started_at, tuning: {n, correct, accuracy}, holdout: {...}, changes: [...]}` | 35, 36-41 | `benchmark.asymptote`, gates 1-8..1-13 |
| `pages.upsert_pages(..., domain_id, status="DRAFT")` returns created/updated ids; `pages.write_terms` bulk helper | 20 | 24 (skill text), 31, 36-41 |
| Skill source note: every session summary from wave 1-4 on says whether skills loaded from Unity Catalog or the workspace folder (R1 spike evidence) | 27 | 28-45 |
| SDK wheel `genie_ontology_modeled_knowledge_sdk-<version>-py3-none-any.whl` (0.1.0), built by the SDK bundle's `artifacts.sdk_wheel` and uploaded to `workspace.artifact_path` = the SDK bundle's `sdk_wheels` volume; stable path pattern in `docs/distribution/wheel_publish.md` (CLI path, or `releases/<version>/` if the CLI path is not stable); project templates pin `sdk_version` and install `sdk_wheel` through a job environment; `vendor=False` is the scaffold default | 23 (code), 23b (publish) | 27, 28, 29, 30, 43 |

## Owned paths by wave

No two sessions in a wave share a path. Files touched in more than one wave have one owner per wave:

| File | Owners (wave) |
|---|---|
| `pyproject.toml` | 18 (1-0), 23 (1-2) |
| `databricks.yml` (SDK root), `resources/**` | 18 (1-0), 23 (1-2), 23b (1-2b) |
| `notebooks/sdk_smoke.ipynb` | 23 (1-2), 23b (1-2b) |
| `docs/distribution/**` | 18 (1-0), 23 (1-2), 23b (1-2b) |
| `README.md` | 23 (1-2, "Getting the SDK"), 45 (1-17) |
| `src/.../scaffold.py` | 21 (1-1), 23 (1-2), 27 (1-3), 28 (1-4) |
| `src/.../config.py`, `schemas/**` | 19 (1-1), 27 (1-3), 28 (1-4) |
| `templates/ontology-metric-views/**` | 21 (1-1), 23 (1-2) |
| `notebooks/init_ontology_project.ipynb` | 23 (1-2), 29 (1-4) |
| `ci/github/workflows/genie-ontology-modeled-knowledge-sdk-ci.yml` | 18 (1-0), 23 (1-2) |
| `docs/usage.md` | 29 (1-4), 44 (1-16) |
| `templates/run/**` | 28 (1-4); `templates/run/README.md` also 44 (1-16) |
| `examples/tpch/docs/tuning/**` | 35-41 (one per wave); `benchmark/**` only 32-34 (1-6) |

## Repository-root files

Sessions write only inside `build_root`. The GitHub workflows and the skills mapping belong at the repository root, so sessions write them under `ci/` (`ci/github/workflows/*.yml`, `ci/skills.yaml`) and `ci/README.md` lists the moves. The owner moves them to `.github/workflows/` and the root `skills.yaml` in the build-1 PR (default decision, 2026-11-25).

## Owner prerequisites

| Id | Before | Step | Done when |
|---|---|---|---|
| P1-1 | 1-0 | Update the instance vars file outside the repo (path in the [build-1 planning summary](../../sessions/2026-11-25_build-1-planning.md)) (`build_root`, `manifest_path` -> this folder; keep `instance_suffix`, `monitor_principal`, `monitor_job_level`), redeploy with `scripts/deploy_instance.py` from the web terminal, run setup | build job defaults point here, branch default = manifest `branch` |
| P1-2 | 1-0 | Write `.local/build-1.json` with `pages_domain_id` | file parses, is ignored |
| P1-8 | 1-0 | Answer the SDK setup questions in the SDK bundle's gitignored dev overrides: `sdk_catalog` (existing catalog), `sdk_schema` (recommended: a new schema the bundle creates, e.g. `ontology_sdk`), `warehouse_id`; readers default to the developer in `dev` (`sdk_schema_grants` / `sdk_volume_grants`, owner decision 2026-11-26). No SQL or grants: session 18's deploy creates the schema and volume, owned by the build identity, and the bundle applies the grant lists | overrides parse, catalog exists |
| P1-3 | 1-3 | Confirm the Unity Gateway skills preview is on (no schema or grants: skills go into the SDK schema) | listing skills in the SDK schema works |
| P1-4 | 1-5 | Keep consumer access at the bundle defaults (owner decision 2026-11-26: the developer in `dev`, `account users` elsewhere, via complex variables `schema_grants` / `agent_permissions` / `sdk_*_grants`; no `consumer_group` keys) and add `sdk_volume_path` (the SDK `sdk_wheels` volume path, from its bundle summary) to the metric-views one | keys present, untracked |
| P1-5 | 1-5 | Delete on the branch `examples/tpch/ontology-genie-agents/agents/ontology_agent.geniespace.json` and `examples/tpch/ontology-metric-views/src/genie_ontology_modeled_knowledge_sdk_vendored/` (TPC-H moves to the wheel) | neither in `git ls-files` |
| P1-6 | 1-16 | Child build on the second domain per `docs/customer-path/run_plan.md` (owner, or Devin with the owner's hand-off approval) | child `build_verdict.json` exists |
| P1-7 | after merge | GitHub: OIDC service principals for CI validate and skills publishing, `production` environment, branch protection; move `ci/` files to the repo root | workflows run on a PR |

Doing P1-1..P1-5 and P1-8 before the build starts lets Devin run waves 1-0..1-15 without stopping. All of these are listed in the [build-1 planning session summary](../../sessions/2026-11-25_build-1-planning.md).

## Session plans

| Session | Plan |
|---|---|
| 18 | [18_ci_and_sdk_floor.md](18_ci_and_sdk_floor.md) |
| 19 | [19_geniespace_and_config.md](19_geniespace_and_config.md) |
| 20 | [20_pages_domain_scoped.md](20_pages_domain_scoped.md) |
| 21 | [21_templates_and_scaffold.md](21_templates_and_scaffold.md) |
| 22 | [22_benchmark_library.md](22_benchmark_library.md) |
| 23 | [23_wheel.md](23_wheel.md) |
| 23b | [23b_wheel_publish.md](23b_wheel_publish.md) |
| 24 | [24_discovery_skills.md](24_discovery_skills.md) |
| 25 | [25_synthesis_curation_skills.md](25_synthesis_curation_skills.md) |
| 26 | [26_tuning_skill.md](26_tuning_skill.md) |
| 27 | [27_skills_publishing.md](27_skills_publishing.md) |
| 28 | [28_run_kit.md](28_run_kit.md) |
| 29 | [29_guided_setup.md](29_guided_setup.md) |
| 30 | [30_tpch_mv_refresh.md](30_tpch_mv_refresh.md) |
| 31 | [31_tpch_draft_pages.md](31_tpch_draft_pages.md) |
| 32 | [32_benchmark_sales.md](32_benchmark_sales.md) |
| 33 | [33_benchmark_fulfillment_procurement.md](33_benchmark_fulfillment_procurement.md) |
| 34 | [34_benchmark_cross_view.md](34_benchmark_cross_view.md) |
| 35 | [35_tuning_baseline.md](35_tuning_baseline.md) |
| 36-41 | [36-41_tuning_iteration.md](36-41_tuning_iteration.md) |
| 42 | [42_report_simulation.md](42_report_simulation.md) |
| 43 | [43_customer_path_prep.md](43_customer_path_prep.md) |
| 44 | [44_customer_path_report.md](44_customer_path_report.md) |
| 45 | [45_build1_docs.md](45_build1_docs.md) |

## Observations not changed

* Build-0 notes from session 07 (`genie_spaces` `file_path` is not interpolated; `file_path` resolves relative to the declaring YAML): platform behavior, already documented and tested. No build-1 change.
* The genie-build-waves framework items (backlog 7, 12) are tracked in genie-build-waves, not here.
