# Session 36 (wave 1-8): TPC-H Tuning Iteration 1 (MV-First)

Build 1, branch `mg-genie-ontology-build-1-plan` (Git folder checked read-only: on branch, head fef41c1). Mode `edit`, `allow_deploy`. **Status: pass** (run 829522414538457, continuation 0, first attempt).

Skill source: session-runner UC skill `hls_fde_dev.dev_matthew_giglia_build_waves.genie_build_session_runner`; `skills/ontology-tuning` read from the workspace.

## Done

| Task | Result |
|---|---|
| 1. Apply `tuning_plan_01.md` | 18/18 actions applied, 0 reverted; each marked with a one-line outcome. Unverified details checked first: Ship Mode codes read from `samples.tpch.lineitem` (AIR, FOB, MAIL, RAIL, REG AIR, SHIP, TRUCK); High Priority definition copied from the YAML; new `Order Count` uses `COUNT(DISTINCT l_orderkey)` |
| 2. `mv_yaml validate` on `examples/tpch/ontology-metric-views/metric_views` | exit 0: 7 files, 0 errors, 0 warnings |
| 3. Metric-views bundle | `bundle validate --strict -t dev` OK; `bundle deploy -t dev` 0 changed / 3 unchanged (source-linked); `register_metric_views` run **260504764502059** (job 1000154254892119), started 13:21:20Z, SUCCESS (generate_manifest, register_each_mv, smoke_test, cardinality_test all SUCCESS) |
| 3. Spot check | `Order Count` (market share, 1996) = 1,141,556 = distinct orders in source; `Discount Share` = 0.049997 = Discount Revenue / Gross Sales |
| 4. Glossary + page | `national_market_share.md` updated; DRAFT page `05defcc6-0fa3-433b-9661-aeac09ef2dd7` re-upserted with `only_ids` (dry run: body only; live: updated; re-check: unchanged) |
| 5. Agent | agent file not changed, so no agent render or redeploy |
| 6. Evaluation | `benchmark.run_eval` eval run **01f1e99cec631b77b86afd76cfd9923e**, started 2026-11-26T13:26:01Z, DONE. Tuning **92.7% (177/191)**, +8.9 pp; holdout **92.9% (39/42)**, +9.5 pp |
| 6. History | `accuracy_history.json` entry iteration 1 `tuning_plan_01` with changes by ladder step (steps 1, 2, 4, 6, 8) |
| 7. `iterations/01.md` | per split, per view, per type, delta, movement (fixed 18, still failing 13, regressed 1: x063), one-category triage, benchmark defects |
| 9. Asymptote | not reached (1 plan applied, needs at least 3) |
| 9. `tuning_plan_02.md` | 6 actions on steps 1, 5, 6, 8; no agent step; progress records for partly fixed questions |

## Decisions and caveats

* Plan-01 actions 4 and 5 were applied to both views each question uses (Ship Mode in fulfillment and returns; High Priority in fulfillment and orders), which is inside the action's intent.
* Action 1 (percentage format) was already present at baseline; the iteration strengthened the comments.
* x063 regressed, but no plan-01 change touches it (the returns view has no Order Year dimension). The net gain is +17, so nothing is reverted; plan 02 action 1 adds the dimension.
* x042 is reclassified as `benchmark_defect`: the expected SQL adds columns the question does not ask for. Benchmark defects for the owner: f029, f030, f031, x045, x078, x101, x042.
* The eval-run results had no result rows (same as baseline), so triage compares SQL text only.
* No holdout id is cited in `tuning_plan_01.md`, `tuning_plan_02.md` or `iterations/01.md` (checked against `assign_splits`).
* `accuracy_history.json` and the first part of `iterations/01.md` were written by the SDK helpers `append_history` / `write_iteration_md` (Python file writes). The added sections were written with the workspace file tools.

## Files and assets

* Modified: 6 metric view YAMLs (`returns`, `fulfillment`, `market_share`, `revenue`, `profit`, `orders`), `examples/tpch/docs/semantics/national_market_share.md`, `examples/tpch/docs/tuning/tuning_plan_01.md`, `examples/tpch/docs/tuning/accuracy_history.json`.
* Created: `examples/tpch/docs/tuning/iterations/01.md`, `examples/tpch/docs/tuning/tuning_plan_02.md`.
* Assets: 7 metric views re-registered in the dev target schema (run 260504764502059); DRAFT page 05defcc6 updated; one new eval run on the dev Genie space `01f1e8a428241105b01bbc2f4e355e30`.

## Requests

* Owner (normal): review the 7 benchmark defects listed in `tuning_plan_02.md`.
* Session 37 (iteration 2): apply `tuning_plan_02.md`. Action 6 updates the `return_rate` page `b25a694d-21dc-4ec7-9c91-acdfcea5a278` (a session-31 id, so it is inside the approval).
