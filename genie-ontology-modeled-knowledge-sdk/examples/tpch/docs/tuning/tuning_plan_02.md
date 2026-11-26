# Tuning Plan 02 — tpch_supply_chain_agent

Written by: iteration 1 (session 36, build run 829522414538457, 2026-11-26), from fresh triage of the tuning-split failures in iterations/01.md (eval run 01f1e99cec631b77b86afd76cfd9923e).
Applied by: iteration 2.
Rule: MV-first (ladder steps 1-8 before 9-10). Holdout: numbers only (92.9%, 39/42); no holdout question is cited here.

Iteration-1 tuning accuracy 92.7% (177/191). 14 tuning-split failures, each with one category: Benchmark defect 7 (not tuned), Unit / format 3, Ambiguity 2, Filter / edge 1, Missing measure 1. Triage is from the generated SQL versus the expected SQL: the eval-run result details carried no result rows, so values were not compared.

## Actions by metric view

### mv_tpch_supply_chain_returns

| # | Question ids | Category | Ladder step | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| 1 | x063 | Missing measure | 6 new dimension | add `Order Year` = `YEAR(orders.o_orderdate)` (integer year, same name and meaning as in the revenue, profit, orders and market share views) | year-level joins with other views use an integer year, not `date_trunc('YEAR', Order Month)`; fixes the x063 regression | planned | |

### mv_tpch_supply_chain_revenue

| # | Question ids | Category | Ladder step | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| 2 | x046, x054 | Unit / format | 5 expression | `Average Discount` expression `ROUND(AVG(source.l_discount), 4)` (comment step 1 and format step 4 tried in iteration 1 and did not change the SQL) | the value matches 4 decimals without the agent rounding | planned | |

### mv_tpch_supply_chain_profit

| # | Question ids | Category | Ladder step | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| 3 | x028 | Filter / edge | 1 comment | view comment: a year-over-year change keeps every year (the first year has a NULL change; do not filter it out) and returns only the changes asked for | all years returned, no extra columns | planned | |

### mv_tpch_supply_chain_supply_cost

| # | Question ids | Category | Ladder step | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| 4 | x032 | Ambiguity | 1 comment | `Supplier Count` comment: to compare supplier and customer counts by nation, match `Supplier Nation` to `Customer Nation` with an inner join; do not FULL OUTER JOIN or COALESCE missing counts to 0 (the `Ordering Customer Count` comment, step 1 in iteration 1, made the agent list nations but not the join) | inner-join comparison rows | planned | |

### mv_tpch_supply_chain_market_share

| # | Question ids | Category | Ladder step | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| 5 | x070 | Unit / format | 1 comment | `Supplier Nation` comment: a nation's share of total market volume is its Market Volume over the total, a 0-1 fraction rounded to 4 decimals; "which nation earns the most" returns the single top row | rounded share, one row | planned | |

### Glossary / UC Pages

| # | Question ids | Category | Ladder step | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| 6 | x062 | Ambiguity | 8 glossary | `return_rate.md` term: "higher than average" across a grouping compares with the overall rate (no grouping), not the mean of group rates; re-upsert DRAFT page b25a694d-21dc-4ec7-9c91-acdfcea5a278 with `only_ids` (step 1 tried in iteration 1: the agent now uses the overall rate; remaining gap is a LEFT JOIN + rounding, so check whether x062 is a grading-strictness `benchmark_defect` candidate before applying) | x062 matches or is reclassified | planned | |

### Agent (steps 9-10, exhaustion record required)

None. No failure has every applicable step 1-8 exhausted.

| # | Question ids | Category | Ladder step | Change | Exhaustion record | Status | Outcome |
|---|---|---|---|---|---|---|---|

## Exhaustion records

Progress records (not yet exhausted; no agent change allowed):

```json
[
  {"question_id": "x046", "category": "Unit / format", "tried": [{"step": 1, "iteration": 1, "result": "still failing"}, {"step": 4, "iteration": 1, "result": "still failing"}]},
  {"question_id": "x054", "category": "Unit / format", "tried": [{"step": 1, "iteration": 1, "result": "still failing"}, {"step": 4, "iteration": 1, "result": "still failing"}]},
  {"question_id": "x028", "category": "Filter / edge", "tried": [{"step": 1, "iteration": 1, "result": "partly fixed: absolute changes now, first year dropped"}]},
  {"question_id": "x032", "category": "Ambiguity", "tried": [{"step": 1, "iteration": 1, "result": "partly fixed: nations listed, outer join"}]},
  {"question_id": "x062", "category": "Ambiguity", "tried": [{"step": 1, "iteration": 1, "result": "partly fixed: overall rate used"}, {"step": 2, "iteration": 1, "result": "synonym used"}]},
  {"question_id": "x070", "category": "Unit / format", "tried": [{"step": 1, "iteration": 1, "result": "partly fixed: fraction, unrounded"}]}
]
```

## Reverts carried from the previous iteration

None. Iteration 1 regressed one question (x063), not caused by a plan-01 action (no plan-01 change touches the returns year path); net gain +17 on the tuning split. Action 1 fixes it.

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
| x042 | expected SQL adds `line_items` and `on_time_lines`, not asked for (new in iteration 1) |

## Notes for iteration 2

* Action 2 changes a measure value (rounded at the source). If it regresses passing questions that compare unrounded discounts, revert it in plan 03 and record x046 / x054 as grading-strictness `benchmark_defect` candidates.
* Actions 5 and 6 target needs_review questions whose remaining gap is rounding or join style; if they do not move, report them as grading strictness rather than add more metadata.
