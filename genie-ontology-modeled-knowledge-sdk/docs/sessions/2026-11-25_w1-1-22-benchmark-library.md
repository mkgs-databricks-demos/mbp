# 2026-11-25 - Wave 1-1, session 22: Benchmark library for exhaustive tuning

Run `1057400752545739`, branch `mg-genie-ontology-build-1-plan` (checked read-only via the Repos API; Git folder `mbp` is on that branch), mode `edit`. No Git commands were run. No live API writes: the only live call was a read-only `GET /api/2.0/genie/spaces/01f1e8a428241105b01bbc2f4e355e30?include_serialized_space=true` on the build-0 TPC-H agent, to look for a `benchmarks` section.

## Problem

`benchmark.py` (build-0) handled 10-20 questions from one file, one question at a time, through the conversation API. The exhaustive tuning protocol (build-1 INDEX) needs 100-498 questions per agent from a folder, coverage checks against the metric views, a deterministic holdout split, Genie benchmark evaluation runs, unit-mismatch scoring (build-0 observation 31) and an accuracy history with a stop rule.

## Changes (plan build-1/22 tasks 1-10)

* **Constants** (task 1), exactly as in the INDEX contract: `MIN_QUESTIONS=100`, `MAX_QUESTIONS=498`, `MIN_PER_VIEW=12`, `MIN_CROSS_VIEW_SHARE=0.25`, `HOLDOUT_SHARE=0.2`, `MIN_FIX_ITERATIONS=3`, `ASYMPTOTE_DELTA_PP=1.0`, `ASYMPTOTE_WINDOW=2`, `HOLDOUT_TOLERANCE_PP=2.0`, `MAX_FIX_ITERATIONS=6`. Also `MAX_SPACE_BENCHMARKS=500`, `QUESTION_TYPES` (the eight protocol types) and `SPLITS`.
* **`load_question_set(folder)`** (task 2): reads every `*.yml`/`*.yaml` in the folder, sorted by name and not recursive. Ids must be unique across files; a duplicate error names both files. `Question` gains `split` (optional `split:` key, `tuning`/`holdout` only) and the parsed tag properties `type`, `views`, `measures` and `dimensions`. They come from the `type:`, `view:`, `measure:` and `dimension:` tags. Measure and dimension tags may be qualified as `<mv>.<name>`. Other tags stay as free labels.
* **`coverage(questions, mv_yaml_paths) -> CoverageReport`** (task 3). It reads the metric view YAML with `mv_yaml.iter_mv_files`/`load_mv`; the view name is the file stem, measures come from `measures`, and dimensions from `dimensions` + `fields`. It reports per-view, per-measure and per-dimension counts, the cross-view count and share, the type mix, and `problems`, with `ok`, `to_dict()` and `to_text()`. A problem is raised for: <100 or >498 questions; a view with <12 questions; an untagged measure or dimension; cross-view share <25%; an unused question type; a missing `type:` tag; a missing `expected_sql`; and unknown types, views, measures or dimensions. Matching is case-insensitive. An unqualified measure or dimension tag credits each of the question's views that has it (every view if the question has no `view:` tag). CLI: `python -m genie_ontology_modeled_knowledge_sdk.benchmark coverage <questions_dir> <metric_views_dir> [--json]` exits 0 when ok, 1 on problems and 2 on unreadable input.
* **`assign_splits(questions, holdout=0.2)`** (task 4): `holdout` when the first 8 bytes of `sha256(id)` read as a fraction of 2^64 fall below the share. An explicit `split:` wins. It sets `Question.split` and returns `{id: split}`.
* **Scoring** (task 5): new `Result` fields are `split`, `unit_mismatch`, `needs_review` and `assessment`. `unit_mismatch` is set when a miss would match with the ratio values x100 or /100. That covers scalars of `type:ratio` questions, any non-integral scalar, and the non-integral cells of row expectations, both `expected_answer` and `expected_sql` rows. It is still a miss. `Summary` gains `unit_mismatch`, `needs_review`, `tuning` and `holdout` (`{n, correct, accuracy}` over scored results in that split). `score(results, splits=None)` can override the split per id. `write_results_md` adds the unit-mismatch, needs-review and per-split rows, plus `Split` and `Unit mismatch` columns.
* **`to_space_benchmarks(questions)`** (task 6) returns `{"questions": [{id, question: [text], answer: [{format: "SQL", content: [sql lines]}]}]}`, sorted by id. `id` = `benchmark_id(question_id)`, a uuid5 32-hex value, so results map back. Tokenized SQL is kept as it is. It raises above 500 questions, on duplicate ids, and on a question without `expected_sql`.
* **`run_eval(space_id, ws, question_ids=None, poll_s=10, timeout_s=7200, *, questions=None) -> EvalRun`** (task 7) calls `ws.api_client.do`, because the SDK floor 0.45 has no eval-runs wrapper. The wrappers `genie_create_eval_run` and the others exist only in newer SDKs; 0.122 was inspected. Steps:
  * POST `.../eval-runs` with `benchmark_question_ids` = the benchmark ids, or all questions when `question_ids` is None.
  * Poll `GET .../eval-runs/{id}`. The interval starts at `poll_s` and grows x1.5 up to 60 s.
  * Page `GET .../results` with `page_size=100` and `page_token`, and read `GET .../results/{result_id}` for each result.
  * Assessment: `manual_assessment` (bool) wins over `assessment`. `GOOD` is a match, `BAD` a miss, and `NEEDS_REVIEW` or none is a miss listed in `EvalRun.needs_review`. SQL and rows come from the `SQL` actual response's `sql_execution_result`, and `unit_mismatch` is checked against the expected response rows.
  * Any terminal status other than `DONE` raises `RuntimeError`. Hitting the deadline raises `TimeoutError`.
  * Field names were checked against the SDK dataclasses (`GenieEvalRunResponse`, `GenieEvalResult`, `GenieEvalResultDetails`, `GenieEvalResponse`, `EvaluationStatusType`).
* **`run_benchmark(..., max_workers=4)`** (task 8): uses a thread pool and keeps the result order. Every Genie and statement call goes through `_with_backoff`: retries on HTTP 429/500/502/503/504, SDK `TooManyRequests`/`TemporarilyUnavailable`/... and `RESOURCE_EXHAUSTED`. Waits are `2 s * 2^attempt` capped at 60 s, with jitter, for up to 6 retries. `timeout_s` still bounds each question.
* **History and stop rule** (task 9): `history_entry(...)` builds an `accuracy_history.json` entry from a `Summary`. `append_history(path, entry)` creates or appends, sorts by iteration, and rejects duplicate iterations or missing keys. `asymptote(history)` returns `{reached, reason, fix_iterations, last_deltas_pp, holdout_gap_pp, exhausted}`:
  * It needs at least 3 applied plans (iterations >= 1).
  * Then either both of the last 2 deltas are < 1.0 pp, or tuning accuracy is 100%.
  * And the latest holdout accuracy is within 2.0 pp of its best.
  * `exhausted` is true when the rule is not reached after 6 plans.
  * `write_iteration_md(path, entry, *, state, results, plan_applied, next_plan)` writes `iterations/<k>.md`. It lists **only tuning-split failures** and never holdout ids or questions.
* **Module docstring** (task 10): question YAML and tags, coverage rules, splits, scoring (now with `unit_mismatch` and `needs_review`), eval-run mapping and the stop rule.
* **Tests:** `tests/test_benchmark.py` goes from 15 to 47 tests. The existing `FakeGenie` is now thread-safe (lock + id counter) because `run_benchmark` runs in parallel by default. An autouse fixture records sleeps instead of sleeping. New fixtures: `tests/fixtures/benchmark/metric_views/` (`mv_orders`, `mv_parts`, `mv_suppliers`) and `tests/fixtures/benchmark/question_set/` (`simple.yml`, `cross.yml`).

## Decisions

* **Benchmarks section shape: from docs, not verified.** The build-0 TPC-H agent's serialized space has no `benchmarks` key (keys: `config`, `data_sources`, `instructions`, `version`). The shape follows the Genie Agents API docs ("each benchmark question must have exactly one answer with format set to SQL") and the list-of-lines convention the space uses for `example_question_sqls`. Session 19 owns `build_space`/`validate_space`. It should accept this exact shape, or record a request to change `to_space_benchmarks`.
* `benchmark_id` uses its own uuid5 namespace instead of importing `geniespace.stable_id`. That avoids an import from a module session 19 is editing in the same wave, and a possible import cycle if `geniespace` later imports `benchmark`.
* `coverage` treats an unused question type and a missing `expected_sql` as problems, because the protocol lists both under coverage and expectations. Sessions 32-34 should expect the CLI to flag them.
* `run_eval` raises on `EVALUATION_FAILED`/`CANCELLED`/`TIMEOUT` instead of returning partial results, so a broken run cannot be scored as low accuracy.
* Holdout accuracy that is missing makes `asymptote` not reached ("no tuning or holdout accuracy"). The protocol always records both.

## Checks

Run from a fresh copy of build_root at `/tmp/gos-s22-gate`. The copy includes the other wave 1-1 sessions' work in progress at that time.

| Check | Result |
|---|---|
| pytest (`GENIE_BUILD_WAVES_DIR` set, gate command) | pass: 403 passed |
| tests/test_benchmark.py | pass: 47 passed (15 before) |
| ruff check . / ruff format --check . | pass (30 files formatted) |
| mypy src | pass (9 source files) |
| benchmark coverage CLI on the fixture question set | exit 1 with 9 problems (expected: 3 questions) |
| Mutation checks, each made in a /tmp copy and reverted: unit mismatch disabled, asymptote delta threshold loosened, `MIN_PER_VIEW` lowered, backoff made constant, holdout failures listed | each made 1-2 tests fail |
| Ported files equal the /tmp working copy (cmp) | pass: all 7 files |

Acceptance tests from the plan:

* coverage fails on 99 and 499 questions, on a view with 11 questions, and on 24% cross-view (each alone);
* splits are stable across runs, with pinned holdout ids;
* the `unit_mismatch` cases;
* `run_eval` with a fake API (NOT_STARTED -> RUNNING -> DONE, two result pages, 429 on the first poll);
* 429 backoff;
* table-driven `asymptote` cases: 2 fix iterations -> not reached; deltas 0.8 and 0.4 after 3 -> reached; holdout gap 2.5 -> not reached; 100% -> reached.

## Files modified

* `src/genie_ontology_modeled_knowledge_sdk/benchmark.py`
* `tests/test_benchmark.py`
* `tests/fixtures/benchmark/metric_views/mv_orders.yml`, `mv_parts.yml`, `mv_suppliers.yml` (new)
* `tests/fixtures/benchmark/question_set/simple.yml`, `cross.yml` (new)

## Notes for other sessions

* Session 19: `build_space(..., benchmarks=to_space_benchmarks(qs))` must accept `{"questions": [{"id", "question": [str], "answer": [{"format": "SQL", "content": [str]}]}]}` (ids are 32-hex).
* Session 26 (tuning skill) and 28 (run kit): the API names and stop-rule fields are in the module docstring. Tuning sessions should write `iterations/<k>.md` with `write_iteration_md` so holdout failures stay hidden.
* Sessions 32-34: tag questions as `type:<t>`, `view:<mv>` (the file stem), `measure:[<mv>.]<name>` and `dimension:[<mv>.]<name>`, using the metric view display names exactly as in the YAML `name`.
* Session 35: use `run_eval(space_id, ws, questions=qs)` after loading `to_space_benchmarks(qs)` into the agent. Fall back to `run_benchmark(..., max_workers=4)` if the eval-runs API is unavailable.
