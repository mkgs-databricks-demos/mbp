# Tuning Plan 02 — Bakehouse Retail Sales Agent

**Status: applied** in iteration 2 (build run 409860738864401, session 13). YAML registered by `register_metric_views` run 251284026050684 (SUCCESS); re-evaluated in eval run `01f1eb035de91aad886e10d893b5fefc` (tuning 134/146, 91.8%). See `docs/tuning/iterations/02.md`.

* Source: iteration 1, Genie eval run `01f1eafb99ba1a47ac5f2814b651116f`, started 2026-11-28T07:16:16Z (build run 409860738864401, session 12). See `docs/tuning/iterations/01.md`.
* Current: tuning 131/146 (89.7%), holdout 35/41 (85.4%, numbers only). `benchmark.asymptote`: not reached (1 of 3 required plans applied).
* Scope of triage: the **15 tuning-split failures only**. No holdout question is listed or cited.
* Evidence: for 10 failures (a-045, a-046, b-048, a-061, x-004, x-035, x-048, x-055, x-059, b-039), Genie's SQL and the rendered `expected_sql` were both re-run read-only on the dev metric views; row counts compared, and the first up to 6 rows of each inspected. The other 5 (b-010, b-013, b-042, x-018, x-056) are plan 01 benchmark-defect candidates and were not re-run in this iteration.
* Ladder order: metric view (1-7), glossary (8), agent (9-10). No agent-layer action is planned; one exhaustion record is started (x-004).

## Data facts checked (read-only, dev target)

* `Supplier Continent` values: Africa, Asia, Central America, Europe, North America, South America, Unknown. `ILIKE '%European%'` matches none (b-048 returned 0; expected 5).
* x-004: Genie's `RANK() <= 10` returns 11 rows because ranks 10 tie at 1212 (Cinnamon Spice, Raisin Ranch); the expectation uses `LIMIT 10`.
* x-055: Genie's top 10 includes `Unknown supplier` (rank 4); the expectation keeps `Supplier Status = 'Supplier on file'` only.
* x-059: Genie's share is 100.0 where the expectation is 1.0 (Genie multiplied its own ratio by 100).
* x-048: for `Supplier on file` on 2024-05-16, Genie's `Prior Day Gross Sales` is 1755 vs expected 1647 (`No supplier on file` matches: 2073 / 2049). Genie grouped the window measure by `Supplier Status` in mv_bakehouse_sales; the expectation sums per-store rows. Cause not yet verified.

## Actions by metric view

### mv_bakehouse_supplier_coverage

| # | Ladder step | Category | Question ids | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| C7 | 1 (comment) | Filter / edge | b-048 | `Supplier Continent` comment: exact values (Africa, Asia, Central America, Europe, North America, South America, Unknown); filter with `=`, never `ILIKE`; 'European' means `= 'Europe'` | Agent filters `= 'Europe'` | applied | b-048 fixed (filters `= 'Europe'`) |
| C8 | 2 (synonyms) | Synonym gap | b-048 | Synonyms `approved vendors`, `number of approved suppliers` on `Approved Suppliers` | Agent uses `Approved Suppliers` instead of `Supplier Count` + filter | applied | b-048 fixed (with C7); also added synonym `number of approved vendors` and a usage note on the comment |

### mv_bakehouse_sales

| # | Ladder step | Category | Question ids | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| S8 | 1 (comment) | Filter / edge | x-055 | `Supplier Name` comment: 'Unknown supplier' is not a supplier; when ranking or listing suppliers, filter `Supplier Status = 'Supplier on file'` | Unknown supplier no longer ranked | applied | Worked: x-055 now filters `Supplier on file`, same 10 suppliers and values; still BAD on rounding only (expectation `ROUND(...,2)`) -> benchmark_defect |
| S9 | 1 (comment) | Unit / format | x-059 | View and `Franchises with Sales` comments: shares and rates are returned as 0-1 fractions; do not multiply by 100, including ratios computed from two measures | Share returned as 1.0, not 100.0 | applied | x-059 fixed |
| S10 | 1 (comment), after a read-only check | Filter / edge | x-048 | First verify read-only why `Prior Day Gross Sales` grouped by `Supplier Status` with a `Transaction Date` filter differs from the per-store sum (stores without a sale that day?). Then document the behaviour on `Prior Day Gross Sales` / `Daily Gross Sales`; if the measure is wrong for this grouping, consider step 5 | Supplier-on-file prior day = 1647 | applied (comment) | Check: the measure is right. Grouped by Supplier Status it returns 1755 = `Gross Sales` of 2024-05-15 for that group; the expectation's 1647 drops stores with no sale on 2024-05-16. No step 5. x-048 reclassified benchmark_defect; comment documents the grouping behaviour |
| S11 | none (exhaustion record started) | Ambiguity | x-004 | No metric view step applies to top-N tie handling (it is not a property of a measure or dimension). Record only; reconsider in plan 03 if it recurs | n/a | record only | x-004 still fails in iteration 2 (RANK tie, 11 rows); exhaustion record completed in plan 03 |

## benchmark_defect (for the owner; not tuned)

a-045, a-046, b-039 (Genie's values equal the expectation; the expectation adds a column not asked for), a-061 (same values on the rows inspected; the expectation adds a constant `Franchise ID` column), x-035 (Genie adds a `USA` row with 0 for "each customer home country"), and from plan 01: b-010, b-013, b-042, x-018, x-056 (candidate). a-046 passed at baseline with unchanged fields; its regression looks like grading variance on the extra column.

## Classification count

15 tuning failures, each with exactly one category: Filter / edge 3 (b-048, x-055, x-048); Unit / format 1 (x-059); Ambiguity 1 (x-004); Benchmark defect 10 (a-045, a-046, a-061, b-010, b-013, b-039, b-042, x-018, x-035, x-056).

## Exhaustion records

```json
{"question_id": "x-004", "category": "Ambiguity",
 "tried": [{"step": 1, "iteration": 2, "result": "not applicable: tie handling in top-N is not measure or dimension metadata"},
           {"step": 2, "iteration": 2, "result": "not applicable"},
           {"step": 3, "iteration": 2, "result": "not applicable"},
           {"step": 4, "iteration": 2, "result": "not applicable"},
           {"step": 5, "iteration": 2, "result": "not applicable"},
           {"step": 6, "iteration": 2, "result": "not applicable"},
           {"step": 7, "iteration": 2, "result": "not applicable"},
           {"step": 8, "iteration": 2, "result": "not applicable: no glossary term covers top-N"}]}
```

Incomplete until iteration 2 confirms x-004 still fails; no agent change is planned in this plan.
