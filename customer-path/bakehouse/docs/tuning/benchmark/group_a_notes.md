# Benchmark notes: view group A (session 10a)

* Build run: 409860738864401, wave 6, session 10a. Date checked: 2026-11-28.
* File: `docs/tuning/benchmark/group_a.yml` (80 single-view questions, ids `a-001`..`a-080`).
* View group A: the first half of `ontology-metric-views/metric_views/manifest.json` by name, rounded up for 3 views: `mv_bakehouse_customer_activity`, `mv_bakehouse_sales`. Session 10b's `group_b.yml` also covers `mv_bakehouse_sales` (30 questions) plus `mv_bakehouse_supplier_coverage` (18). That overlap is harmless, and no ids collide.
* Execution: each `expected_sql` was rendered with the resolved target (`docs/registration/resolved_target.json`) and run read-only (SELECT only) on the project warehouse through the Statement Execution API. The SQL was re-run from the written file after the edit, not from the authoring copy.

## Statement states

All 80 statements: `SUCCEEDED`. Rows returned are listed for reference only; they are not graded.

| id | state | rows |
|---|---|---|
| a-001 | SUCCEEDED | 1 |
| a-002 | SUCCEEDED | 1 |
| a-003 | SUCCEEDED | 1 |
| a-004 | SUCCEEDED | 1 |
| a-005 | SUCCEEDED | 1 |
| a-006 | SUCCEEDED | 1 |
| a-007 | SUCCEEDED | 1 |
| a-008 | SUCCEEDED | 1 |
| a-009 | SUCCEEDED | 1 |
| a-010 | SUCCEEDED | 3 |
| a-011 | SUCCEEDED | 3 |
| a-012 | SUCCEEDED | 5 |
| a-013 | SUCCEEDED | 2 |
| a-014 | SUCCEEDED | 3 |
| a-015 | SUCCEEDED | 9 |
| a-016 | SUCCEEDED | 1 |
| a-017 | SUCCEEDED | 1 |
| a-018 | SUCCEEDED | 1 |
| a-019 | SUCCEEDED | 1 |
| a-020 | SUCCEEDED | 1 |
| a-021 | SUCCEEDED | 1 |
| a-022 | SUCCEEDED | 1 |
| a-023 | SUCCEEDED | 1 |
| a-024 | SUCCEEDED | 3 |
| a-025 | SUCCEEDED | 3 |
| a-026 | SUCCEEDED | 3 |
| a-027 | SUCCEEDED | 2 |
| a-028 | SUCCEEDED | 1 |
| a-029 | SUCCEEDED | 3 |
| a-030 | SUCCEEDED | 1 |
| a-031 | SUCCEEDED | 1 |
| a-032 | SUCCEEDED | 10 |
| a-033 | SUCCEEDED | 1 |
| a-034 | SUCCEEDED | 6 |
| a-035 | SUCCEEDED | 1 |
| a-036 | SUCCEEDED | 1 |
| a-037 | SUCCEEDED | 1 |
| a-038 | SUCCEEDED | 1 |
| a-039 | SUCCEEDED | 1 |
| a-040 | SUCCEEDED | 1 |
| a-041 | SUCCEEDED | 1 |
| a-042 | SUCCEEDED | 1 |
| a-043 | SUCCEEDED | 1 |
| a-044 | SUCCEEDED | 6 |
| a-045 | SUCCEEDED | 6 |
| a-046 | SUCCEEDED | 3 |
| a-047 | SUCCEEDED | 3 |
| a-048 | SUCCEEDED | 1 |
| a-049 | SUCCEEDED | 10 |
| a-050 | SUCCEEDED | 5 |
| a-051 | SUCCEEDED | 5 |
| a-052 | SUCCEEDED | 1 |
| a-053 | SUCCEEDED | 3 |
| a-054 | SUCCEEDED | 5 |
| a-055 | SUCCEEDED | 2 |
| a-056 | SUCCEEDED | 17 |
| a-057 | SUCCEEDED | 3 |
| a-058 | SUCCEEDED | 1 |
| a-059 | SUCCEEDED | 1 |
| a-060 | SUCCEEDED | 1 |
| a-061 | SUCCEEDED | 17 |
| a-062 | SUCCEEDED | 46 |
| a-063 | SUCCEEDED | 17 |
| a-064 | SUCCEEDED | 1 |
| a-065 | SUCCEEDED | 1 |
| a-066 | SUCCEEDED | 1 |
| a-067 | SUCCEEDED | 6 |
| a-068 | SUCCEEDED | 27 |
| a-069 | SUCCEEDED | 1 |
| a-070 | SUCCEEDED | 9 |
| a-071 | SUCCEEDED | 6 |
| a-072 | SUCCEEDED | 6 |
| a-073 | SUCCEEDED | 1 |
| a-074 | SUCCEEDED | 2 |
| a-075 | SUCCEEDED | 1 |
| a-076 | SUCCEEDED | 1 |
| a-077 | SUCCEEDED | 1 |
| a-078 | SUCCEEDED | 1 |
| a-079 | SUCCEEDED | 27 |
| a-080 | SUCCEEDED | 3 |

## Coverage (this file only)

`benchmark.coverage(load_questions(group_a.yml), [mv_bakehouse_customer_activity.yml, mv_bakehouse_sales.yml])` (SDK wheel 0.1.1):

* Per view: `mv_bakehouse_customer_activity` 34, `mv_bakehouse_sales` 46 (minimum 12 each: met).
* Every measure and dimension of both views is tagged at least once (0 untagged).
* Type mix: breakdown 15, edge 8, filter 11, ratio 9, simple 10, synonym 16, time 11.
* Problems reported for this file alone, all expected because they are checked on the combined set by the wave gate: 80 questions (< 100), cross-view share 0% (single-view file by scope), `cross_view` type unused (covered by session 10c's `cross_view.yml`).

## Edge cases encoded

* `a-030`: no customer has 0 purchases in the current data, so the expected answer is 0.
* `a-033` / `a-075`: country codes (`USA` for customers, `US` for stores).
* `a-074`: `Sugar Rush` names two stores; answer per `Franchise ID`.
* `a-076`: 2024-05-17 is a partial day.
* `a-077`: net sales is not modeled; the expected answer is gross sales, with the caveat.
