# Tuning Plan 05 — tpch_supply_chain_agent

Written by: iteration 4 (session 39, build run 829522414538457, 2026-11-26), from fresh triage of the tuning-split failures in iterations/04.md (eval run 01f1e9b700941e0babec9fa9438fbc86).
Applied by: iteration 5.
Rule: MV-first (ladder steps 1-8 before 9-10). Holdout: numbers only (92.9%, 39/42); no holdout question is cited here.

Iteration-4 tuning accuracy 94.2% (180/191), +0.5 pp. 11 tuning-split failures, each with one category: Benchmark defect 10 (unchanged), Ambiguity 1 (f034, regression). Triage is from the generated SQL versus the expected SQL (no result rows in the eval details).

## Actions by metric view

### mv_tpch_supply_chain_returns

| # | Question ids | Category | Ladder step | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| 1 | f034 | Ambiguity | 1 comment | `Returned Revenue` measure comment: replace "report the NULL, do not COALESCE it to 0" with "report the NULL as-is: do not replace it with 0 by COALESCE, IFNULL, NVL or CASE WHEN ... IS NULL THEN 0. A Return Flag other than R (for example N) has no returned lines, so Returned Revenue there is NULL" | f034 returns the raw `Returned Revenue` measure (NULL); other returns questions unchanged | planned | |

### Agent (steps 9-10, exhaustion record required)

None. No failure has every applicable step 1-8 exhausted.

| # | Question ids | Category | Ladder step | Change | Exhaustion record | Status | Outcome |
|---|---|---|---|---|---|---|---|

## Exhaustion records

Progress records (not yet exhausted; no agent change allowed):

```json
[
  {"question_id": "f034", "category": "Ambiguity", "tried": [{"step": 1, "iteration": 1, "what": "Returned Revenue NULL comment (no COALESCE)"}]}
]
```

Closed in iteration 4 (fixed): f042 (step 1, iteration 4), x094 (step 1, iteration 4).

## Reverts carried from the previous iteration

None. Iteration 4 regressed one question (f034, net +1). f034 is on the returns view, which no plan-04 action touched; it is variance on an existing rule, tightened by action 1 rather than reverted.

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
| x042 | expected SQL adds `line_items` and `on_time_lines`, not asked for |
| x062 | grading strictness: expected SQL rounds to 5 decimals, not asked for |
| x070 | grading strictness: expected SQL rounds the share to 4 decimals, not asked for |
| x032 | grading strictness: agent adds a difference column; needs_review |

## Notes for iteration 5

* Stop rule after iteration 4: not reached only because of holdout. Last deltas [-0.52, +0.52] pp (both < 1.0, tuning curve flat); holdout 92.9% is 4.8 pp below its best (97.6%), tolerance 2.0. Iteration 5 meets the rule if its tuning delta is < 1.0 pp and holdout returns to at least 95.6%, i.e. 41/42 or better (40/42 = 95.2% is not enough).
* All 10 remaining non-f034 failures are benchmark defects; the tuning split cannot rise much further without the owner fixing them.
* Holdout moved 41 -> 37 -> 39 with only comment changes; this looks like run-to-run variance. If iteration 5 still misses the holdout tolerance with no tuning-split cause, report it for the owner rather than tuning against it.
