# 2026-11-26 Wave 1-15 Session 43: Customer Path Prep (R9)

Build run `829522414538457`, branch `mg-genie-ontology-build-1-plan` (checked read-only). Mode `edit`, owned paths `docs/customer-path/**`.

## Changes

* `docs/customer-path/sdk_config.example.json`: inputs for `samples.bakehouse` (four `sales_*` tables), placeholders `<target_catalog>`, `<target_schema>`, `<warehouse_id>`, `<sdk_catalog>`, `<sdk_schema>`; `max_metric_views_per_agent` = 30.
* `docs/customer-path/run_plan.md`: dataset choice, 15 numbered steps in the order of `docs/usage.md` steps 0-4 and the guided notebook cells (who, expected evidence), empty intervention log table (`# | step | who | what happened | why | fix or prerequisite | link`), and known doc gaps.

## Dataset choice (task 1)

`samples` schemas listed via `samples.information_schema.tables`: accuweather, bakehouse, healthverity, nyctaxi, tpcds_sf1, tpcds_sf1000, tpch*, wanderbricks. `samples.bakehouse` (preferred by the plan) is readable: sales_transactions 3,333 rows, sales_customers 300, sales_franchises 48, sales_suppliers 27, media_customer_reviews 204, media_gold_reviews_chunked 196. The two media tables are free-text / RAG chunks and are excluded from `source_tables`.

## Checks

| Check | Result | Detail |
|---|---|---|
| validate_config (placeholders) | pass | 0 errors, 0 warnings |
| validate_config (filled /tmp copy) | pass | 0 errors, 0 warnings (first draft used 50 and warned; changed to 30) |
| dry scaffold `/tmp/customer-path-dry` (vendor=False) | pass | 43 files written; no vendored files; metric-views bundle `sdk_version` default `0.1.0` |
| validate_manifest | pass | 0 errors, 0 warnings; 15 waves, 20 sessions, 190 job tasks |
| validate_authorizations | pass | 0 errors, 0 warnings |
| run plan read-back | pass | 15 numbered steps; intervention log has only header + separator rows |

Nothing written outside `docs/customer-path/`, this summary, the status file and `/tmp`. No deploys, no DDL.

## usage.md / notebook discrepancies (task 5, for session 44)

1. `init_ontology_project` does not pass its `branch` widget to `scaffold_project`, so the scaffolded `waves.json` `branch` defaults to `genie-build-<project_name>` while the vars file `build_branch` comes from the widget.
2. The run kit README says to record `skills` and `pages_domain_id` in `sdk_config.json`; the notebook takes `skills_catalog` / `skills_schema` / `pages_domain_id` widgets but its config dict does not include them.
3. Notebook widget default `max_metric_views_per_agent` = 50 triggers a `config_warnings` warning (agents split at 30).
4. usage.md step 2.2 names a `consumer_group` widget; the notebook has `readers` / `curators`.

## Requests

None. The child build itself is owner prerequisite P1-6 (run_plan.md).
