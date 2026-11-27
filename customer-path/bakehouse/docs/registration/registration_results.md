# Metric View Registration Results

Wave 3, session 06. Bundle `ontology-metric-views`, target `dev`.

## Job run

| field | value |
|---|---|
| job | `[dev matthew_giglia] register_metric_views` (job id 1000154254892119) |
| run id | 377694921681813 |
| result state | `TERMINATED` / `SUCCESS` |
| start time (UTC) | 2026-11-27T13:42:50Z |
| end time (UTC) | 2026-11-27T13:45:01Z |
| build run | 244030216249267, started 2026-11-27T13:00:48Z (registration run started after it) |
| previous registration | run 283984710672415 (build run 38498872047824), also SUCCESS |
| started with | `bundle run register_metric_views --target dev --no-wait`, then polled to a terminal state |

## Tasks

| task | task run id | result | notebook output |
|---|---|---|---|
| `generate_manifest` | 281676331154187 | SUCCESS | `{"metric_views": 3, "warnings": 0}` |
| `register_each_mv` (for_each, 3 iterations) | 321747765234966 | SUCCESS | see per-view table |
| `smoke_test` | 239083627145873 | SUCCESS | `{"metric_views": 3, "passed": 3, "failed": []}` |
| `cardinality_test` | 419489096532803 | SUCCESS | `{"metric_views": 3, "checked": 2, "failed": []}` (2 views have joins; `mv_bakehouse_customer_activity` has none, its join is inside the SQL source) |

## Per-view registration

Every `metric_views/manifest.json` entry (3 of 3) is registered.

| view | yaml_path | iteration run id | registered | columns | UC table_type |
|---|---|---|---|---|---|
| `${target_catalog}.${target_schema}.mv_bakehouse_customer_activity` | `metric_views/bakehouse_retail_sales/mv_bakehouse_customer_activity.yml` | 140083486873717 | yes | 17 | METRIC_VIEW |
| `${target_catalog}.${target_schema}.mv_bakehouse_sales` | `metric_views/bakehouse_retail_sales/mv_bakehouse_sales.yml` | 695750792554149 | yes | 30 | METRIC_VIEW |
| `${target_catalog}.${target_schema}.mv_bakehouse_supplier_coverage` | `metric_views/bakehouse_retail_sales/mv_bakehouse_supplier_coverage.yml` | 161700504692309 | yes | 20 | METRIC_VIEW |

The `information_schema.tables` `last_altered` time of all three views is 2026-11-27 13:44:12 UTC, inside the run window. The resolved catalog and schema are in `resolved_target.json`.

## SDK imported by the job

Installed wheel `genie_ontology_modeled_knowledge_sdk-0.1.1-py3-none-any.whl` (not vendored):

* The job environment `sdk` installs `${sdk_volume_path}/.internal/genie_ontology_modeled_knowledge_sdk-0.1.1-py3-none-any.whl` (from `bundle summary`); the wheel exists in the volume.
* The notebooks' `load_sdk` uses `<bundle_root>/src/genie_ontology_modeled_knowledge_sdk_vendored/` only if `mv_yaml.py` is there, otherwise the installed package. No `src/` folder exists in the bundle source or in the deployed files, so the job imported the installed wheel.

## Notes

* The target schema also holds other objects (161 tables/views in total in `information_schema.tables`, including many `__..._metric_view_mat_...` materialized views) that this session did not create. Left untouched.
