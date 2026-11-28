# Cross-view benchmark notes (session 10c)

* File: `docs/tuning/benchmark/cross_view.yml`, 59 questions (`x-001` .. `x-059`), every one tagged with two or more `view:` tags (56 two-view, 3 three-view: x-043, x-044, x-045).
* Checked 2026-11-28. Every `expected_sql` was rendered (`${target_catalog}.${target_schema}` = the dev target from `docs/registration/resolved_target.json`) and run read-only on SQL warehouse `24087b85239cacac` through the Statement Execution API. All 59 returned state `SUCCEEDED`.

## Join paths used

| Views | Key | Notes |
|---|---|---|
| sales <-> supplier_coverage | `Franchise ID` | Per-store join. Base measures are summed after the join; ratios are recomputed from base measures, never averaged |
| sales <-> supplier_coverage | `Franchise Country` / `Franchise Size` | Side-by-side group comparisons |
| sales <-> customer_activity | `Customer Country` / `Continent` / `State` / `Gender` | `mv_bakehouse_sales` has no `Customer ID` dimension, so no per-customer join is possible; `<=>` is used for nullable keys |
| customer_activity <-> supplier_coverage | country | Customer 'USA' maps to franchise 'US' (x-043) |

## Statement states

| id | state | rows |
|---|---|---|
| x-001 | SUCCEEDED | 2 |
| x-002 | SUCCEEDED | 2 |
| x-003 | SUCCEEDED | 28 |
| x-004 | SUCCEEDED | 10 |
| x-005 | SUCCEEDED | 1 |
| x-006 | SUCCEEDED | 7 |
| x-007 | SUCCEEDED | 2 |
| x-008 | SUCCEEDED | 6 |
| x-009 | SUCCEEDED | 34 |
| x-010 | SUCCEEDED | 6 |
| x-011 | SUCCEEDED | 9 |
| x-012 | SUCCEEDED | 9 |
| x-013 | SUCCEEDED | 5 |
| x-014 | SUCCEEDED | 1 |
| x-015 | SUCCEEDED | 2 |
| x-016 | SUCCEEDED | 12 |
| x-017 | SUCCEEDED | 6 |
| x-018 | SUCCEEDED | 10 |
| x-019 | SUCCEEDED | 9 |
| x-020 | SUCCEEDED | 9 |
| x-021 | SUCCEEDED | 6 |
| x-022 | SUCCEEDED | 5 |
| x-023 | SUCCEEDED | 10 |
| x-024 | SUCCEEDED | 9 |
| x-025 | SUCCEEDED | 10 |
| x-026 | SUCCEEDED | 18 |
| x-027 | SUCCEEDED | 3 |
| x-028 | SUCCEEDED | 6 |
| x-029 | SUCCEEDED | 3 |
| x-030 | SUCCEEDED | 3 |
| x-031 | SUCCEEDED | 3 |
| x-032 | SUCCEEDED | 10 |
| x-033 | SUCCEEDED | 2 |
| x-034 | SUCCEEDED | 17 |
| x-035 | SUCCEEDED | 2 |
| x-036 | SUCCEEDED | 17 |
| x-037 | SUCCEEDED | 1 |
| x-038 | SUCCEEDED | 3 |
| x-039 | SUCCEEDED | 3 |
| x-040 | SUCCEEDED | 2 |
| x-041 | SUCCEEDED | 48 |
| x-042 | SUCCEEDED | 15 |
| x-043 | SUCCEEDED | 9 |
| x-044 | SUCCEEDED | 3 |
| x-045 | SUCCEEDED | 3 |
| x-046 | SUCCEEDED | 21 |
| x-047 | SUCCEEDED | 10 |
| x-048 | SUCCEEDED | 2 |
| x-049 | SUCCEEDED | 288 |
| x-050 | SUCCEEDED | 144 |
| x-051 | SUCCEEDED | 3 |
| x-052 | SUCCEEDED | 6 |
| x-053 | SUCCEEDED | 24 |
| x-054 | SUCCEEDED | 1 |
| x-055 | SUCCEEDED | 10 |
| x-056 | SUCCEEDED | 10 |
| x-057 | SUCCEEDED | 1 |
| x-058 | SUCCEEDED | 2 |
| x-059 | SUCCEEDED | 5 |

## Coverage (SDK 0.1.1 `benchmark.coverage`)

* Own file only: 59 questions, 59 cross-view (share 1.0); per view: sales 59, supplier_coverage 38, customer_activity 24. Types: cross_view 31, time 8, ratio 6, breakdown 4, filter 4, edge 3, synonym 3. Problems listed for the file alone, all expected to be covered by the combined set: fewer than 100 questions; `simple` unused; sales measures `Gross Sales All Products` and `Transaction Count All Payment Methods`, customer_activity `Customer ID`, supplier_coverage `Franchise Name` / `Franchise City` untagged in this file.
* Combined set (`group_a.yml` + `group_b.yml` + `cross_view.yml`, as on disk at check time): 187 questions, 59 cross-view (31.6%), per view customer_activity 58, sales 135, supplier_coverage 56, **no problems** (passes).

## Findings for later tuning

* `Franchises per Supplier` (supplier_coverage) fails with `DIVIDE_BY_ZERO` when a group has no supplier on file (e.g. grouped by `Supplier Continent` = 'Unknown'). x-021 filters to `Supplier Status = 'Supplier on file'`. Candidate MV fix: `try_divide` / NULLIF in that measure (and other ratio measures whose denominator can be 0).
* `mv_bakehouse_sales` has no `Customer ID` dimension, so per-customer questions that combine purchase bands with sales detail cannot be answered from metric views alone.
