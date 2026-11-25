# TPC-H Metric View Registration Results

Bundle: `examples/tpch/ontology-metric-views`, target `dev`. Job: `register_metric_views` (generate_manifest -> register_each_mv forEach -> smoke_test + cardinality_test). Target schema: `<catalog>.<schema>` (from the gitignored dev overrides). Run ids and resolved names are in the session 12 summary under `docs/sessions/`.

Result: all 7 `manifest.json` entries registered, passed the smoke test (`MEASURE()` query) and passed the cardinality test, on the first deploy/run attempt.

| MV name | Registered | Smoke pass | Cardinality pass | Attempts |
|---|---|---|---|---|
| mv_tpch_supply_chain_fulfillment | yes | pass | pass | 1 |
| mv_tpch_supply_chain_market_share | yes | pass | pass | 1 |
| mv_tpch_supply_chain_orders | yes | pass | pass | 1 |
| mv_tpch_supply_chain_profit | yes | pass | pass | 1 |
| mv_tpch_supply_chain_returns | yes | pass | pass | 1 |
| mv_tpch_supply_chain_revenue | yes | pass | pass | 1 |
| mv_tpch_supply_chain_supply_cost | yes | pass | pass | 1 |

## Job task results
| Task | Result | Output |
|---|---|---|
| generate_manifest | SUCCESS | 7 metric views, 0 warnings |
| register_each_mv | SUCCESS | 7 of 7 iterations succeeded, 0 failed |
| smoke_test | SUCCESS | 7 checked, 7 passed, 0 failed |
| cardinality_test | SUCCESS | 7 checked, 0 failed |

## Independent check (outside the job)
* `information_schema.tables` for the target schema lists all 7 views with `table_type = METRIC_VIEW`.
* A `SELECT <first dimension>, MEASURE(<first measure>) ... GROUP BY ALL LIMIT 3` against each view returned rows for all 7.
* Each view's `materialization:` block created its materialized views (and their pipeline event log tables) in the target schema.

## Platform features confirmed
The session 11 hand-over asked to confirm these at registration. All registered without changes:
* Nested (snowflake) joins up to 4 levels (`orders -> customer -> nation -> region`).
* `FILTER (WHERE ...)` measures.
* `materialization:` blocks with `type: aggregated`.

## Defects fixed
None. No change to the bundle, notebooks or YAMLs was needed.
