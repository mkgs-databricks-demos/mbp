# Tuning Plan 01 — tpch_supply_chain_agent

Written by: iteration 0 (baseline, 2026-11-26), from the tuning-split failures in iterations/00_baseline.md (eval run 01f1e95a7f2e12baa07333ab54feff30).
Applied by: iteration 1.
Rule: MV-first (ladder steps 1-8 before 9-10). Holdout: numbers only (83.3%, 35/42); no holdout question is cited here.

Baseline tuning accuracy 83.8% (160/191). 31 tuning-split failures, each with one category: Unit / format 11, Ambiguity 7, Filter / edge 6, Benchmark defect 6 (not tuned), Missing measure 1. Triage is from the generated SQL versus the expected SQL: the eval-run result details carried no result rows, so values were not compared.

## Actions by metric view

### mv_tpch_supply_chain_returns

| # | Question ids | Category | Ladder step | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| 1 | x034, x014 | Unit / format | 4 format | set a percentage `format` on `Return Line Rate` and `Return Rate`, and state in their `comment` that the value is a 0-1 fraction | the agent stops multiplying by 100 when the question asks for a fraction or share | planned | |
| 2 | x062 | Ambiguity | 1 comment | `Return Line Rate` comment: "average" across nations means the overall rate (the measure with no grouping), not the mean of per-nation rates; add synonym "refund rate on lines" | the agent compares with the overall rate | planned | |

### mv_tpch_supply_chain_fulfillment

| # | Question ids | Category | Ladder step | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| 3 | f002, x042 | Unit / format | 4 format | percentage `format` on `On-Time Shipping Rate` and `On-Time Delivery Rate`; comment says 0-1 fraction | fraction returned as asked | planned | |
| 4 | f011, x058 | Filter / edge | 1 comment | `Ship Mode` dimension comment: values are exact codes (list to be read from the data in iteration 1; not verified at baseline); `AIR` and `REG AIR` are different modes; filter with `=` / `IN`; questions about several modes are answered per mode | no `ILIKE '%AIR%'` that also matches REG AIR; per-mode rows for x058 | planned | |
| 5 | x017 | Ambiguity | 1 comment | `High Priority` comment: boolean (definition to be copied from the view YAML in iteration 1); return it as the grouping column | boolean group column as expected | planned | |

### mv_tpch_supply_chain_market_share

| # | Question ids | Category | Ladder step | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| 6 | s059, s052, s053, x070 | Unit / format | 1 comment | `Market Volume` comment (and view comment): national market share = `MEASURE(Market Volume) FILTER (WHERE Supplier Nation = ...) / MEASURE(Market Volume)`, a 0-1 fraction; "across all years" means no year grouping | share as a fraction, single row when no breakdown is asked | planned | |
| 7 | x023 | Missing measure | 6 new measure | add `Order Count` (distinct orders; expression to be written against the view's source in iteration 1), so "per order" does not fall back to `Line Item Count` | market volume per order computed from orders, not lines | planned | |

### mv_tpch_supply_chain_revenue

| # | Question ids | Category | Ladder step | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| 8 | s036 | Unit / format | 6 new measure | add `Discount Share` = `Discount Revenue / Gross Sales` with a percentage `format` (0-1) | the fraction of gross sales given up is one measure | planned | |
| 9 | x093, x014 | Ambiguity | 1 comment | `Order Count` comment in this view: orders with at least one line in the selection; for order volume by order date use `mv_tpch_supply_chain_orders` | order counts come from the orders view | planned | |
| 10 | x003 | Ambiguity | 1 comment | `Revenue` comment: compare with order-header `Order Total Price` as a ratio (net revenue / order total price) | ratio column as expected | planned | |
| 11 | x046, x054 | Unit / format | 4 format | set `format` with explicit decimal places on `Average Discount` (4) | rounding matches the expected 4 decimals | planned | |
| 12 | s040 | Filter / edge | 1 comment | `Revenue` comment: an empty selection returns NULL; do not coalesce to 0 | NULL returned for an empty filter | planned | |

### mv_tpch_supply_chain_profit

| # | Question ids | Category | Ladder step | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| 13 | f051, x097 | Filter / edge | 1 comment | `Profit` comment: empty selection returns NULL (no COALESCE); cross-view year joins use inner joins on `Order Year` | NULL / inner-join results as expected | planned | |
| 14 | x028 | Ambiguity | 1 comment | view comment: "change" year over year means the absolute difference from the prior year unless a percent is asked | absolute deltas | planned | |
| 15 | x070 | Unit / format | (see action 6) | covered by the market share comment | | planned | |

### mv_tpch_supply_chain_orders

| # | Question ids | Category | Ladder step | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| 16 | x032 | Ambiguity | 1 comment | `Ordering Customer Count` comment: "are there any nations with ..." lists the matching nations with both counts | rows per nation instead of a yes/no flag | planned | |

### mv_tpch_supply_chain_market_share / mv_tpch_supply_chain_returns (empty selections)

| # | Question ids | Category | Ladder step | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| 17 | f034, s058 | Filter / edge | 1 comment | `Returned Revenue` and `Market Volume` comments: empty selection returns NULL; do not coalesce | NULL for empty filters | planned | |

### Glossary / UC Pages

| # | Question ids | Category | Ladder step | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| 18 | s059, s052, s053 | Unit / format | 8 glossary | glossary term "National Market Share" (fraction 0-1, TPC-H Q8 definition) and draft UC Page | consistent share definition | planned | |

### Agent (steps 9-10, exhaustion record required)

None at baseline. No instruction or example SQL is planned: no failure has an exhaustion record yet.

| # | Question ids | Category | Ladder step | Change | Exhaustion record | Status | Outcome |
|---|---|---|---|---|---|---|---|

## Exhaustion records

```json
[]
```

## Reverts carried from the previous iteration

None (baseline).

| Action | Why reverted | Questions it regressed |
|---|---|---|

## Benchmark defects (for the owner, not tuned)

| Question id | Problem with the expectation |
|---|---|
| f029 | asks "what percent"; expected SQL returns a 0-1 fraction |
| f030 | asks "in percent"; expected SQL returns a 0-1 fraction |
| f031 | asks "what percentage"; expected SQL returns a 0-1 fraction |
| x078 | expected SQL adds a `profit_per_supplier` column the question does not ask for |
| x101 | expected SQL adds `quantity_per_customer`, not asked for |
| x045 | expected SQL adds `line_items`, not asked for |

## Notes for iteration 1

* Actions 12, 13 and 17 (NULL vs 0 on empty selections) may be grading strictness rather than semantics; if the comment does not change the agent's answer, iteration 1 should report them as `benchmark_defect` candidates rather than add expression changes.
* Actions 4, 5 and 7 carry details not verified at baseline (Ship Mode value list, High Priority definition, Order Count expression); check them against the data and YAML before applying.
