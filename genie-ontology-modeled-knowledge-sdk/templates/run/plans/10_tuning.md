# Session 10: Benchmark & Tuning

## Scope
Benchmark each deployed `{{domain_name}}` Genie Agent with 10-20 questions, then fix failures with the smallest general change: metric views first, agents last. Allow at most 2 fix iterations. Re-register and redeploy on `{{bundle_target}}` as needed, and write `docs/tuning/`. This is the only session in its wave, because it deploys.

## Context
* Skill: load `skills/ontology-tuning/SKILL.md` and follow its MV-first rule, iteration limit and templates.
* SDK functions (`genie_ontology_modeled_knowledge_sdk.benchmark`): `load_questions(path)`, `run_benchmark(space_id, questions, ws, timeout_s=120)`, `score(results)`, `write_results_md(summary, results, path)`. Metric view checks: the `mv_yaml` validator CLI and `manifest.build_manifest` (vendored copy under `ontology-metric-views/src`).
* Inputs: `docs/deployment/deployment_results.md` (space ids), `docs/research/**`, `docs/semantics/**`, metric view YAML, and agent files.
* Use a single `docs/tuning/benchmark_questions.yml`, with each question tagged `agent:<agent_name>`.
* Approvals: `bundle.deploy` of the two project bundles is implied by `allow_deploy`. Re-running `register_metric_views` is approved in the session's `authorizations`. Deploy no other bundle or target.
* Committed files stay tokenized. The overrides files are owner-only.

## Tasks
1. Write `docs/tuning/benchmark_questions.yml` (10-20 per agent, covering the skill's tags) and `docs/tuning/tuning_plan.md`.
2. Run the baseline benchmark and score it.
3. Iterations 1-2, only while an agent is below 70%: triage the failures, fix the metric view YAML first (validate it, rebuild `manifest.json`), change agent files only when no metric view fix applies, then redeploy. For YAML changes: deploy `ontology-metric-views` and run `bundle run register_metric_views`. For agent changes: render if needed and deploy `ontology-genie-agents`. Then re-run the benchmark.
4. Write `docs/tuning/benchmark_results.md` with `write_results_md`: per-agent accuracy for each run, the final run time, and the remaining failures with their proposed fixes.

## Acceptance Criteria
- [ ] 10-20 questions per agent.
- [ ] The final run happened after this build run started, and every agent scores at least 70%. If not, after 2 iterations stop with `status: "fail"` and list what remains.
- [ ] The metric view validator exits 0, and no instruction restates metric view metadata.

## Owned Paths
- `docs/tuning/**`
- `ontology-metric-views/metric_views/**`
- `ontology-genie-agents/agents/**`

## Dependencies
- Session 09: deployed agents and their space ids.
