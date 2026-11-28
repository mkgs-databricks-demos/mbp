# Tuning Plan 04 — Bakehouse Retail Sales Agent

* Source: iteration 3, Genie eval run `01f1eb0b1b1913d6b9212913ea668510`, started 2026-11-28T09:07:15Z (build run 409860738864401, session 14). See `docs/tuning/iterations/03.md`.
* Current: tuning 133/146 (91.1%), holdout 37/41 (90.2%, numbers only). `benchmark.asymptote`: not reached (3 plans applied; last deltas 2.05, -0.68 pp; the 2.05 pp delta is still inside the window).
* Scope of triage: the **13 tuning-split failures only**. No holdout question is listed or cited.
* Evidence: the 4 regressions (a-055, b-010, x-047, x-054) re-run read-only on the dev metric views (Genie SQL and rendered `expected_sql`, full result sets compared). The other 9 are carried benchmark-defect candidates, not re-run.
* Ladder order: metric view (1-7), glossary (8), agent (9-10). No new agent instruction. One agent-layer **partial revert** (G1r) of the plan 03 instruction that caused x-047.

## Data facts checked (read-only, dev target)

* x-047: Genie and the expectation agree on the top 8 stores. At the tie on growth 1.0, Genie ordered by `Franchise Name` (G1 says "then the name") and returned 3000046 (Baked Bliss) and 3000007; the expectation orders by `Franchise ID` and returns 3000007 and 3000020. Store names are not unique (Franchise Name comment).
* x-054: Genie grouped by `Franchise Size` (XL 22.52, XXL 16.26); the expectation is one combined value 19.75 for XL and XXL stores on an approved supplier. Genie used the sales-view `Supplier Approved` filter correctly.
* a-055: values identical; Genie returned `INITCAP(Customer Gender)` (`Male`, `Female`); the stored values are `male`, `female`.
* b-010: values identical; Genie returns `Gross Sales` next to the share, the expectation returns the denominator `Gross Sales All Products` (not asked). Same pattern as a-045, b-039.

## Actions by metric view

### mv_bakehouse_sales

| # | Ladder step | Category | Question ids | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| S13 | 1 (comment) | Ambiguity | x-047 | `Franchise ID` comment: add "When ranking stores (top N), break ties on the measure by Franchise ID, not Franchise Name." | Tied stores ordered by id; x-047 returns 3000007, 3000020 | planned | |
| S14 | 1 (comment) | Ambiguity | x-054 | `Franchise Size` comment: add "Several sizes named together ('XL and XXL stores') mean one combined group: filter IN ('XL', 'XXL') and return one value; group by Franchise Size only when the question asks by size or for each size." | One combined ATV (19.75) | planned | |
| S15 | 1 (comment) | Unit / format | a-055 | `Customer Gender` comment: exact values 'male', 'female' (lowercase); return them as stored, do not change case (no INITCAP / UPPER) | Values match the stored labels | planned | |

### mv_bakehouse_customer_activity

| # | Ladder step | Category | Question ids | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| A4 | 1 (comment) | Unit / format | a-055 | Same `Customer Gender` exact-value / keep-case comment as S15 (consistency across views) | Same as S15 | planned | |

### Agent (bakehouse_retail_sales_agent)

| # | Ladder step | Category | Question ids | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| G1r | revert (part of G1) | Ambiguity | x-047 (regressed by G1), x-004 (keep fixed) | Remove the tie-break clause ", then the name," from the G1 instruction; keep "return exactly N rows ... LIMIT N (not RANK() <= N ...)". Tie-break comes from S13 (metric view). No new instruction. Render with `--check`, redeploy ontology-genie-agents | x-047 fixed, x-004 stays fixed | planned | |

## benchmark_defect (for the owner; not tuned)

a-045, a-046, b-039, b-010 (expectation adds a column not asked for), a-061 (adds a constant `Franchise ID` column), b-042, x-018 (from plan 01), x-035 (Genie adds a `USA` row with 0), x-048 (verified in iteration 2: the expectation drops prior-day sales of stores with no sale on 2024-05-16), x-055 (rounding only).

## Classification count

13 tuning failures, each with exactly one category: Ambiguity 2 (x-047, x-054); Unit / format 1 (a-055); Benchmark defect 10 (a-045, a-046, a-061, b-010, b-039, b-042, x-018, x-035, x-048, x-055).

## Exhaustion records

No new agent instruction or example SQL is planned, so no new record is needed. G1r only removes text from G1. The x-004 record that backs G1 (plan 03) stays valid:

```json
{"question_id": "x-004", "category": "Ambiguity",
 "tried": [{"step": 1, "iteration": 2, "result": "not applicable: tie handling in top-N is not measure or dimension metadata; S8 applied and x-004 still failed on the tie"},
           {"step": 2, "iteration": 2, "result": "not applicable: Genie picks the right measure and dimension"},
           {"step": 3, "iteration": 2, "result": "not applicable: names are right"},
           {"step": 4, "iteration": 2, "result": "not applicable: values match"},
           {"step": 5, "iteration": 2, "result": "not applicable: measure expression is right"},
           {"step": 6, "iteration": 2, "result": "not applicable: no missing measure or dimension"},
           {"step": 7, "iteration": 2, "result": "not applicable: single-view answer, no join problem"},
           {"step": 8, "iteration": 2, "result": "not applicable: no glossary term covers top-N"},
           {"step": 9, "iteration": 3, "result": "fixed by G1 (eval 01f1eb0b1b1913d6b9212913ea668510)"}],
 "confirmed_failing": {"iteration": 2, "eval_run_id": "01f1eb035de91aad886e10d893b5fefc", "detail": "RANK() <= 10 returns 11 rows"}}
```

If x-047 still fails after S13 and G1r, iteration 5 may add the tie-break to G1 again only with an x-047 exhaustion record (S13 = step 1 tried).
