# Session 37 (wave 1-9): TPC-H Tuning Iteration 2 (MV-First)

Build 1, branch `mg-genie-ontology-build-1-plan` (Git folder checked read-only: on branch, tree clean at start). Mode `edit`, `allow_deploy`. **Status: pass** (run 829522414538457, continuation 0, first attempt).

Skill source: session-runner UC skill `hls_fde_dev.dev_matthew_giglia_build_waves.genie_build_session_runner`.

## Done

| Task | Result |
|---|---|
| 1. Apply `tuning_plan_02.md` | 5 applied, 1 reverted (not applied); each marked with a one-line outcome |
| 2. `mv_yaml validate` on `examples/tpch/ontology-metric-views/metric_views` | exit 0: 7 files, 0 errors, 0 warnings |
| 3. Metric-views bundle | `bundle validate --strict -t dev` OK; `bundle deploy -t dev` 0 changed / 3 unchanged (source-linked); `register_metric_views` run **997993635139017** (job 1000154254892119), 14:25:10Z to 14:28:57Z, TERMINATED SUCCESS (generate_manifest 7 views 0 warnings, smoke_test 7/7, cardinality_test 7/7) |
| 3. Spot check | returns `Order Year` gives integer years 1992-1998 (returned revenue NULL from 1996 on, as TPC-H flags returns only on older lines); `Average Discount` per ship mode = 0.0500 for all 7 modes = `ROUND(AVG(l_discount), 4)` on `samples.tpch.lineitem` |
| 4. Glossary / pages | no change (action 6 not applied), so no page upsert |
| 5. Agent | agent file not changed, so no render or redeploy |
| 6. Evaluation | eval run **01f1e9a5cbae1ec8817029d8fb8334e6** on space `01f1e8a428241105b01bbc2f4e355e30`, started 2026-11-26T14:29:31Z, DONE, 233/233 results. Tuning **94.2% (180/191)**, +1.6 pp; holdout **97.6% (41/42)**, +4.8 pp |
| 6. History | `accuracy_history.json` entry iteration 2 `tuning_plan_02` (steps 1, 5, 6) |
| 7. `iterations/02.md` | per split, per view, per type, delta, movement (fixed 4: x028, x046, x054, x063; still failing 10; regressed 1: f008), triage, benchmark defects |
| 9. Asymptote | not reached: 2 plans applied (needs 3); last deltas [8.9006, 1.5706] pp; holdout gap 0.0 |
| 9. `tuning_plan_03.md` | 1 action (step 1, fulfillment `Q12 Late Receipt Count` comment for f008); no agent step |

## Decisions

* **Action 6 (x062 glossary) not applied.** The plan asked to check first whether x062 is a grading-strictness defect. The agent already compares with the overall rate. The remaining gap is `ROUND(..., 5)`, which the question does not ask for, plus a LEFT JOIN that returns the same rows as the expected inner join. So x062 is reclassified as a benchmark defect, with no glossary or page write.
* x032 and x070 moved as intended (inner join; `LIMIT 1`). What still differs is an extra column (x032) or missing rounding (x070), neither asked for. Both are reclassified as grading-strictness benchmark defects, following plan 02's note not to add more metadata for these.
* f008 regressed. No plan-02 action touches the fulfillment view (the agent dropped `Ship Mode` from the grouping). Net gain is +3, so nothing is reverted; plan 03 action 1 targets it.
* Action 2 (rounding at the source) regressed no passing question.
* `accuracy_history.json` and the first part of `iterations/02.md` were written by the SDK helpers `append_history` / `write_iteration_md` (Python file writes, as in sessions 35-36). The added sections were written with the workspace file tools.
* No holdout id is cited in `tuning_plan_02.md`, `tuning_plan_03.md` or `iterations/02.md` (checked against `assign_splits`).

## Files and assets

* Modified: 5 metric view YAMLs (`returns`, `revenue`, `profit`, `supply_cost`, `market_share`), `examples/tpch/docs/tuning/tuning_plan_02.md`, `examples/tpch/docs/tuning/accuracy_history.json`.
* Created: `examples/tpch/docs/tuning/iterations/02.md`, `examples/tpch/docs/tuning/tuning_plan_03.md`.
* Assets: 7 metric views re-registered in `hls_fde_dev.dev_matthew_giglia_ontology` (run 997993635139017); one new eval run on the dev Genie space.

## Requests

* Owner (normal): review the 10 benchmark defects in `tuning_plan_03.md` (7 carried plus x032, x062, x070 for grading strictness).
* Session 38 (iteration 3): apply `tuning_plan_03.md` (one fulfillment YAML comment).
