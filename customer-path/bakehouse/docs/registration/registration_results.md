# Metric View Registration Results

Wave 3, session 06. Bundle `ontology-metric-views`, target `dev`.

## Job run

| field | value |
|---|---|
| job | `[dev matthew_giglia] register_metric_views` (job id 859595802942054) |
| run id | 352877825862386 |
| result state | `TERMINATED` / `SUCCESS` |
| start time (UTC) | 2026-11-28T05:08:30Z |
| end time (UTC) | 2026-11-28T05:10:41Z |
| build run | 409860738864401, started 2026-11-28T05:05:18Z (registration run started after it) |
| previous registration | run 377694921681813 on job 1000154254892119 (build run 244030216249267), also SUCCESS |
| deploy note | `bundle deploy` in this build found no prior deployment state and created a new job (859595802942054) and re-applied the schema and its grants; the earlier job 1000154254892119 still exists outside bundle state (see session summary) |
| started with | `bundle run register_metric_views --target dev --no-wait`, then polled to a terminal state |

## Tasks

| task | task run id | result | notebook output |
|---|---|---|---|
| `generate_manifest` | 1121632101215608 | SUCCESS | `{"metric_views": 3, "warnings": 0}` |
| `register_each_mv` (for_each, 3 iterations) | 418356790873533 | SUCCESS | see per-view table |
| `smoke_test` | 884609972872843 | SUCCESS | `{"metric_views": 3, "passed": 3, "failed": []}` |
| `cardinality_test` | 914550165449358 | SUCCESS | `{"metric_views": 3, "checked": 2, "failed": []}` (2 views have joins; `mv_bakehouse_customer_activity` has none, its join is inside the SQL source) |

## Per-view registration

Every `metric_views/manifest.json` entry (3 of 3) is registered.

| view | yaml_path | iteration run id | registered | columns | UC table_type |
|---|---|---|---|---|---|
| `${target_catalog}.${target_schema}.mv_bakehouse_customer_activity` | `metric_views/bakehouse_retail_sales/mv_bakehouse_customer_activity.yml` | 481147020957692 | yes | 17 | METRIC_VIEW |
| `${target_catalog}.${target_schema}.mv_bakehouse_sales` | `metric_views/bakehouse_retail_sales/mv_bakehouse_sales.yml` | 1051251474504696 | yes | 30 | METRIC_VIEW |
| `${target_catalog}.${target_schema}.mv_bakehouse_supplier_coverage` | `metric_views/bakehouse_retail_sales/mv_bakehouse_supplier_coverage.yml` | 586410427915028 | yes | 20 | METRIC_VIEW |

The `information_schema.tables` `last_altered` time of all three views is 2026-11-28 05:09:54 UTC, inside the run window. The resolved catalog and schema are in `resolved_target.json`.

## SDK imported by the job

Installed wheel `genie_ontology_modeled_knowledge_sdk-0.1.1-py3-none-any.whl` (not vendored):

* The job environment `sdk` installs `${sdk_volume_path}/.internal/genie_ontology_modeled_knowledge_sdk-0.1.1-py3-none-any.whl` (from `bundle summary`); the wheel exists in the volume.
* The notebooks' `load_sdk` uses `<bundle_root>/src/genie_ontology_modeled_knowledge_sdk_vendored/` only if `mv_yaml.py` is there, otherwise the installed package. No `src/` folder exists in the bundle source or in the deployed files, so the job imported the installed wheel.

## Notes

* The target schema also holds other objects (161 tables/views in total in `information_schema.tables`, including many `__..._metric_view_mat_...` materialized views) that this session did not create. Left untouched.
