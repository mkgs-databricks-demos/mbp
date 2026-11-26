# 2026-11-26 - Wave 1-6, session 34: Cross-view benchmark questions

* Run `1020175336236697`, task `w1-6_session`, continuation 0. Mode: `edit` with `allow_execute`. Final status: **pass**.
* Branch: the Git folder `mbp` is on `mg-genie-ontology-build-1-plan` (checked read-only through the Repos API). No Git commands were run.
* Skills: the session-runner skill loaded from Unity Catalog (`hls_fde_dev.dev_matthew_giglia_build_waves.genie_build_session_runner`). No ontology skill was loaded. The method came from plan 32, the build-1 INDEX contract and `benchmark.py`.

## Context read

* Plans: build-1 34, 32 and INDEX (tuning protocol and question YAML contract).
* Session summaries: 22 (benchmark library) and 30 (registered views, `resolved_target.json`).
* `domain_manifest.yml`.
* The 7 registered metric views, read through `DESCRIBE TABLE EXTENDED ... AS JSON`. Session 30 recorded that these match the working-tree YAML.
* `benchmark.coverage` tag parsing, read in a /tmp copy:
  * Only the first `type:` tag counts.
  * Qualified `measure:<mv>.<name>` tags credit exactly one view.
  * A question with 2 or more `view:` tags counts as cross-view.

## Changes

* `examples/tpch/docs/tuning/benchmark/cross_view.yml` (new): 105 questions, `x001`-`x105`.
  * Views per question: 90 use 2 views, 14 use 3 and 1 uses 4.
  * The first tag is `type:cross_view`, followed by a secondary type, every `view:` the question needs, and qualified `measure:` and `dimension:` tags.
  * `expected_sql` has one `MEASURE()` CTE per view, joined on a shared dimension alias, and is tokenized with `${target_catalog}.${target_schema}`.
* `examples/tpch/docs/tuning/benchmark/cross_view_notes.md` (new):
  * The pair matrix: 16 pairs with a business meaning, each with 5-18 questions, plus 5 pairs excluded with reasons.
  * Every question id with its statement state and row count.
  * The questions that were changed, and the coverage results.

## Decisions

* **Size: 105 questions**, above the minimum of 60. The cross-view share of the whole set stays at 25% or more as long as sessions 32 and 33 together write no more than 315 questions.
* **Nation roles:** customer nation and supplier nation are joined only where the question is explicitly about demand versus supply base (orders / supply_cost, x029-x032, x092).
* **Returns time window:** returns questions use years before 1995. In this data, only older lines carry return flag `R`. x014 and x103 were moved to 1993 after the first runs gave zero or NULL returns.
* **Edge questions kept on purpose:**
  * x032 returns no rows.
  * x065 returns 0 returned lines in 1998.
  * The reconciliation questions x047, x096, x100, x104 and x105 compare the same quantity across two views. A full-result check confirmed a difference of 0 on every row.
* **No `expected_answer`:** every expectation is carried by `expected_sql`. Most results have several rows.

## Checks

| Check | Result |
|---|---|
| Every `expected_sql`, rendered with `resolved_target.json`, run read-only on the warehouse through the Statement Execution API | pass: 105/105 SUCCEEDED (run 1 from the generator, run 2 from the questions loaded back from the workspace file) |
| File on disk equals the generated YAML; parses; 105 unique ids | pass |
| No resolved catalog, schema or `samples.tpch` in the YAML | pass |
| `benchmark coverage` on this file alone (/tmp copy, 7 metric view YAMLs) | 105 questions; 100% cross-view; every view has 20 or more questions; every measure covered. The remaining problems are expected for one file: 8 single-view dimensions are not used, and only the `cross_view` type is counted |
| Wave gate `benchmark_coverage` over all three files | not run: `sales.yml` and `fulfillment_procurement.yml` (sessions 32 and 33, same wave) did not exist yet. The gate runs it |

## For sessions 32 and 33 and the gate

These dimensions are not covered by `cross_view.yml`, so the single-view files have to cover them:

* fulfillment: `Receipt Date`, `Receipt Month`, `Receipt Year`
* profit: `Part Name`
* returns: `Customer Name`
* supply_cost: `Part Key`, `Part Size`, `Supplier Name`

## Files modified

* `examples/tpch/docs/tuning/benchmark/cross_view.yml`
* `examples/tpch/docs/tuning/benchmark/cross_view_notes.md`
