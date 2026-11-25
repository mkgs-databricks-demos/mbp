# Session 22: Benchmark Library for Exhaustive Tuning

## Scope
Extend `benchmark.py` for the [exhaustive tuning protocol](INDEX.md#exhaustive-tuning-protocol-owner-request): folder question sets, a coverage matrix against the metric views, a deterministic holdout split, `unit_mismatch` scoring, Genie benchmark evaluation runs, accuracy history and the asymptote rule. Mocked tests only.

## Context
* Owner request (2026-11-25): 100-498 questions per agent, exhaustive over every metric view and cross-view questions; at least three tuning plans; tune until accuracy flattens; MV-first.
* Build-0 observation 31: a x100 match of a 0-1 ratio counted as a plain miss.
* Genie benchmark evaluation API: `POST /api/2.0/genie/spaces/{space_id}/eval-runs` (`benchmark_question_ids` optional) -> `eval_run_id`, `eval_run_status` (`RUNNING`, `DONE`, `EVALUATION_FAILED`, ...), `num_correct`, `num_done`, `num_needs_review`; `GET .../eval-runs/{id}`, `GET .../eval-runs/{id}/results` (paged, 100 per page), `GET .../results/{result_id}` (details). Use the SDK wrapper if session 18's floor has one, else `ws.api_client.do`. Up to 500 benchmark questions per agent.
* The existing `run_benchmark` (Genie conversation API, one question per conversation) stays as the fallback; Genie API requests are rate-limited per workspace (HTTP 429), so add bounded concurrency and exponential backoff.

## Tasks
1. Constants exactly as listed in the [INDEX contracts](INDEX.md#cross-session-contracts).
2. `load_question_set(folder)`: all `*.yml` in a folder, unique ids across files, tags parsed into `type`, `views`, `measures`, `dimensions`.
3. `coverage(questions, mv_yaml_paths) -> CoverageReport`: counts per view, measure and dimension (read the metric view YAML via `mv_yaml`), cross-view share (questions tagged with >= 2 views), type mix; `ok` and a list of problems against the constants. CLI: `python -m genie_ontology_modeled_knowledge_sdk.benchmark coverage <questions_dir> <metric_views_dir>` exits non-zero on problems.
4. `assign_splits(questions, holdout=HOLDOUT_SHARE)`: stable by hash of the id; an explicit `split:` in the YAML wins.
5. `score`: new per-result flag `unit_mismatch` (result equals expected x100 or /100 for ratio expectations); `Summary` gains `unit_mismatch` and per-split accuracy (`tuning`, `holdout`).
6. `to_space_benchmarks(questions)`: the benchmarks-section shape session 19 accepts (tokenized SQL stays tokenized; the render step resolves it).
7. `run_eval(space_id, ws, question_ids=None, poll_s=10, timeout_s=7200)`: start, poll with backoff, page results and details into `Result` objects (map Genie benchmark ids back to question ids); `needs_review` results count as not matched and are listed.
8. `run_benchmark(..., max_workers=4)`: thread pool, 429/5xx backoff, per-question timeout.
9. `append_history(path, entry)` and `asymptote(history) -> dict(reached, reason, fix_iterations, last_deltas_pp, holdout_gap_pp)` implementing the stop rule; `write_iteration_md(...)` for `iterations/<k>.md`.
10. Update the module docstring (scoring definition, eval-run mapping, stop rule).

## Acceptance Criteria
- [ ] Gate `pytest` and `lint` pass.
- [ ] Tests: coverage fails on 99 and 499 questions, on a view with 11 questions, on 24% cross-view; splits are stable across runs; `unit_mismatch` case; `run_eval` with a fake API (RUNNING -> DONE, two result pages); 429 backoff; `asymptote` table-driven cases (2 fix iterations -> not reached; deltas 0.8 and 0.4 after 3 -> reached; holdout gap 2.5 -> not reached; 100% -> reached).

## Owned Paths
- `src/genie_ontology_modeled_knowledge_sdk/benchmark.py`, `tests/test_benchmark.py`, `tests/fixtures/benchmark/**`

## Dependencies
- Session 18. Contract with session 19 (benchmarks section shape).
