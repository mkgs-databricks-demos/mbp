# Session 35 (wave 1-7): TPC-H Benchmarks in the Agent & Baseline Evaluation

Build 1, branch `mg-genie-ontology-build-1-plan`. Mode `edit`, `allow_deploy`. **Status: pass** (run 829522414538457). Earlier run 629243800379582 was blocked on the `benchmark._eval_result` scoring bug; the fix landed in commit 754bba0, so this run is a retry that keeps that run's agent file and re-does the evaluation.

Skill source: the session-runner skill loaded from Unity Catalog (`hls_fde_dev.dev_matthew_giglia_build_waves.genie_build_session_runner`); `skills/ontology-tuning` read from the workspace folder.

## Done

| Task | Result |
|---|---|
| 1. `load_question_set` + `assign_splits` + `coverage` | pass: 233 questions, 0 problems, cross-view share 45.1%; splits 191 tuning / 42 holdout |
| 2. Benchmarks section in the agent file | inherited from run 629243800379582, equal to `to_space_benchmarks(qs)`; `validate_space` 0 errors |
| 3. `geniespace render agents .rendered --params examples/tpch/docs/registration/resolved_target.json --check` | exit 0; target schema and 7 identifiers resolve; rendered file has 233 benchmarks, no `${` tokens, `validate_space` 0 errors (run in-process) |
| 3. `bundle validate --strict --target dev` / `bundle deploy --target dev` | Validation OK / 0 changed, 1 unchanged (space already had the 233 benchmarks) |
| 4. Baseline eval | eval run `01f1e95a7f2e12baa07333ab54feff30`, started 2026-11-26T05:30:31+00:00 (after this build run started at 2026-11-26T05:25:43Z), DONE, 233/233 results mapped |
| 4. `benchmark.score` | tuning **83.8% (160/191)**, holdout **83.3% (35/42)**, overall 83.7%; 2 needs_review; `accuracy_history.json` iteration 0 `baseline`; `iterations/00_baseline.md` with per-view / per-type (tuning split) and failures by category |
| 5. Triage + `tuning_plan_01.md` | 31 tuning failures, one category each: Unit / format 11, Ambiguity 7, Filter / edge 6, Benchmark defect 6, Missing measure 1. 18 actions on ladder steps 1, 4, 6 and 8, all `planned`; no agent instruction or example SQL; no holdout id cited (checked) |
| 6. `agent_validation.md` | 3/3 probes SQL generated + SUCCEEDED (7, 25, 35 rows); build-1 section appended |

## Decisions and caveats

* The run-629243800379582 eval (04:13Z) was not reused: the gate needs an evaluation that started after this build run started.
* Eval-run result details had no result rows, so `unit_mismatch` was 0 for every result and triage is from the generated vs expected SQL text. Unit / format was assigned where the agent multiplied a 0-1 ratio by 100 although the question asked for a fraction or share.
* Six benchmark defects are reported for the owner (f029, f030, f031 ask for a percent but expect a fraction; x078, x101, x045 expect columns not asked for). The benchmark is frozen and was not edited.
* Some plan details are marked unverified (Ship Mode value list, High Priority definition, new Order Count expression); iteration 1 must check them against data/YAML.
* Docs were written with Python file writes (SDK helpers `append_history` / `write_iteration_md` write files themselves); the agent file was written by run 629243800379582 with the workspace import API.

## Files and assets

* Modified: `examples/tpch/ontology-genie-agents/agents/tpch_supply_chain_agent.geniespace.json` (inherited), `examples/tpch/docs/deployment/agent_validation.md`.
* Created: `examples/tpch/docs/tuning/accuracy_history.json`, `examples/tpch/docs/tuning/iterations/00_baseline.md`, `examples/tpch/docs/tuning/tuning_plan_01.md`.
* Asset: dev Genie space of the agents bundle (benchmarks loaded); one new eval run on it. Space id in the status file (`resolved_targets`).

## Requests

* Owner (normal): review the six benchmark defects listed in `tuning_plan_01.md`.
* Session 36 (iteration 1): apply `tuning_plan_01.md`; verify the unverified details first.
