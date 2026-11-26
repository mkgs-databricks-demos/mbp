# Session 11: Benchmark Baseline & Tuning Plan 01

## Scope
Assign tuning and holdout splits, add the benchmarks to the agent files, render and deploy `ontology-genie-agents` to `{{bundle_target}}`, run the baseline evaluation, and write `docs/tuning/accuracy_history.json` and `docs/tuning/tuning_plan_01.md`. This is the only session in its wave, because it deploys. Baseline accuracy is recorded, not gated.

## Context
* Skill: `ontology-tuning` by its Unity Catalog id from `sdk_config.json` `skills`; fallback `skills/ontology-tuning/SKILL.md` in the SDK checkout.
* SDK (installed wheel `{{sdk_version}}`): `benchmark.load_question_set`, `assign_splits`, `to_space_benchmarks`, `run_benchmark`; `geniespace render <src> <dst> --params docs/registration/resolved_target.json --check` and `validate_space`.
* Approvals: `bundle.deploy` of `ontology-genie-agents` (`{{bundle_target}}`) is in the session's `authorizations`. Deploy nothing else.
* Never cite a holdout question in a tuning plan.

## Tasks
1. Load `docs/tuning/benchmark/*.yml`, assign splits, write the split map to `docs/tuning/splits.json`.
2. Add the tuning-split benchmarks to each agent file; render with `--check`; `validate_space` every file.
3. `bundle validate --strict` and `bundle deploy --target {{bundle_target}}` from `ontology-genie-agents/`.
4. Run the baseline over both splits; append a `baseline` entry (tuning and holdout accuracy, start time) to `accuracy_history.json`.
5. Write `tuning_plan_01.md`: every failed tuning-split question with one category and a ladder step (metric view first, UC semantics next, agent instructions last).

## Acceptance Criteria
- [ ] Baseline entry from an evaluation that started after this build run started.
- [ ] `tuning_plan_01.md` classifies every failed tuning-split question and cites no holdout question.

## Owned Paths
- `docs/tuning/**`, `ontology-genie-agents/agents/**`

## Dependencies
- Sessions 10a, 10b, 10c: question set. Session 06: `docs/registration/resolved_target.json`.
