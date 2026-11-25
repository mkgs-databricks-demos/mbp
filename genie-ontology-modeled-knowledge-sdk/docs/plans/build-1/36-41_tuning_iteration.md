# Sessions 36-41: TPC-H Tuning Iteration k (MV-First)

One plan for six sessions. The manifest `scope` gives `k`: 36 -> 1, 37 -> 2, 38 -> 3 (mandatory), 39 -> 4, 40 -> 5, 41 -> 6 (conditional). `kk` = two-digit `k`.

## Scope
Apply `tuning_plan_<kk>.md`, re-register and redeploy what changed, re-evaluate both splits, record the iteration, check the asymptote rule, and write the next tuning plan.

## Context
* [Exhaustive tuning protocol](INDEX.md#exhaustive-tuning-protocol-owner-request) and `skills/ontology-tuning` (fix ladder, exhaustion records, templates).
* **MV-first, always.** Unity Catalog semantic options come first: metric view `comment`, `synonyms`, `display_name`, `format`, expressions and `FILTER`, new measures or dimensions, join fixes or moving a measure to the right-grain view, glossary term + draft Page. An agent text instruction (ladder step 9) or example SQL (step 10, multi-step questions only) is allowed **only** for a failure whose exhaustion record shows every applicable step 1-8 was tried in an earlier iteration and did not fix it. Never restate metric view metadata in instructions; never add example SQL for a single-view, single-measure question.
* **Holdout:** read only holdout accuracy numbers, never holdout question text or failures. Do not edit `docs/tuning/benchmark/**` (benchmark changes would invalidate the curve; a wrong expectation is reported in the iteration file as `benchmark_defect` for the owner).
* Authorized: `bundle.deploy` of both TPC-H bundles (target dev), `jobs.run_now` of `register_metric_views`, `workspace.write` for DRAFT pages this build created (session 31's recorded ids only).
* Unattended rules: no Git, no file deletion; change metric view YAML, the agent file, glossary term files, `docs/pages/**` and `docs/tuning/**` only.

## Tasks
0. **Conditional start (k >= 4):** run `benchmark.asymptote` on `docs/tuning/accuracy_history.json`. If `reached` is true, write `docs/tuning/iterations/<kk>.md` with `converged at iteration <j>` and the asymptote output, change nothing else, and finish `pass` (session 41 still writes `tuning_summary.md`). Iterations 1-3 always run in full.
1. Apply every action in `tuning_plan_<kk>.md`; mark each `applied` or `reverted` with a one-line outcome.
2. `gos-validate-mv examples/tpch/ontology-metric-views/metric_views` exits 0.
3. If YAML changed: `bundle deploy -t dev` and `bundle run register_metric_views -t dev` on the metric-views bundle; all views pass smoke + cardinality (max 3 attempts; revert the breaking action otherwise).
4. If glossary terms changed: re-upsert those DRAFT pages with `only_ids` (session 31's ids).
5. If the agent file changed (steps 9-10 only, with exhaustion records): render with `--params ... --check` and `bundle deploy -t dev` on the agents bundle.
6. Re-evaluate with `benchmark.run_eval`; score per split; `append_history` (`iteration: k`, changes by ladder step).
7. Write `docs/tuning/iterations/<kk>.md` (accuracy per split, per view, per type; delta vs previous; fixed / regressed / still failing questions from the tuning split; `benchmark_defect` list).
8. Regressions: an action that broke previously passing questions is reverted in the next plan unless the net gain is positive and explained.
9. Run `benchmark.asymptote`. If k >= 3 and it is reached, record it in `iterations/<kk>.md` and write no further plan. Otherwise write `tuning_plan_<kk+1>.md` from fresh triage of remaining tuning-split failures (steps 1-8 first; steps 9-10 only with an exhaustion record).
10. **Session 41 only:** write `docs/tuning/tuning_summary.md` (accuracy curve for both splits, every change by ladder step and iteration, remaining failures with category and exhausted steps, instruction/example-SQL count and why each was needed). If the rule is still not reached after iteration 6, say so plainly; the wave's `asymptote` check then fails for the owner to decide.

## Acceptance Criteria
- [ ] Wave gate checks for iteration `kk` and `mv_first` pass (plus `asymptote` and `tuning_summary` for session 41).
- [ ] Every registration and deploy run id is in the session summary.

## Owned Paths / Assets
- `examples/tpch/ontology-metric-views/metric_views/**`, `examples/tpch/ontology-genie-agents/agents/**`, `examples/tpch/docs/semantics/**`, `examples/tpch/docs/pages/**`, `examples/tpch/docs/tuning/**` (not `benchmark/**`)
- Dev deployments of both TPC-H bundles, the registration job, this build's DRAFT pages.

## Dependencies
- Session 35 (baseline, tuning_plan_01), then the previous iteration.
