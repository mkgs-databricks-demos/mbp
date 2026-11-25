# Session 33: Benchmark Questions — Fulfillment & Procurement Views

## Scope
Write at least 15 benchmark questions for each of `mv_tpch_supply_chain_fulfillment`, `mv_tpch_supply_chain_returns`, `mv_tpch_supply_chain_profit` and `mv_tpch_supply_chain_supply_cost`, each with tokenized `expected_sql` that ran `SUCCEEDED`. Write only the owned files.

## Context
* Same method, contract and rules as [plan 32](32_benchmark_sales.md) (different wording from sample questions; no report scenarios).
* Your share: 60-120 single-view questions.
* Build-0 observation 30: ratio units. Include at least 3 `ratio` questions on `Return Rate` / `Return Line Rate` that a reader could take as a percentage, with `expected_answer` as the 0-1 fraction (the scorer reports `unit_mismatch`).

## Tasks
1. Per view: every measure and dimension at least once; types `simple`, `breakdown`, `time`, `filter`, `ratio`, `synonym`, `edge` (at least 2 each where supported).
2. Ids `f001`...; tags as in plan 32.
3. `expected_sql` rendered and run read-only; `expected_answer` for scalars.
4. `fulfillment_procurement_notes.md`: coverage counts, every question id with statement state, dropped questions with reasons.

## Acceptance Criteria
- [ ] >= 15 questions per view; every measure and dimension of the four views covered.
- [ ] Every `expected_sql` ran `SUCCEEDED`.
- [ ] No resolved catalog or schema name in the YAML.

## Owned Paths
- `examples/tpch/docs/tuning/benchmark/fulfillment_procurement.yml`, `examples/tpch/docs/tuning/benchmark/fulfillment_procurement_notes.md`

## Dependencies
- Sessions 22, 26, 30.
