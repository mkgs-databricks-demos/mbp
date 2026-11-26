# Tuning Plan 03 — tpch_supply_chain_agent

Written by: iteration 2 (session 37, build run 829522414538457, 2026-11-26), from fresh triage of the tuning-split failures in iterations/02.md (eval run 01f1e9a5cbae1ec8817029d8fb8334e6).
Applied by: iteration 3 (session 38, build run 829522414538457, 2026-11-26). **Status: applied** (1 applied, 0 reverted). Result: eval run 01f1e9ae68ee11e59b439813000f7b87, see iterations/03.md.
Rule: MV-first (ladder steps 1-8 before 9-10). Holdout: numbers only (97.6%, 41/42); no holdout question is cited here.

Iteration-2 tuning accuracy 94.2% (180/191). 11 tuning-split failures, each with one category: Benchmark defect 10 (7 carried, 3 new grading-strictness: x032, x062, x070), Ambiguity 1 (f008, a regression not caused by a plan-02 action). Triage is from the generated SQL versus the expected SQL (no result rows in the eval details).

## Actions by metric view

### mv_tpch_supply_chain_fulfillment

| # | Question ids | Category | Ladder step | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| 1 | f008 | Ambiguity | 1 comment | `Q12 Late Receipt Count` comment: TPC-H Q12 reports late receipts per ship mode and order priority group; when a question names ship modes, keep `Ship Mode` in the grouping (one row per mode and High Priority value), not only the priority split | rows per ship mode and priority; fixes the f008 regression | applied | f008 fixed: agent groups by Ship Mode and High Priority (register run 390630077686402 SUCCESS) |

### Agent (steps 9-10, exhaustion record required)

None. No failure has every applicable step 1-8 exhausted.

| # | Question ids | Category | Ladder step | Change | Exhaustion record | Status | Outcome |
|---|---|---|---|---|---|---|---|

## Exhaustion records

Progress records (not yet exhausted; no agent change allowed):

```json
[
  {"question_id": "f008", "category": "Ambiguity", "tried": []}
]
```

Closed in iteration 2 (fixed): x028 (steps 1 in iterations 1-2), x046 and x054 (steps 1, 4, then 5), x063 (step 6).

## Reverts carried from the previous iteration

None. Iteration 2 regressed one question (f008), not caused by a plan-02 action (no plan-02 change touches the fulfillment view); net gain +3 on the tuning split. Action 1 targets it. Plan-02 action 6 (x062 glossary) was not applied, so there is nothing to revert.

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
| x062 | grading strictness (new in iteration 2): expected SQL rounds to 5 decimals, not asked for; agent's LEFT JOIN returns the same rows |
| x070 | grading strictness (new in iteration 2): expected SQL rounds the share to 4 decimals, not asked for; agent returns the top row as a 0-1 fraction |
| x032 | grading strictness (new in iteration 2): agent inner-joins and filters correctly, with an extra difference column; needs_review |

## Notes for iteration 3

* Iteration 3 is mandatory (the stop rule needs at least 3 applied plans). The last two tuning deltas were +8.9 and +1.6 pp. After iteration 3 the window is [+1.6, delta 3], and +1.6 is not below 1.0, so the asymptote cannot be reached at iteration 3; the earliest is iteration 4 (deltas 3 and 4 both < 1.0 pp, holdout within 2.0 pp of its best, 97.6%). Still run `benchmark.asymptote` after scoring.
* Remaining non-defect failures are 1 of 191; further metadata on the grading-strictness questions would restate the question's wording, so they are left for the owner.
