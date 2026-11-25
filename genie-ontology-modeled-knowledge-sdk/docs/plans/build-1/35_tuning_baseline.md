# Session 35: TPC-H Benchmarks in the Agent & Baseline Evaluation

## Scope
Load the full benchmark set into the TPC-H agent, render it from the resolved target with the identifier check, deploy the agents bundle, run the baseline evaluation, score both splits, and write tuning plan 01. Deploy only the agents bundle.

## Context
* [Exhaustive tuning protocol](INDEX.md#exhaustive-tuning-protocol-owner-request); `skills/ontology-tuning`.
* Authorized: `bundle.deploy` of `examples/tpch/ontology-genie-agents` (target dev). Benchmark evaluation runs and conversations are read/evaluate calls on the deployed agent under `allow_execute`; if the eval-runs API is refused, use `benchmark.run_benchmark` (fallback) and say so.
* Holdout questions are loaded into the agent's benchmarks too (benchmarks do not feed the agent's answers), so one evaluation scores both splits. Tuning sessions never read holdout question text.
* Build-0 placeholder agent file is gone (P1-5). The agent has no instruction or example-SQL changes at baseline.

## Tasks
1. `benchmark.load_question_set` + `assign_splits` + `coverage` over `docs/tuning/benchmark/` (must pass; stop `blocked` otherwise).
2. Add the benchmarks section (`to_space_benchmarks`, at most 498) to `agents/tpch_supply_chain_agent.geniespace.json`; `validate_space`.
3. `geniespace render --params examples/tpch/docs/registration/resolved_target.json --check`; `bundle validate --strict -t dev`; `bundle deploy -t dev` (max 4 attempts).
4. Baseline: `benchmark.run_eval` on the deployed space; `score` per split; write `docs/tuning/iterations/00_baseline.md` (accuracy per split, per view, per type, failures by category) and the first `accuracy_history.json` entry (`iteration: 0`, `label: baseline`).
5. Triage tuning-split failures with the skill's categories; write `docs/tuning/tuning_plan_01.md`: actions by metric view and ladder step (steps 1-8 first), expected effect, status `planned`.
6. Update `docs/deployment/agent_validation.md` (probes still pass: 3 simple questions).

## Acceptance Criteria
- [ ] Gate checks `baseline_results` and `tuning_plan_01` pass.
- [ ] No instruction or example SQL in tuning_plan_01 without an exhaustion record (there should be none at baseline).

## Owned Paths / Assets
- `examples/tpch/ontology-genie-agents/**`, `examples/tpch/docs/tuning/**` (not `benchmark/**`), `examples/tpch/docs/deployment/**`
- Dev deployment of the agents bundle.

## Dependencies
- Sessions 19, 22, 30, 31, 32, 33, 34.
