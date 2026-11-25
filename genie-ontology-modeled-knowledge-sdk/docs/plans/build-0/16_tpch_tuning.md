# Session 16: TPC-H Dogfood — Benchmark & Tuning

## Scope
Dogfood the `ontology-tuning` skill:
* generate 10-20 benchmark questions for the TPC-H agent, with expected SQL or answers where derivable
* run them with `benchmark.run_benchmark` and score them
* triage failures and fix metric views first (comments, synonyms, measures), with at most 2 iterations, re-registering through the metric-views bundle
* write `examples/tpch/docs/tuning/tuning_plan.md` and `benchmark_results.md`

## Context
* Load `skills/ontology-tuning/SKILL.md` (session 05b); [L200-H](../../design/L200-H-tuning-engine.md). The accuracy definition is the one in the `benchmark.py` docstring.
* **Threshold policy (build-0):** the 70% target is recorded, not gated. If accuracy is below 70% after 2 iterations, finish with status `pass` and a "Build 1 tuning backlog" section. The baseline is unknown, so a hard gate would need manual waiving.
* Deploys: `allow_deploy: true` (only deployer in the wave). Re-register MVs with `bundle deploy` + `bundle run register_metric_views` on `examples/tpch/ontology-metric-views`. Redeploy the agents bundle only if a `.geniespace.json` change is justified (Phase 2: genuinely ambiguous terms only).
* Expected answers come from your own read-only SQL over `samples.tpch` (state the query in the results file).

## Tasks
1. Write `examples/tpch/docs/tuning/benchmark_questions.yml` (contract in INDEX.md).
2. Baseline run -> score -> triage table.
3. Iteration 1 (and 2 if needed): MV fixes -> re-register -> re-run -> score.
4. `tuning_plan.md` (actions per MV/agent, MV-first rationale) and `benchmark_results.md` (per-question results, accuracy per iteration).

## Acceptance Criteria
- [ ] Integrator check `benchmark_results`: `benchmark_results.md` exists, with at least 10 questions and an accuracy score per iteration.
- [ ] Every MV change was re-registered and the registration job run ended SUCCESS (run id in the summary).
- [ ] Agent instruction changes (if any) are each justified as an ambiguous term.

## Owned Paths / Assets
- `examples/tpch/docs/tuning/**`
- `examples/tpch/ontology-metric-views/metric_views/**`
- `examples/tpch/ontology-genie-agents/agents/**`
- Workspace: dogfood metric views and Genie Agent (dev).

## Dependencies
- Session 15: deployed agent. Sessions 04, 05b.
