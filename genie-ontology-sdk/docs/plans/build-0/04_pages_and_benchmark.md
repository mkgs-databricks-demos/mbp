# Session 04: UC Pages & Benchmark Helpers

## Scope
Build `src/genie_ontology_sdk/pages.py` (glossary markdown -> UC Page payloads, idempotent upsert) and `src/genie_ontology_sdk/benchmark.py` (run benchmark questions through the Genie conversation API and score them). Tests use mocks only; this session makes no live API calls.

## Context
* [L200-F](../../design/L200-F-registration-pipeline.md) Wave 5.5 (page sections: definition, business context, data usage, related terms, source).
* [L200-H](../../design/L200-H-tuning-engine.md) Phase 3 (10-20 questions per agent; scoring = correct SQL, correct result, correct interpretation).
* UC Pages / Discover pages: load the `discover-pages` skill for the current REST endpoints and payload. Wrap them behind a small client interface, so a changed endpoint touches one function.
* Genie conversation API: `WorkspaceClient().genie` (`start_conversation_and_wait`, `get_message_attachment_query_result` or the current equivalents). Confirm the method names in the installed databricks-sdk with `help()`; do not guess.
* Glossary input format (written by sessions 10a/13): one markdown file per term with front matter `term`, `synonyms`, `domain`, `subdomain`, `related_terms`, `sources`. See [INDEX.md](../INDEX.md#cross-session-contracts).

## Tasks
1. `pages.py`:
   * `parse_glossary(dir) -> list[Term]`
   * `to_page_payload(term, domain_id=None) -> dict`
   * `upsert_pages(terms, client, *, dry_run=True) -> list[PageResult]`: looks pages up by title, then creates or updates; never deletes
   * `PagesClient` protocol + `RestPagesClient(ws)`
2. `benchmark.py`:
   * `load_questions(path)`: YAML list of `{id, question, expected_sql?, expected_answer?, tags}`
   * `run_benchmark(space_id, questions, ws, *, timeout_s=120) -> list[Result]`
   * `score(results) -> Summary`: counts for sql_generated / sql_succeeded / matches_expected, and accuracy = matches / questions with expectations, else succeeded / total
   * `write_results_md(summary, results, path)`
3. Tests with fake clients: payload shape, idempotent upsert (second run updates 0 changed pages), benchmark scoring math, markdown output.

## Acceptance Criteria
- [ ] pytest (from a `/tmp` copy) passes, with at least 10 tests across `test_pages.py` and `test_benchmark.py`.
- [ ] `upsert_pages(..., dry_run=True)` makes no client write calls (asserted by the fake).
- [ ] The scoring definition is written in the `benchmark.py` docstring (sessions 16 and 17 quote it).

## Owned Paths / Assets
- `src/genie_ontology_sdk/pages.py`, `src/genie_ontology_sdk/benchmark.py`
- `tests/test_pages.py`, `tests/test_benchmark.py`, `tests/fixtures/glossary/**`, `tests/fixtures/benchmark/**`

## Dependencies
- Session 01: package layout, `FakeWorkspaceClient` pattern.
