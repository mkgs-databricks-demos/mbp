# Benchmark notes: fulfillment and procurement views (session 33)

Question file: [fulfillment_procurement.yml](fulfillment_procurement.yml), ids `f001`-`f069`, single-view questions only (cross-view questions are in `cross_view.yml`, session 34).

## Method

* Source of measures and dimensions: the registered YAML in `examples/tpch/ontology-metric-views/metric_views/tpch_supply_chain/` (session 30's version).
* Wording is my own; the agent's `sample_questions` were not used.
* `expected_sql` uses `MEASURE()` over `${target_catalog}.${target_schema}.<mv>`. For each run, the tokens were replaced with the values in `examples/tpch/docs/registration/resolved_target.json` and the query ran read-only through the Statement Execution API on that file's warehouse.
* `expected_answer` is set only for scalar results (one row, one column, not NULL): 30 questions. Ratios are stored as 0-1 fractions, rounded to 6 decimals (build-0 observation 30). Other numbers are rounded to 4 decimals. The scorer's tolerance is relative 1e-4.
* Ratio unit traps (observation 30): f029 and f031 (`Return Line Rate`) and f030 (`Return Rate`) ask for a percentage, and f028 (`Return Rate`) asks for a fraction. All four expect the 0-1 fraction, so an answer of 24.7 scores as `unit_mismatch`.

## Coverage (per view)

`benchmark.coverage` was run on this file with the four metric view YAMLs. Every measure and dimension of the four views is tagged at least once. The only problems it reports apply to the whole set, not to this file: fewer than 100 questions, 0% cross-view and no `cross_view` type. Sessions 32 and 34 close those.

| View | Questions | simple | breakdown | time | filter | ratio | synonym | edge |
|---|---|---|---|---|---|---|---|---|
| mv_tpch_supply_chain_fulfillment | 18 | 2 | 2 | 3 | 3 | 2 | 3 | 3 |
| mv_tpch_supply_chain_returns | 17 | 2 | 3 | 2 | 2 | 4 | 2 | 2 |
| mv_tpch_supply_chain_profit | 17 | 3 | 3 | 2 | 3 | 2 | 2 | 2 |
| mv_tpch_supply_chain_supply_cost | 17 | 3 | 4 | 0 | 3 | 2 | 2 | 3 |
| **Total** | **69** | 10 | 12 | 7 | 11 | 10 | 9 | 10 |

`mv_tpch_supply_chain_supply_cost` has no `time` questions because it has no date column (it is snapshot data at offer grain).

Under `benchmark.assign_splits`, this file has 60 tuning and 9 holdout questions.

## Statement state per question

All 69 `expected_sql` statements ended `SUCCEEDED`, both on the first run and again on a re-run from the written file.

| Id | State | Id | State | Id | State |
|---|---|---|---|---|---|
| f001 | SUCCEEDED | f024 | SUCCEEDED | f047 | SUCCEEDED |
| f002 | SUCCEEDED | f025 | SUCCEEDED | f048 | SUCCEEDED |
| f003 | SUCCEEDED | f026 | SUCCEEDED | f049 | SUCCEEDED |
| f004 | SUCCEEDED | f027 | SUCCEEDED | f050 | SUCCEEDED |
| f005 | SUCCEEDED | f028 | SUCCEEDED | f051 | SUCCEEDED |
| f006 | SUCCEEDED | f029 | SUCCEEDED | f052 | SUCCEEDED |
| f007 | SUCCEEDED | f030 | SUCCEEDED | f053 | SUCCEEDED |
| f008 | SUCCEEDED | f031 | SUCCEEDED | f054 | SUCCEEDED |
| f009 | SUCCEEDED | f032 | SUCCEEDED | f055 | SUCCEEDED |
| f010 | SUCCEEDED | f033 | SUCCEEDED | f056 | SUCCEEDED |
| f011 | SUCCEEDED | f034 | SUCCEEDED | f057 | SUCCEEDED |
| f012 | SUCCEEDED | f035 | SUCCEEDED | f058 | SUCCEEDED |
| f013 | SUCCEEDED | f036 | SUCCEEDED | f059 | SUCCEEDED |
| f014 | SUCCEEDED | f037 | SUCCEEDED | f060 | SUCCEEDED |
| f015 | SUCCEEDED | f038 | SUCCEEDED | f061 | SUCCEEDED |
| f016 | SUCCEEDED | f039 | SUCCEEDED | f062 | SUCCEEDED |
| f017 | SUCCEEDED | f040 | SUCCEEDED | f063 | SUCCEEDED |
| f018 | SUCCEEDED | f041 | SUCCEEDED | f064 | SUCCEEDED |
| f019 | SUCCEEDED | f042 | SUCCEEDED | f065 | SUCCEEDED |
| f020 | SUCCEEDED | f043 | SUCCEEDED | f066 | SUCCEEDED |
| f021 | SUCCEEDED | f044 | SUCCEEDED | f067 | SUCCEEDED |
| f022 | SUCCEEDED | f045 | SUCCEEDED | f068 | SUCCEEDED |
| f023 | SUCCEEDED | f046 | SUCCEEDED | f069 | SUCCEEDED |

## Edge questions with an empty or NULL result

These have no `expected_answer` because the result is NULL, so the scorer compares result rows against `expected_sql`:

* f034: `Returned Revenue` with `Return Flag = 'N'` (the measure's own filter excludes those lines).
* f051: `Profit` for part names containing 'plaid' (the result is NULL: no sold line matches).
* f068: `Minimum Supply Cost` for `Part Size = 51` (the YAML comment gives sizes 1 to 50; the result is NULL).

f035 expects 0.0: no line of the August 1998 orders is returned.

## Dropped or reworded questions

* None dropped.
* f069 was reworded before it was written. The first draft asked for the 5 brands with the lowest minimum supply cost, but the first two rows it returned (Brand#11 and Brand#12) were tied at 1.00, so the top 5 could depend on tie order. It now asks for the minimum supply cost of every brand (25 rows).
