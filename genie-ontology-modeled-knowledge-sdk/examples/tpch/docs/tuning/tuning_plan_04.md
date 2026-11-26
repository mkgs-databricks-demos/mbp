# Tuning Plan 04 — tpch_supply_chain_agent

Written by: iteration 3 (session 38, build run 829522414538457, 2026-11-26), from fresh triage of the tuning-split failures in iterations/03.md (eval run 01f1e9ae68ee11e59b439813000f7b87).
Applied by: iteration 4 (session 39, build run 829522414538457, 2026-11-26). **Status: applied** (2 applied, 0 reverted). Eval run 01f1e9b700941e0babec9fa9438fbc86: tuning 94.2% (180/191), holdout 92.9% (39/42).
Rule: MV-first (ladder steps 1-8 before 9-10). Holdout: numbers only (88.1%, 37/42); no holdout question is cited here.

Iteration-3 tuning accuracy 93.7% (179/191), -0.5 pp. 12 tuning-split failures, each with one category: Benchmark defect 10 (unchanged from plan 03), Ambiguity 2 (f042, x094, both regressions). Triage is from the generated SQL versus the expected SQL (no result rows in the eval details).

## Actions by metric view

### mv_tpch_supply_chain_profit

| # | Question ids | Category | Ladder step | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| 1 | f042 | Ambiguity | 1 comment | View `comment`: replace "return only the changes asked for, not the underlying yearly values" with: "Return a year-over-year difference only when the question asks for the year-over-year (or annual) change or growth; a question about how yearly profit changed over a range of years is a trend: return Profit per Order Year." Keep the rest of the sentence (absolute difference, keep the first year with a NULL change) | f042 returns `Profit` by `Order Year`; x063 (fixed by plan-02 action 3) keeps passing | applied | f042 fixed; x063 still passes |

### mv_tpch_supply_chain_revenue

| # | Question ids | Category | Ladder step | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| 2 | x094 | Ambiguity | 1 comment | `Revenue` measure comment: add "Net revenue means this measure (net of discount); do not subtract Returned Revenue or refunds unless the question asks for revenue after returns. Combined with other views by Ship Mode, join the per-mode results with an inner join on Ship Mode" | x094 returns `Revenue` with inner joins; no change to other revenue questions | applied | x094 fixed; no revenue-view regression |

### Agent (steps 9-10, exhaustion record required)

None. No failure has every applicable step 1-8 exhausted.

| # | Question ids | Category | Ladder step | Change | Exhaustion record | Status | Outcome |
|---|---|---|---|---|---|---|---|

## Exhaustion records

Progress records (not yet exhausted; no agent change allowed):

```json
[
  {"question_id": "f042", "category": "Ambiguity", "tried": []},
  {"question_id": "x094", "category": "Ambiguity", "tried": []}
]
```

Closed in iteration 3 (fixed): f008 (step 1 in iteration 3).

## Reverts carried from the previous iteration

None reverted. Iteration 3 regressed two questions (net -1). x094 is not touched by the plan-03 action. f042 is traced to plan-02 action 3 (profit view comment); instead of reverting it (it fixed x063), action 1 narrows the sentence that caused the regression.

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

## Notes for iteration 4

* Stop rule after iteration 3: not reached. Last deltas [+1.57, -0.52] pp; holdout gap 9.5 pp (best 97.6%, now 88.1%). Iteration 4 can meet the rule only if its tuning delta is < 1.0 pp and holdout returns to at least 95.6%.
* The holdout drop (4 questions) came with a single fulfillment measure comment; it is most likely run-to-run variance. Iteration 4 re-measures it; if holdout stays low with no matching tuning-split cause, report it for the owner rather than tuning against it (holdout is never read).
* f008 passes, but the agent used `ILIKE` on Ship Mode despite the comment; watch it, no action now.
