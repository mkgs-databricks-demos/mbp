# Session 35 (wave 1-7): TPC-H Benchmarks in the Agent & Baseline Evaluation

Build 1, run 629243800379582, branch `mg-genie-ontology-build-1-plan`. Mode `edit`, `allow_deploy`. **Status: blocked** (SDK scoring bug outside owned paths).

Skill source: the session-runner skill loaded from Unity Catalog (`hls_fde_dev.dev_matthew_giglia_build_waves.genie_build_session_runner`); `skills/ontology-tuning` read from the workspace folder.

## Done

| Task | Result |
|---|---|
| 1. `load_question_set` + `assign_splits` + `coverage` over `docs/tuning/benchmark/` | pass: 233 questions, 0 problems, cross-view share 45.1%, every type used, every view >= 37 questions; splits 191 tuning / 42 holdout |
| 2. Benchmarks section in `agents/tpch_supply_chain_agent.geniespace.json` | 233 questions from `to_space_benchmarks`; `validate_space` 0 errors; no other part of the agent changed (no instruction or example-SQL changes at baseline) |
| 3. `geniespace render --params examples/tpch/docs/registration/resolved_target.json --check` | exit 0: target schema and 7 identifiers resolve; rendered file has 233 benchmarks, no `${` tokens, `validate_space` 0 errors |
| 3. `bundle validate --strict --target dev` | Validation OK |
| 3. `bundle deploy --target dev` (attempt 1 of 4) | exit 0, 1 changed (`genie_spaces.tpch_supply_chain_agent`). Deployed space read back: 233 benchmarks, 7 tables, `update_time` 2026-11-26T04:13:26Z, warehouse matches `resolved_target.json` |
| 4. Baseline eval run (`benchmark.run_eval`) | eval run `01f1e94fcc711598bd98b2859ae28ec0` started 2026-11-26T04:13:56Z, status DONE, 233/233 results returned and all mapped to question ids |
| 4. `benchmark.score` per split | **wrong result, see blocker** |
| 4-6. `00_baseline.md`, `accuracy_history.json`, `tuning_plan_01.md`, `agent_validation.md` probes | not written (blocked) |

The space id is recorded in the status file only (`resolved_targets`).

## Blocker: `benchmark._eval_result` misreads `manual_assessment`

`benchmark.score` reported 0 of 233 correct (tuning 0/191, holdout 0/42), while the eval run itself reports `num_correct` 195 and `num_needs_review` 2.

Root cause (`src/genie_ontology_modeled_knowledge_sdk/benchmark.py`, `_eval_result`): the code treats any boolean `manual_assessment` as a manual verdict (`True` -> GOOD, `False` -> BAD). The eval-runs results API returns `manual_assessment: false` meaning "not manually assessed", next to the real verdict in `assessment`. So every result was forced to BAD.

Evidence (all 233 result details fetched): `(assessment, manual_assessment)` = `(GOOD, false)` 195, `(BAD, false)` 36, `(NEEDS_REVIEW, false)` 2. `actual_response` is a list in all 233 details. The `Result` objects had `sql_generated` and `sql_succeeded` set for all 233, so only the verdict mapping is wrong.

Raw API verdicts by split, for the record only (**not** the SDK scoring definition, not written to `accuracy_history.json`): tuning 162 GOOD / 27 BAD / 2 NEEDS_REVIEW of 191; holdout 33 GOOD / 9 BAD of 42.

Suggested fix (owner or the session that owns `benchmark.py`): use `assessment` as the verdict; let `manual_assessment` override it only when it is a manual verdict (for example when the API marks the result as manually reviewed), not when it is `false`. Add a test with a fixture result `{"assessment": "GOOD", "manual_assessment": false}` that must score correct.

## How to resume (no new evaluation needed)

The eval run started after this build run started, so it can be re-scored once the fix lands:

1. Fix `_eval_result` and its tests.
2. Re-collect the results of eval run `01f1e94fcc711598bd98b2859ae28ec0` (the results-collection half of `run_eval`) on the space in the status file, then `score(results, splits)`.
3. Write `accuracy_history.json` (`iteration: 0`, `label: baseline`, that eval run id and its start time), `iterations/00_baseline.md`, triage tuning-split failures into `tuning_plan_01.md`, and re-run the 3 probes for `docs/deployment/agent_validation.md`.

## Decisions and deviations

* The agent file (164 KB after adding benchmarks) was written with the workspace import API (`w.workspace.upload`, `format: RAW`, overwrite) from Python, not with the file editor: the agents README notes the editor cannot handle `.geniespace.json` files, and the file is too large for a patch edit. The file was read back byte-identical and passes `validate_space`.
* `geniespace render --check` failed in a subprocess with no credentials (`default auth: cannot configure default credentials`); I ran the same CLI in-process with `geniespace.main([...])`, which passed. The rendered `.rendered/` file is gitignored.
* I did not write a baseline from my own re-scoring, because the protocol defines accuracy as `benchmark.score`'s result and `benchmark.py` is outside this session's owned paths.

## Files and assets

* Modified: `examples/tpch/ontology-genie-agents/agents/tpch_supply_chain_agent.geniespace.json` (benchmarks section added).
* Generated (gitignored): `examples/tpch/ontology-genie-agents/.rendered/tpch_supply_chain_agent.geniespace.json`.
* Asset updated: the dev Genie space of `examples/tpch/ontology-genie-agents` (benchmarks loaded). One eval run created on it.

## Requests

* To owner (high): fix `benchmark._eval_result` as above, then resume this session from step 2 of "How to resume".
