# Tuning Plan 01 — Bakehouse Retail Sales Agent

* Source: baseline (iteration 0), Genie eval run `01f1eaf3c4a8155bbf2f167f93d93a39`, started 2026-11-28T06:20:12Z (build run 409860738864401, session 11). See `docs/tuning/iterations/00_baseline.md` and `docs/tuning/accuracy_history.json`.
* Baseline: tuning split 117/146 (80.1%), holdout 33/41 (80.5%, numbers only). 186/187 generated SQL that succeeded; 0 `unit_mismatch`, 0 `needs_review`.
* Scope of triage: the **29 tuning-split failures only**. No holdout question is listed or cited.
* Evidence: the Genie eval run returns the verdict (`BAD`) and Genie's SQL, but no result rows. Each failure was classified by comparing Genie's SQL with `expected_sql`, plus read-only checks of dimension values on the dev metric views (below). Value-level differences were not re-run per question; iteration 1 confirms each fix.
* Ladder order: metric view (steps 1-7) first, glossary (8) next, agent (9-10) last. No agent-layer action is planned: no exhaustion record exists yet.

## Data facts checked (read-only, dev target)

* `Franchise Country ILIKE '%US%'` matches both `US` and `Australia`.
* `Franchise Size` values: `S`, `M`, `L`, `XL`, `XXL` (`ILIKE '%XL%'` also matches `XXL`).
* `Customer State` mixes codes and names: `CA`, `California`; `ILIKE '%CA%'` also matches `South Carolina`.
* `Supplier Status` values: `Supplier on file`, `No supplier on file`; `Supplier Approved` values: `Y`, `Unknown`. Genie used values that do not exist (`Matched supplier`, `%match%`, `%unknown%`).

## Actions by metric view

### mv_bakehouse_sales

| # | Ladder step | Category | Question ids | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| S1 | 1 (comment) | Filter / edge | a-075, b-024, a-067 | `Franchise Country` comment: exact country values (for example `US` and `Australia` are distinct values); filter with `=`, never `ILIKE` | US filters stop pulling in Australia | planned | |
| S2 | 1 (comment) | Filter / edge | a-066 | `Franchise Size` comment: exact values `S`, `M`, `L`, `XL`, `XXL`; filter with `=` | XL stops matching XXL | planned | |
| S3 | 5 (expression) | Filter / edge | b-026 | Normalize `Customer State` to one form (map full names such as `California` to the 2-letter code) in the dimension expression; comment the convention | CA count includes California, excludes South Carolina | planned | |
| S4 | 2 (synonyms) | Synonym gap | a-061 | Synonyms `day-over-day change`, `daily change`, `vs prior day` on `Comparable Franchise Sales Growth (proxy)`, and comments on `Daily Gross Sales` / `Prior Day Gross Sales` that they are the day-over-day pair | Agent uses the three measures instead of its own `LAG` | planned | |
| S5 | 4 (format) | Unit / format | b-017, a-045 | `format: percentage` on `Comparable Franchise Sales Growth (proxy)` and `Product Mix`, and comment "0-1 ratio; do not multiply by 100" | Agent stops scaling ratios by 100 | planned | |
| S6 | 1 (comment) | Ambiguity | a-080 | `Sales per Franchise` comment: already an average per store for the grouping; do not group by `Franchise ID` unless a per-store list is asked | One row per week, not per store | planned | |
| S7 | none | Benchmark defect | b-010, b-013 | Report only. b-010: Genie returned the correct `Product Mix` measure; the expectation also requires `Gross Sales All Products`, which the question does not ask for. b-013: Genie's SQL is equivalent except `date_trunc('DAY', ...)` returns a timestamp | Owner review; do not tune | n/a | |

### mv_bakehouse_supplier_coverage

| # | Ladder step | Category | Question ids | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| C1 | 1 (comment) | Synonym gap | x-001, x-004, x-009, x-048 | `Supplier Status` comment listing exact values `Supplier on file` / `No supplier on file`, and that it (not `Supplier Name`) splits stores with and without a supplier | Agent groups or filters on the real values | planned | |
| C2 | 2 (synonyms) | Synonym gap | x-010, x-015 | Synonyms on `Supplier Approved` (`approved vendor`, `certified vendor`, `approved supplier`), and comment with values `Y` / `Unknown` | Agent groups by `Supplier Approved` directly instead of relabeling | planned | |
| C3 | 1 (comment) | Ambiguity | b-039 | Comments separating `Approved Supplier Share (Franchise Basis)` (share of all stores) from `(Supplier Basis)` (share of suppliers) | Agent picks the franchise basis for store questions | planned | |
| C4 | 7 (right-grain / join) | Join issue | x-002, x-007, x-055, x-059 | Bring `Supplier Status`, `Supplier Approved` and `Supplier Name` into `mv_bakehouse_sales` as dimensions via a LEFT join franchise -> supplier on `supplierID` (`docs/data_profiles/data_model_summary.md`: `one_to_one`, 21 of 48 franchises unmatched, so LEFT join only and label nulls) so ratio measures (`Average Transaction Value`, `Units per Transaction`, `Sales per Franchise`) are computed in one view | Agent stops computing ratios per store and then combining them itself after its own join (x-002: AVG of per-store ATV; x-055: per-store units per transaction ranked, not recomputed per supplier; x-007: per-store rows, not one value per group; x-059: own HAVING-based counts) | planned | |
| C5 | 1 (comment) | Unit / format | x-016 | Covered by S5 (`Product Mix` / share format): Genie computed the share then labelled it `_pct` (×100 risk) | Share returned as 0-1 ratio | planned | |
| C6 | none | Benchmark defect | b-042, x-018 | Report only. b-042: the expectation adds a `Franchise Count` column that the question does not ask for. x-018: the expectation adds `Franchise City`, which was not asked for | Owner review; do not tune | n/a | |

### mv_bakehouse_customer_activity

| # | Ladder step | Category | Question ids | Change | Expected effect | Status | Outcome |
|---|---|---|---|---|---|---|---|
| A1 | 5 (expression) | Filter / edge | x-043 | Harmonize `Customer Country` codes with `Franchise Country` (`USA` → `US`) in the dimension expression, plus a comment | Country joins across views line up without CASE remapping | planned | |
| A2 | 7 (join) | Join issue | x-035, x-036 | Comment on `Buying Customers` / `First Purchase Date` / `Last Purchase Date` about the grain, and with C4 and A1, check whether customer-country sales can be answered in one view. Genie used `FULL OUTER JOIN` across views and left NULLs where the expectation joins and uses 0 | Correct row set and zero handling | planned | |
| A3 | none | Benchmark defect (candidate) | x-056 | Genie's SQL (state sales + repeat customers, top 10 by receipts via `RANK`) looks equivalent to the expectation; ties or the `LEFT JOIN` may explain the verdict. Re-check after S3 (state normalization also changes this question) | Owner review | n/a | |

## Classification count

29 tuning failures, each with exactly one category: Filter / edge 6 (a-075, b-024, a-067, a-066, b-026, x-043); Synonym gap 7 (a-061, x-001, x-004, x-009, x-048, x-010, x-015); Unit / format 3 (b-017, a-045, x-016); Ambiguity 2 (a-080, b-039); Join issue 6 (x-002, x-007, x-055, x-059, x-035, x-036); Benchmark defect 5 (b-010, b-013, b-042, x-018, x-056).

## benchmark_defect (for the owner)

b-010, b-013, b-042, x-018, x-056 (candidate). The benchmark is frozen after this baseline; these are not edited during tuning.

## Exhaustion records

None (no agent-layer action planned).
