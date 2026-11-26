# TPC-H Metric View Registration Results

Bundle: `examples/tpch/ontology-metric-views`, target `dev`. Job: `register_metric_views` (generate_manifest -> register_each_mv forEach -> smoke_test + cardinality_test). Target schema: the one recorded in [resolved_target.json](resolved_target.json) (resolved from `bundle summary`). Run ids are in the session summaries under `docs/sessions/` (session 12 for build 0, session 30 for build 1).

## Build 1 (session 30): SDK wheel and ratio units

SDK source: every job task installs the pinned wheel `genie_ontology_modeled_knowledge_sdk-0.1.0` from the SDK bundle's `sdk_wheels` volume through the job environment `sdk`. There is no vendored copy under `examples/tpch/`. Each `register_single_mv` iteration reported `sdk_source = wheel`, `sdk_version = 0.1.0`, with the module file under `site-packages`.

1. **Move to the wheel (YAML unchanged):** deploy, then a registration run. All 7 views were registered, and smoke and cardinality passed. The tokenized DDL of the YAML the job registered ([ddl_after_wheel.sql](ddl_after_wheel.sql)) is byte for byte equal to the DDL captured before the move ([ddl_before_wheel.sql](ddl_before_wheel.sql)).
2. **Observation 30 (ratio units):** the `Return Rate` and `Return Line Rate` comments in `mv_tpch_supply_chain_returns` now say the value is a fraction 0-1 (both already had `format: percentage`, which affects display only). `gos-validate-mv validate`: 7 files, 0 errors, 0 warnings. Deploy and re-registration passed on the first attempt. The registered view text carries both comments, and `MEASURE(Return Rate)` still returns a 0-1 value.

| MV name | Registered | Smoke pass | Cardinality pass | Attempts (build 1, after obs 30) |
|---|---|---|---|---|
| mv_tpch_supply_chain_fulfillment | yes | pass | pass | 1 |
| mv_tpch_supply_chain_market_share | yes | pass | pass | 1 |
| mv_tpch_supply_chain_orders | yes | pass | pass | 1 |
| mv_tpch_supply_chain_profit | yes | pass | pass | 1 |
| mv_tpch_supply_chain_returns | yes | pass | pass | 1 |
| mv_tpch_supply_chain_revenue | yes | pass | pass | 1 |
| mv_tpch_supply_chain_supply_cost | yes | pass | pass | 1 |

Independent checks: `information_schema.schemata` has the resolved schema, and `information_schema.tables` lists all 7 views with `table_type = METRIC_VIEW`. The `DESCRIBE TABLE EXTENDED ... AS JSON` view text of all 7 parses to the same `version`, `source`, `comment`, `dimensions`, `measures` and `joins` as the YAML. The platform only normalizes: comments are stripped and the `on` key is quoted.

## Build 0 (session 12)

Result: all 7 `manifest.json` entries registered, passed the smoke test (`MEASURE()` query) and passed the cardinality test, on the first deploy/run attempt (SDK from a vendored copy, since removed).

### Job task results (build 0; build 1 runs had the same counts)
| Task | Result | Output |
|---|---|---|
| generate_manifest | SUCCESS | 7 metric views, 0 warnings |
| register_each_mv | SUCCESS | 7 of 7 iterations succeeded, 0 failed |
| smoke_test | SUCCESS | 7 checked, 7 passed, 0 failed |
| cardinality_test | SUCCESS | 7 checked, 0 failed |

### Independent check (outside the job)
* `information_schema.tables` for the target schema lists all 7 views with `table_type = METRIC_VIEW`.
* A `SELECT <first dimension>, MEASURE(<first measure>) ... GROUP BY ALL LIMIT 3` against each view returned rows for all 7.
* Each view's `materialization:` block created its materialized views (and their pipeline event log tables) in the target schema.

### Platform features confirmed
The session 11 hand-over asked to confirm these at registration. All registered without changes:
* Nested (snowflake) joins up to 4 levels (`orders -> customer -> nation -> region`).
* `FILTER (WHERE ...)` measures.
* `materialization:` blocks with `type: aggregated`.

### Defects fixed
None in build 0. No change to the bundle, notebooks or YAMLs was needed.
