# Session 34: Benchmark Questions — Cross-View

## Scope
Write at least 60 questions that need two or more of the seven metric views, each with tokenized `expected_sql` that ran `SUCCEEDED`. Write only the owned files.

## Context
* Same method, contract and rules as [plan 32](32_benchmark_sales.md).
* The cross-view share must be >= 25% of the whole set (sessions 32 + 33 + 34). Plan for the upper end of 32 and 33: write at least 60 and up to 150, keeping the total at most 498.
* Use the verified joins and shared dimensions in `examples/tpch/docs/data_profiles/data_model_summary.md` and `examples/tpch/docs/domain_manifest.yml`. A cross-view question combines measures from different views over a shared dimension (nation, region, time, part, supplier, customer segment), compares two KPIs, or derives one from two (revenue vs supply cost, returns vs revenue by nation).

## Tasks
1. List every view pair with a business meaning (in the notes); at least 3 questions per such pair, and some 3-view questions.
2. Types: tag `type:cross_view` plus the secondary type (`breakdown`, `time`, `ratio`, ...).
3. Ids `x001`...; tags list every view and measure the question needs.
4. `expected_sql` joins or unions `MEASURE()` results from each view on the shared dimension (CTEs per view), rendered and run read-only.
5. `cross_view_notes.md`: pair matrix with counts, every question id with statement state, dropped questions with reasons.

## Acceptance Criteria
- [ ] >= 60 cross-view questions; every meaningful view pair has >= 3.
- [ ] Every `expected_sql` ran `SUCCEEDED`.
- [ ] Wave gate `benchmark_coverage` passes over the three files together.

## Owned Paths
- `examples/tpch/docs/tuning/benchmark/cross_view.yml`, `examples/tpch/docs/tuning/benchmark/cross_view_notes.md`

## Dependencies
- Sessions 22, 26, 30.
