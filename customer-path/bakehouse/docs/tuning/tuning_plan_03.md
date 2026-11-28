# Tuning Plan 03 — Bakehouse Retail Sales Agent

**Status: applied** in iteration 3 (build run 409860738864401, session 14). Eval run `01f1eb0b1b1913d6b9212913ea668510`, started 2026-11-28T09:07:15Z: tuning 133/146 (91.1%, -0.7 pp), holdout 37/41 (90.2%). All four actions applied; all three targeted questions fixed; G1 also caused one regression (x-047), carried into `tuning_plan_04.md`. See `docs/tuning/iterations/03.md`.

* Source: iteration 2, Genie eval run `01f1eb035de91aad886e10d893b5fefc`, started 2026-11-28T08:11:51Z (build run 409860738864401, session 13). See `docs/tuning/iterations/02.md`.
* Current: tuning 134/146 (91.8%), holdout 35/41 (85.4%, numbers only). `benchmark.asymptote`: not reached (2 of 3 required plans applied; last deltas 9.59, 2.05 pp).
* Scope of triage: the **12 tuning-split failures only**. No holdout question is listed or cited.
* Evidence: x-004, x-008, x-042, x-055 re-run read-only on the dev metric views (Genie SQL and rendered `expected_sql`, row counts and first 6 rows compared); x-048 checked in iteration 2 (S10). The other 7 are carried benchmark-defect candidates, not re-run.
* Ladder order: metric view (1-7), glossary (8), agent (9-10). One agent-layer action (G1) is planned, backed by the completed x-004 exhaustion record below.

## Data facts checked (read-only, dev target)

* `Customer Purchase Band` values: `2-5 purchases`, `6-10 purchases`, `11+ purchases`. x-042: Genie filtered `= '11+'` (0 customers per continent; expected 55 / 53 / ...).
* `Supplier Size` (mv_bakehouse_supplier_coverage) values: S, M, L, XL, XXL, Unknown (21 stores with no supplier). x-008: Genie joined sales to the coverage view and dropped `Unknown` (5 rows); the expectation keeps it (6 rows, Unknown = 33537). Supplier Size is not a dimension of mv_bakehouse_sales, so Genie had to join two views itself.
* x-055: after S8 Genie returns the same 10 suppliers and values as the expectation; the only difference is `ROUND(..., 2)` in the expectation.
* x-004: Genie still uses `RANK() <= 10` and returns 11 rows (tie at rank 10).

## Actions by metric view

### mv_bakehouse_sales

| # | Ladder step | Category | Question ids | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| S12 | 6 (new dimension) | Filter / edge | x-008 | Add `Supplier Size` = `COALESCE(franchise.supplier.size, 'Unknown')` (same pattern as C4's Supplier Name / Approved), comment: exact values S, M, L, XL, XXL, Unknown; 'Unknown' = stores with no supplier on file, keep it in breakdowns unless the question excludes those stores | Single-view breakdown with the Unknown row; 6 rows | applied | x-008 fixed: Genie groups mv_bakehouse_sales by `Supplier Size`, 6 rows incl. Unknown = 33537. Synonyms `supplier size band`, `vendor size` added |

### mv_bakehouse_supplier_coverage

| # | Ladder step | Category | Question ids | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| C9 | 1 (comment) | Filter / edge | x-008 | `Supplier Size` comment: exact values S, M, L, XL, XXL, Unknown; 'Unknown' = the 21 stores with no supplier on file; keep it in breakdowns by supplier attributes unless the question excludes stores without a supplier | Unknown row kept | applied | Comment applied (also points to the new sales dimension); x-008 fixed |

### mv_bakehouse_customer_activity

| # | Ladder step | Category | Question ids | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| A3 | 1 (comment) | Filter / edge | x-042 | `Customer Purchase Band` comment: exact values '2-5 purchases', '6-10 purchases', '11+ purchases'; '11 or more times' means = '11+ purchases'; filter with = on the exact value | Heavy-buyer counts non-zero | applied | x-042 fixed: Genie filters `= '11+ purchases'`. Comment lists all five CASE values (current data has the last three) |

### Agent (bakehouse_retail_sales_agent)

| # | Ladder step | Category | Question ids | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| G1 | 9 (one text instruction) | Ambiguity | x-004 | One instruction: "For 'top N' / 'which N' questions, return exactly N rows: ORDER BY the measure DESC, then the name, and LIMIT N (not RANK() <= N, which returns extra rows on ties)." Render with `--check`, redeploy ontology-genie-agents. Exhaustion record below is complete | x-004 returns 10 rows | applied | x-004 fixed (ORDER BY ... LIMIT 10). Regressed x-047: the "then the name" tie-break made Genie order tied stores by Franchise Name instead of Franchise ID; net 0. Partial revert of the tie-break clause planned in tuning_plan_04 (G1r) |

## benchmark_defect (for the owner; not tuned)

a-045, a-046, b-039 (expectation adds a column not asked for), a-061 (adds a constant `Franchise ID` column), b-042, x-018 (from plan 01), x-035 (Genie adds a `USA` row with 0), x-048 (verified in iteration 2: the expectation drops prior-day sales of stores with no sale on 2024-05-16; Genie's 1755 is the correct total), x-055 (rounding only, after S8).

## Classification count

12 tuning failures, each with exactly one category: Filter / edge 2 (x-008, x-042); Ambiguity 1 (x-004); Benchmark defect 9 (a-045, a-046, a-061, b-039, b-042, x-018, x-035, x-048, x-055).

## Exhaustion records

```json
{"question_id": "x-004", "category": "Ambiguity",
 "tried": [{"step": 1, "iteration": 2, "result": "not applicable: tie handling in top-N is not measure or dimension metadata; S8 (Supplier Name comment, iteration 2) applied and x-004 still fails on the tie"},
           {"step": 2, "iteration": 2, "result": "not applicable: Genie picks the right measure and dimension"},
           {"step": 3, "iteration": 2, "result": "not applicable: names are right"},
           {"step": 4, "iteration": 2, "result": "not applicable: values match"},
           {"step": 5, "iteration": 2, "result": "not applicable: measure expression is right"},
           {"step": 6, "iteration": 2, "result": "not applicable: no missing measure or dimension"},
           {"step": 7, "iteration": 2, "result": "not applicable: single-view answer, no join problem"},
           {"step": 8, "iteration": 2, "result": "not applicable: no glossary term covers top-N"}],
 "confirmed_failing": {"iteration": 2, "eval_run_id": "01f1eb035de91aad886e10d893b5fefc", "detail": "RANK() <= 10 returns 11 rows"}}
```

Complete: every step 1-8 is recorded with a reason, and iteration 2 confirmed x-004 still fails. G1 is the only agent-layer change and does not restate metric view metadata.
