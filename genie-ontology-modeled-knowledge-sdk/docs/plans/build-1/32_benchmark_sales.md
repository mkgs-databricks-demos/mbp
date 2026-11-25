# Session 32: Benchmark Questions — Sales Views

## Scope
Write at least 15 benchmark questions for each sales metric view (`mv_tpch_supply_chain_orders`, `mv_tpch_supply_chain_revenue`, `mv_tpch_supply_chain_market_share`), each with tokenized `expected_sql` that ran `SUCCEEDED`. Write only the owned files.

## Context
* [Exhaustive tuning protocol](INDEX.md#exhaustive-tuning-protocol-owner-request) and the question YAML contract in [INDEX](INDEX.md#cross-session-contracts); `skills/ontology-tuning` (session 26) is the method.
* Sessions 33 and 34 write the other files in parallel; together the set must reach 100-498 questions with >= 25% cross-view (session 34). Your share: 45-90 single-view questions.
* Read the registered YAML in `examples/tpch/ontology-metric-views/metric_views/` (session 30's version), the glossary in `examples/tpch/docs/semantics/`, and the KPI research in `examples/tpch/docs/research/`. Do **not** read the agent's `sample_questions` text into the benchmark: use different wording.
* Do not write report-style multi-turn scenarios: session 42 owns the independent evaluation.

## Tasks
1. For each view: every measure asked at least once, every dimension used at least once; cover the types `simple`, `breakdown`, `time`, `filter`, `ratio`, `synonym`, `edge` (at least 2 of each per view where the view supports it).
2. Question ids `s001`...; tags `type:<t>`, `view:<mv>`, `measure:<m>`, `dimension:<d>`.
3. `expected_sql`: `SELECT ... MEASURE(<measure>) FROM ${target_catalog}.${target_schema}.<mv> ...`; render it with `resolved_target.json` and run it read-only on the warehouse; add `expected_answer` for scalars.
4. `sales_notes.md`: per-view coverage counts, every question id with statement state, and any question dropped with the reason.
5. Check: `gos-benchmark coverage` on your file alone reports full measure and dimension coverage for the three views.

## Acceptance Criteria
- [ ] >= 15 questions per view; every measure and dimension of the three views covered.
- [ ] Every `expected_sql` ran `SUCCEEDED` (listed in the notes).
- [ ] No resolved catalog or schema name in the YAML.

## Owned Paths
- `examples/tpch/docs/tuning/benchmark/sales.yml`, `examples/tpch/docs/tuning/benchmark/sales_notes.md`

## Dependencies
- Sessions 22 (benchmark API), 26 (method), 30 (registered views, `resolved_target.json`).
