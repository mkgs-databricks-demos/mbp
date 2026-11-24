# 2026-11-24 — Wave 0-6, Session 12: TPC-H Metric View Registration

Branch `mg-genie-ontology-modeled-knowledge-sdk` (checked read-only: Git folder is on the branch, clean). Mode: edit (`allow_execute`, `allow_deploy`). Continuation 0. This summary covers two build runs.

## Result (build run `1082430844509839`): pass

The owner authorizations for this run added `jobs.run_now` on the dogfood bundle's job. One deploy/run attempt was enough:

1. `bundle validate --strict -t dev`: Validation OK.
2. `bundle deploy -t dev`: 0 created, 0 changed, 3 unchanged (source-linked, git folder at `6c518b3`).
3. `bundle run register_metric_views -t dev --no-wait`: job `1000154254892119`, run `151387126659064` (started 1795548322877 ms, after this build run started). Ended **TERMINATED / SUCCESS** in about 3 minutes.
   * `generate_manifest` (task run `64217631895905`): 7 metric views, 0 warnings.
   * `register_each_mv` (task run `470422196940488`): forEach 7/7 iterations succeeded, 0 failed.
   * `smoke_test` (task run `809770865087506`): 7 checked, 7 passed.
   * `cardinality_test` (task run `682803942355559`): 7 checked, 0 failed.
4. Independent check, outside the job: `hls_fde_dev.information_schema.tables` for `dev_matthew_giglia_ontology` lists all 7 manifest names as `METRIC_VIEW`, and a `MEASURE()` query on the first measure/dimension of each YAML returned rows for all 7.
5. Wrote `examples/tpch/docs/registration/registration_results.md` (no resolved catalog/schema names in it).
6. Final `bundle validate --strict -t dev`: Validation OK.

Platform features from the session 11 hand-over all registered unchanged: nested joins up to 4 levels, `FILTER (WHERE ...)` measures, and `materialization:` blocks. Note: the materializations create managed materialized views, `__materialization_*` tables and `event_log_*` tables in the target schema. They belong to the metric views and go away with them.

Defects fixed: none. Template fixes for build 1: none.

## Earlier result (build run `701596191246320`): blocked

The bundle validated and deployed to `dev`. I did **not** run the `register_metric_views` job. The owner authorizations for this session list only `bundle.deploy` on this bundle (target dev). A job run (`bundle run register_metric_views -t dev`) is not on that list. The session runner skill says job runs need an explicit approval in the prompt, and that approval wording in plan files does not count. So no metric views are registered yet, and the smoke and cardinality tests have not run.

## What was done
1. Read `PROJECT_MEMORY.md`, the plan `build-0/12_tpch_mv_registration.md`, and the session 11 summary (7 metric view YAMLs + `manifest.json`). There is no `hi_genie/` folder at the build root.
2. `bundle validate --strict -t dev` (from `examples/tpch/ontology-metric-views`): **Validation OK**.
3. `bundle deploy -t dev`: **succeeded**. Created 3 resources: `schemas.ontology_schema`, `schemas.ontology_schema.grants`, `jobs.register_metric_views`. Source-linked deployment (0 files uploaded). Deployment id `975815647682859`, version 1.
4. `bundle summary -t dev` resolved IDs:
   * Job `register_metric_views` (`[dev matthew_giglia] register_metric_views`): `1000154254892119`
   * Schema: `hls_fde_dev.dev_matthew_giglia_ontology` (grant: `account users` USE_SCHEMA, SELECT)
   * Git commit at deploy: `c5aec15e6a89cc8d52378cb3f108d594a745d03c`

## Not done (blocked)
* Task 1 run step: `bundle run register_metric_views -t dev`. Not approved.
* Task 2 checks (job SUCCESS, every manifest entry exists as a metric view, `MEASURE()` smoke, cardinality): these depend on the job run.
* Task 3 `examples/tpch/docs/registration/registration_results.md`: not written, because there are no results to report. A placeholder would mislead the `mv_smoke` gate check.

## To unblock
The owner (or monitor, within the owner's policy) adds a `job.run` approval for the `register_metric_views` job of this bundle (dev, job id `1000154254892119`), then re-runs this session. Or the owner runs it by hand from the bundle folder: `databricks bundle run register_metric_views -t dev`. Then this session (or a re-run) checks the results, fixes defects in `examples/tpch/ontology-metric-views/**`, and writes `registration_results.md`.

The session 11 hand-over still applies on the first run: check that nested joins (up to 4 levels), `FILTER (WHERE ...)` measures and the `materialization:` blocks register on the platform.

## Checks
| Check | Result |
|---|---|
| Branch is `mg-genie-ontology-modeled-knowledge-sdk` | pass |
| `bundle validate --strict -t dev` | pass |
| `bundle deploy -t dev` | pass (3 created) |
| `registration_job` | skipped: job run not approved (run 701596191246320) |
| `mv_smoke` | skipped: job run not approved (run 701596191246320) |

## Files modified
* Run `1082430844509839`: `examples/tpch/docs/registration/registration_results.md` (new), plus this summary and `.build-status/1082430844509839/12.json`.
* Run `701596191246320`: none in `owned_paths`; this summary and `.build-status/701596191246320/12.json`.

## Checks (run `1082430844509839`)
| Check | Result |
|---|---|
| Branch is `mg-genie-ontology-modeled-knowledge-sdk` | pass |
| `bundle validate --strict -t dev` (start and end) | pass |
| `bundle deploy -t dev` | pass (3 unchanged) |
| `registration_job` | pass: run `151387126659064` SUCCESS |
| `mv_smoke` | pass: 7/7 registered, smoke pass, cardinality pass |

## Template fixes for build 1
None. The template-derived job and notebooks worked unchanged.
