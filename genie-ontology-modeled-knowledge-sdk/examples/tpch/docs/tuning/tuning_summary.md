# Tuning Summary — tpch_supply_chain_agent

Written by session 41 (build run 829522414538457, 2026-11-26). Sources: `accuracy_history.json`, `iterations/00_baseline.md`..`06.md`, `tuning_plan_01.md`..`tuning_plan_05.md`. Holdout figures are numbers only; no holdout question was read.

## Result

Stop rule: **reached at iteration 5** (`benchmark.asymptote`: tuning accuracy gained < 1.0 pp in each of the last 2 iterations; holdout within 2.0 pp of its best). 5 fix iterations applied (minimum 3), not exhausted (limit 6). Iteration 6 recorded `converged at iteration 5` and changed nothing.

```json
{"reached": true, "reason": "tuning accuracy gained < 1.0 pp in each of the last 2 iterations; holdout within 2.0 pp of its best", "fix_iterations": 5, "last_deltas_pp": [0.5235, 0.5236], "holdout_gap_pp": 0.0, "exhausted": false}
```

Net: tuning split 83.8% -> 94.8% (+11.0 pp, 160 -> 181 of 191); holdout 83.3% -> 97.6% (+14.3 pp, 35 -> 41 of 42). Every change was a Unity Catalog semantic change (ladder steps 1-8). **No agent instruction and no example SQL was added.** All 10 remaining tuning-split failures are benchmark defects.

## Accuracy curve

| Iteration | Label | Eval run | Tuning accuracy | Delta (pp) | Holdout accuracy | Holdout gap to best (pp) |
|---|---|---|---|---|---|---|
| 0 | baseline | 01f1e95a7f2e12baa07333ab54feff30 | 83.8% (160/191) | — | 83.3% (35/42) | 0.0 |
| 1 | tuning_plan_01 | 01f1e99cec631b77b86afd76cfd9923e | 92.7% (177/191) | +8.90 | 92.9% (39/42) | 0.0 |
| 2 | tuning_plan_02 | 01f1e9a5cbae1ec8817029d8fb8334e6 | 94.2% (180/191) | +1.57 | 97.6% (41/42) | 0.0 |
| 3 | tuning_plan_03 | 01f1e9ae68ee11e59b439813000f7b87 | 93.7% (179/191) | -0.52 | 88.1% (37/42) | 9.5 |
| 4 | tuning_plan_04 | 01f1e9b700941e0babec9fa9438fbc86 | 94.2% (180/191) | +0.52 | 92.9% (39/42) | 4.8 |
| 5 | tuning_plan_05 | 01f1e9bfb0df1b80b8150581a4dc3e1d | 94.8% (181/191) | +0.52 | 97.6% (41/42) | 0.0 |
| 6 | converged | (none) | 94.8% (181/191) | — | 97.6% (41/42) | 0.0 |

The holdout dip at iterations 3-4 (41 -> 37 -> 39) came with single comment changes and no matching tuning-split cause; it returned to its best at iteration 5 with no holdout-directed change, so it is read as run-to-run variance, not overfitting (no agent-layer change existed to revert).

## Changes by ladder step

Counts are tuning-plan actions; one action may touch more than one view.

| Step | Layer | Iterations | Actions applied | Actions reverted |
|---|---|---|---|---|
| 1 | metric view comment | 1, 2, 3, 4, 5 | 19 (it1: 12, it2: 3, it3: 1, it4: 2, it5: 1) | 0 |
| 2 | metric view synonyms | 1 | 1 (Return Line Rate: "refund rate on lines", "share of lines returned"; part of plan-01 action 2) | 0 |
| 3 | metric view display_name | — | 0 | 0 |
| 4 | metric view format | 1 | 3 (Return Rate / Return Line Rate, On-Time Shipping / Delivery Rate, Average Discount) | 0 |
| 5 | expression / FILTER | 2 | 1 (Average Discount = ROUND(AVG(l_discount), 4)) | 0 |
| 6 | new measure or dimension | 1, 2 | 3 (Order Count in market share; Discount Share in revenue; Order Year in returns) | 0 |
| 7 | join fix / right-grain move | — | 0 | 0 |
| 8 | glossary term + DRAFT UC Page | 1, 2 | 1 (National Market Share term, DRAFT page 05defcc6 re-upserted) | 1 (plan-02 action 6, return_rate term for x062: not applied, x062 reclassified as grading strictness) |
| 9 | agent instruction | — | 0 | 0 |
| 10 | agent example SQL | — | 0 | 0 |

By iteration:

| Iteration | Plan | Applied | Reverted | Views touched | Registration run |
|---|---|---|---|---|---|
| 1 | tuning_plan_01 | 18 | 0 | returns, fulfillment, market_share, revenue, profit, orders, glossary | 260504764502059 |
| 2 | tuning_plan_02 | 5 | 1 | returns, revenue, profit, supply_cost, market_share | 997993635139017 |
| 3 | tuning_plan_03 | 1 | 0 | fulfillment | 390630077686402 |
| 4 | tuning_plan_04 | 2 | 0 | profit, revenue | 1067669752222987 |
| 5 | tuning_plan_05 | 1 | 0 | returns | 198716023326190 |

Questions fixed (tuning split): it1 x034, x014, f002, f011, x058, x017, s059, s052, s053, x023, s036, x093, x003, s040, f051, x097, f034, s058 (18 fixed, 1 regressed, net +17); it2 x063, x046, x054, x028; it3 f008; it4 f042, x094; it5 f034. Regressions: x063 (it1), f008 (it2), f042 and x094 (it3), f034 (it4); each was fixed in the next iteration by a metric view change (x063 by step 6, the others by step 1), never by an agent change.

## Agent-layer changes

None. No failure reached an exhaustion record with every applicable step 1-8 tried, so no instruction (step 9) or example SQL (step 10) was allowed or added. The agent file `examples/tpch/ontology-genie-agents/agents/` was last changed by the baseline (wave 1-7, session 35) and was never redeployed during tuning.

| Change | Question ids | Why the metric view / glossary steps were not enough (exhaustion record) |
|---|---|---|

## Remaining tuning-split failures

All 10 are `Benchmark defect`: the expectation, not the agent, is wrong or stricter than the question. They were not tuned (the benchmark is frozen during tuning).

| Question id | Category | Problem | Steps tried | Recommended next fix |
|---|---|---|---|---|
| f029 | Benchmark defect | asks "what percent"; expected SQL returns a 0-1 fraction | none (not tunable) | owner: multiply expected by 100 or reword to "what fraction" |
| f030 | Benchmark defect | asks "in percent"; expected SQL returns a 0-1 fraction | none (not tunable) | owner: same as f029 |
| f031 | Benchmark defect | asks "what percentage"; expected SQL returns a 0-1 fraction | none (not tunable) | owner: same as f029 |
| x042 | Benchmark defect | expected SQL adds `line_items` and `on_time_lines`, not asked for | 4 format (it1), 1 comment (it1): agent answer correct | owner: drop the extra columns from expected SQL |
| x045 | Benchmark defect | expected SQL adds `line_items`, not asked for | none (not tunable) | owner: drop the extra column |
| x078 | Benchmark defect | expected SQL adds `profit_per_supplier`, not asked for | none (not tunable) | owner: drop the extra column |
| x101 | Benchmark defect | expected SQL adds `quantity_per_customer`, not asked for | none (not tunable) | owner: drop the extra column |
| x032 | Benchmark defect (grading strictness, needs_review) | agent inner-joins and filters correctly, adds a difference column | 1 comment (it1 Ordering Customer Count, it2 Supplier Count) | owner: accept extra column or mark the question for manual review |
| x062 | Benchmark defect (grading strictness, needs_review) | expected SQL rounds to 5 decimals, not asked for; agent LEFT JOIN returns the same rows | 1 comment + 2 synonyms (it1); 8 glossary considered and not applied (it2) | owner: remove ROUND from expected or ask for rounding in the question |
| x070 | Benchmark defect (grading strictness, needs_review) | expected SQL rounds the share to 4 decimals, not asked for | 1 comment (it1 Market Volume, it2 Supplier Nation) | owner: remove ROUND from expected or ask for rounding |

Without these 10, the tuning split would score 181/181 on the remaining questions; fixing the expectations is the only way to raise the tuning curve further.

## Benchmark defects reported

f029, f030, f031 (percent asked, fraction expected); x042, x045, x078, x101 (expected SQL adds columns not asked for); x032, x062, x070 (grading strictness, `needs_review`). Reported to the owner in every iteration file and plan since they were found (f029-f031, x045, x078, x101 at baseline; x042 in iteration 1; x032, x062, x070 in iteration 2). `docs/tuning/benchmark/**` was not edited.
