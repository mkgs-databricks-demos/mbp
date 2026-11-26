# Sessions 12-17: Tuning Iteration N (MV-First)

## Scope
One tuning iteration per session: session 12 = iteration 1 ... session 17 = iteration 6. Iterations 1-3 are mandatory. Iterations 4-6 are conditional: when `benchmark.asymptote` over `docs/tuning/accuracy_history.json` already returns `reached=true`, write `docs/tuning/iterations/0N.md` with 'converged at iteration <j>' and the asymptote output, change nothing else, and end `pass`. Session 17 also writes `docs/tuning/tuning_summary.md`. Each session is alone in its wave, because it deploys.

## Context
* Skill: `ontology-tuning` by its Unity Catalog id from `sdk_config.json` `skills`; fallback `skills/ontology-tuning/SKILL.md` in the SDK checkout. Its ladder and asymptote rule are authoritative.
* Ladder: metric view YAML (comments, synonyms, measures, joins) first, then UC semantics (glossary terms, Pages), agent instructions and example SQL last. A change to agent instructions needs an exhaustion record (every earlier ladder step tried for that failure) in the tuning plan.
* SDK (installed wheel `0.1.1`): `python -m genie_ontology_modeled_knowledge_sdk.mv_yaml validate`, `manifest.build_manifest`, `benchmark.run_benchmark`, `benchmark.asymptote`; `geniespace render --params docs/registration/resolved_target.json --check`.
* Approvals (session `authorizations`): `bundle.deploy` of `ontology-metric-views` and `ontology-genie-agents` on `dev`, `jobs.run_now` of `register_metric_views`, `workspace.write` on the project's DRAFT glossary pages. Nothing else.
* Accuracy targets are recorded, not gated; the asymptote and coverage are the required checks.

## Tasks
1. Read `tuning_plan_0N.md` (N = this iteration). For iterations 4-6, check the asymptote first (see Scope).
2. Apply each action in ladder order. YAML changes: validate, rebuild `manifest.json`, `bundle deploy` `ontology-metric-views`, then `bundle run register_metric_views --target dev`. Pages changes: upsert with `domain_id` and `status=DRAFT` (unless `sdk_config.json` `pages_status`). Agent changes: render with `--check`, `bundle deploy` `ontology-genie-agents`.
3. Mark the plan applied with an outcome per action; re-evaluate both splits; append to `accuracy_history.json`.
4. Write `iterations/0N.md` and `tuning_plan_0(N+1).md` (skip the next plan when the asymptote is reached or N = 6).
5. Session 17 only: write `tuning_summary.md` (accuracy curve for tuning and holdout per iteration, every change by ladder step, every remaining failure with category and exhausted steps).

## Acceptance Criteria
- [ ] A new `accuracy_history.json` entry from an evaluation after this build run started, or a 'converged' record.
- [ ] If any metric view YAML changed, `register_metric_views` has a `SUCCESS` run after the change.
- [ ] Session 17: `benchmark.asymptote` returns `reached=true` with at least 3 completed fix iterations.

## Owned Paths
- `docs/tuning/**`, `docs/semantics/**`, `docs/pages/**`, `ontology-metric-views/metric_views/**`, `ontology-genie-agents/agents/**`

## Dependencies
- Session 11 (iteration 1) or the previous iteration session.
