# Tuning Plan 06 - Bakehouse Retail Sales Agent

* Source: iteration 5, Genie eval run `01f1eb1ac8b81eafb4ed2a621d77348a`, started 2026-11-28T10:59:29Z (build run 409860738864401, session 16). See `docs/tuning/iterations/05.md`.
* Current: tuning 133/146 (91.1%; best 135/146 in iteration 4), holdout 36/41 (87.8%, numbers only; best 37/41 in iteration 3). `benchmark.asymptote`: not reached (5 plans; last deltas +1.37, -1.37 pp; holdout gap 2.4 pp > 2.0 pp tolerance; `exhausted=False`, one plan left before `MAX_FIX_ITERATIONS` = 6).
* Scope of triage: the **13 tuning-split failures only**. No holdout question is listed or cited.
* Evidence: the 3 regressions (x-047, b-044, x-016) re-run read-only on the dev metric views (Genie SQL and rendered `expected_sql`, full result sets compared). The other 10 are carried benchmark-defect candidates, not re-run.
* Ladder order: metric view (1-7), glossary (8), agent (9-10). No new agent instruction or example SQL; no agent change in this plan.

## Data facts checked (read-only, dev target)

* b-044: `samples.bakehouse.sales_suppliers.ingredient` has 27 distinct values, all lowercase (almonds, anise, cacao, cane sugar, cardamom, cashews, cinnamon, cloves, cocoa butter, coconut, coffee, fennel seeds, ginger, hazelnuts, honey, mace, maple syrup, molasses, nutmeg, oats, peanuts, pecans, pistachios, poppy seeds, raisins, sesame seeds, vanilla). `= 'Almonds'` returns 0 stores, `= 'almonds'` returns 1.
* x-047: on 2024-05-16 two stores tie at comparable growth 1.0 for ranks 9-10. Ordering ties by Franchise Name keeps 3000046 (Baked Bliss); ordering by Franchise ID keeps 3000007 and 3000020 (the expectation). Ranks 1-8 agree.
* x-016: Genie's 12 `Product Mix` values equal the expectation's `product_share` to 4 decimals; the expectation adds `gross_sales`.

## Decision on the agent layer (plan 05 decision rule, case 2)

R1 raised holdout from 34 to 36 of 41 and regressed x-047. Keep R1 (the G1 text). Do not re-apply G1r and do not add a tie-break instruction. Fix x-047 in the metric view instead (S16), so the name in "then the name" resolves to the identifier through the view metadata.

## Actions by metric view

### mv_bakehouse_sales

| # | Ladder step | Category | Question ids | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| S16 | 1 (comment) | Ambiguity | x-047 | `Franchise Name` comment: append "Never use it to order or break ties when ranking stores: two stores share a name; ORDER BY the measure, then Franchise ID." | x-047 tie broken by Franchise ID; x-004 unchanged | planned | |

### mv_bakehouse_supplier_coverage

| # | Ladder step | Category | Question ids | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| C11 | 1 (comment) | Filter / edge | b-044 | `Supplier Ingredient` comment: append "Values are stored in lowercase (for example 'almonds', 'cane sugar', 'cocoa butter'); filter with = on the lowercase value, so 'Almonds' means = 'almonds'." | b-044 returns 1 store | planned | |

### Agent (bakehouse_retail_sales_agent)

No change (R1 kept, see decision above).

## benchmark_defect (for the owner; not tuned)

a-045, a-046, b-039, b-010, x-016 (expectation adds a column not asked for), a-061 (adds a constant `Franchise ID` column), b-042, x-018 (from plan 01), x-035 (Genie adds a `USA` row with 0), x-048 (verified in iteration 2: the expectation drops prior-day sales of stores with no sale on 2024-05-16), x-055 (rounding only).

## Classification count

13 tuning failures, each with exactly one category: Ambiguity 1 (x-047); Filter / edge 1 (b-044); Benchmark defect 11 (a-045, a-046, a-061, b-010, b-039, b-042, x-016, x-018, x-035, x-048, x-055).

## Exhaustion records

No new agent instruction or example SQL is planned, so no new record is needed. Ladder history for x-047 (for the record, if a later iteration considers an agent change):

```json
{"question_id": "x-047", "category": "Ambiguity",
 "tried": [{"step": 1, "iteration": 4, "result": "fixed together with G1r (S13, Franchise ID comment)"},
           {"step": 1, "iteration": 6, "result": "planned (S16, Franchise Name comment)"}]}
```

Agent changes since the baseline: G1 (plan 03), G1r (plan 04, text removal), R1 (plan 05, revert of G1r, kept).
