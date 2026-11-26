# 2026-11-26: Wave 1-6, session 33: benchmark questions for the fulfillment and procurement views

Job run `1020175336236697`, task `w1-6_session`, continuation 0. Mode `edit` with `allow_execute`. Branch `mg-genie-ontology-build-1-plan`, checked read-only: the Git folder was clean and on that branch. No Git writes, deploys, DDL or Pages writes.

Skill source: the session runner skill loaded from Unity Catalog (`hls_fde_dev.dev_matthew_giglia_build_waves.genie_build_session_runner`). The `ontology-tuning` skill was not loaded; I followed the method in plans 32 and 33 and the INDEX contract.

## What was done

* Wrote 69 single-view benchmark questions (`f001`-`f069`) in `examples/tpch/docs/tuning/benchmark/fulfillment_procurement.yml`:
  * fulfillment: 18 questions
  * returns: 17
  * profit: 17
  * supply_cost: 17
  * The plan asked for 60-120 in total and at least 15 per view.
* Every question has tokenized `expected_sql` (`MEASURE()` over `${target_catalog}.${target_schema}.<mv>`) and the tags `type:`, `view:`, `measure:` and `dimension:`. The 30 questions with a scalar, non-NULL result also have `expected_answer`.
* Ratio unit traps (observation 30): f028-f031 ask about `Return Rate` / `Return Line Rate`. Three of them ask for a percentage, and all four expect the 0-1 fraction.
* Wrote `fulfillment_procurement_notes.md` with the per-view counts and type mix, the statement state of every id, the edge questions with NULL results, and the one reworded question (f069, reworded to avoid a tie).

## Checks

| Check | Result | Detail |
|---|---|---|
| expected_sql runs | pass | 69 of 69 `SUCCEEDED` on the resolved target's warehouse through the Statement Execution API (read-only SELECTs). Re-run from the written file: 69 of 69 `SUCCEEDED` |
| expected_answer recheck | pass | 30 scalar answers match a fresh run within relative 1e-4 |
| file round trip | pass | `benchmark.load_questions` loads 69 questions; ids, text, SQL, tags and answers match the generated set |
| benchmark coverage (this file) | pass | Every measure and dimension of the four views is tagged; at least 17 questions per view. The only reported problems apply to the whole set: 69 < 100, cross-view 0% and no `cross_view` type. Sessions 32 and 34 provide those |
| type mix per view | pass | At least 2 questions of each type per view, except `time` on supply_cost, which has no date column |
| no resolved names in YAML | pass | Every SQL statement uses the tokens, and the YAML has no resolved catalog or schema string |

Split preview (`assign_splits`): 60 tuning, 9 holdout.

## Decisions and notes

* Statement ids are not recorded in the committed notes file, because workspace-specific ids belong in `docs/sessions/`.
* For the supply_cost view, the two `ratio` questions divide measures in the query: a `MEASURE() FILTER` share in f062 and value per offer in f063. That view has no ratio measure of its own.

## Files

* `examples/tpch/docs/tuning/benchmark/fulfillment_procurement.yml` (new)
* `examples/tpch/docs/tuning/benchmark/fulfillment_procurement_notes.md` (new)

## Requests

None.
