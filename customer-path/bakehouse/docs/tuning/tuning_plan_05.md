# Tuning Plan 05 - Bakehouse Retail Sales Agent

**Status: applied** in iteration 5 (build run 409860738864401, session 16; eval run `01f1eb1ac8b81eafb4ed2a621d77348a`). Result: tuning 133/146 (91.1%), holdout 36/41 (87.8%). See `docs/tuning/iterations/05.md`.

* Source: iteration 4, Genie eval run `01f1eb12ed5416b4899a1792a7e7a3c6`, started 2026-11-28T10:03:14Z (build run 409860738864401, session 15). See `docs/tuning/iterations/04.md`.
* Current: tuning 135/146 (92.5%, best so far), holdout 34/41 (82.9%, numbers only; best 37/41 in iteration 3). `benchmark.asymptote`: not reached (4 plans; last deltas -0.68, +1.37 pp; holdout gap 7.3 pp > 2.0 pp tolerance).
* Scope of triage: the **11 tuning-split failures only**. No holdout question is listed or cited.
* Evidence: the 1 regression (x-021) re-run read-only on the dev metric views (Genie SQL and rendered `expected_sql`, full result sets compared). The other 10 are carried benchmark-defect candidates, not re-run.
* Ladder order: metric view (1-7), glossary (8), agent (9-10). No new agent instruction or example SQL.

## Data facts checked (read-only, dev target)

* x-021: Genie and the expectation agree on all six supplier continents (Africa, Asia, Central America, Europe, North America, South America: 1.0 stores per supplier; units 903, 3959, 75, 2432, 1225, 2384). Genie adds a seventh row `Unknown` (stores with no supplier on file: stores-per-supplier null, 11179 units). The expectation filters `Supplier Status = 'Supplier on file'`. No plan 04 change touches mv_bakehouse_supplier_coverage; the `Supplier Continent` comment lists `Unknown` as a value and does not say that per-supplier questions exclude it.

## Overfitting response (ontology-tuning stop rule)

Holdout fell 7.3 pp (37 -> 34 of 41) while the tuning split rose 1.4 pp. The rule says to revert the latest agent-layer change first. In iteration 4 that was G1r. The metric view changes (S13, S14, S15, A4) are comment-only and each fixed its targeted tuning question with no tuning regression, so they stay.

## Actions by metric view

### mv_bakehouse_supplier_coverage

| # | Ladder step | Category | Question ids | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| C10 | 1 (comment) | Filter / edge | x-021 | `Supplier Continent` comment: add "'Unknown' is not a supplier: for per-supplier figures (stores per supplier, Franchises per Supplier, supplier counts) filter Supplier Status = 'Supplier on file' so no Unknown row is returned; keep Unknown only for store breakdowns that include stores without a supplier." Also append the same per-supplier rule to the `Franchises per Supplier` measure comment | x-021 returns the six continents only | applied | Fixed: x-021 passes (registered by run 370009555972263); no supplier-coverage question regressed on the per-supplier rule |

### Agent (bakehouse_retail_sales_agent)

| # | Ladder step | Category | Question ids | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| R1 | revert (G1r) | overfitting | holdout (numbers only); watch x-047, x-004 | Revert G1r: restore the plan 03 G1 text "ORDER BY the measure DESC, then the name, and LIMIT N". No new instruction (it is the exact text of G1, already backed by the x-004 exhaustion record). Render with `--check`, redeploy ontology-genie-agents | Holdout returns within 2.0 pp of its best (>= 37/41 is not required, gap <= 2.0 pp is); x-004 stays fixed; x-047 should hold through S13 (Franchise ID tie-break in the metric view) | applied | Holdout +2 (34 -> 36 of 41, gap 2.4 pp, not yet within 2.0 pp); x-004 stays fixed; x-047 regressed (Genie breaks the 1.0 tie by Franchise Name, as the restored text says). Decision rule case 2 applies: see tuning_plan_06.md |

Decision rule for iteration 6 (plan 06): if holdout does not recover after R1, the drop is not caused by G1r: re-apply G1r (G1r fixed x-047 on the tuning split) and record the holdout swing as evaluation variance. If holdout recovers and x-047 regresses, keep R1 and do not add a tie-break instruction without an x-047 exhaustion record (S13 = step 1 tried in iteration 4).

## benchmark_defect (for the owner; not tuned)

a-045, a-046, b-039, b-010 (expectation adds a column not asked for), a-061 (adds a constant `Franchise ID` column), b-042, x-018 (from plan 01), x-035 (Genie adds a `USA` row with 0), x-048 (verified in iteration 2: the expectation drops prior-day sales of stores with no sale on 2024-05-16), x-055 (rounding only).

## Classification count

11 tuning failures, each with exactly one category: Filter / edge 1 (x-021); Benchmark defect 10 (a-045, a-046, a-061, b-010, b-039, b-042, x-018, x-035, x-048, x-055).

## Exhaustion records

No new agent instruction or example SQL is planned, so no new record is needed. R1 restores the exact plan 03 G1 text, which is backed by the x-004 record in `tuning_plan_03.md` (carried in `tuning_plan_04.md`). Agent changes since the baseline: G1 (plan 03), G1r (plan 04, text removal), R1 (plan 05, revert of G1r).
