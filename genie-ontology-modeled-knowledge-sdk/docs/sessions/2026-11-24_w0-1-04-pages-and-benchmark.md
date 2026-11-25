# 2026-11-24 — Wave 0-1 / Session 04: UC Pages & Benchmark Helpers

* Build run: job `419885870201924`, run `701596191246320`, task `w0-1_session`, continuation 0
* Mode: `edit` (`allow_execute: true`), workflow `hybrid`, branch `mg-genie-ontology-modeled-knowledge-sdk` (verified read-only via the Repos API on the `mbp` Git folder)
* Status: **pass**. No live API writes; the only live calls were read-only `describe` lookups of the knowledge-page endpoints and `help()`-style inspection of the installed databricks-sdk (0.122.0).

## Changes

| File | What |
|---|---|
| `src/genie_ontology_sdk/pages.py` | `Term`, `PageResult`, `PagesClient` protocol, `RestPagesClient(ws)`, `parse_term_file`, `parse_glossary`, `to_page_payload`, `upsert_pages`, `PAGE_FIELDS` |
| `src/genie_ontology_sdk/benchmark.py` | `Question`, `Result`, `Summary`, `ACCURACY_GATE = 0.70`, `load_questions`, `run_benchmark`, `score`, `write_results_md`; scoring definition in the module docstring |
| `tests/test_pages.py` | 15 tests (fake `PagesClient` recording calls; fake `api_client` for `RestPagesClient`) |
| `tests/test_benchmark.py` | 16 collected (fake `ws.genie` + `ws.statement_execution`) |
| `tests/fixtures/glossary/` | `net_revenue.md`, `discount.md`, `order_priority.md`, `README.md` (skipped by the parser) |
| `tests/fixtures/benchmark/questions.yml` | 4 questions: scalar answer, row-list answer, `expected_sql` only, no expectation |

## Decisions

* **Pages REST API** (from the `discover-pages` skill and endpoint `describe`): `GET/POST /api/2.0/knowledge/pages`, `GET/PATCH /api/2.0/knowledge/pages/{page_id}`; bodies are unwrapped page fields; `filter` (`domain = "domains/<id>"`) and `update_mask` are query params. The installed SDK has no typed client for it, so `RestPagesClient` uses `ws.api_client.do`. All REST details are in that one class.
* **`upsert_pages(terms, client, *, dry_run=True, domain_id=None)`**: added keyword-only `domain_id` (creating a page requires `domains/<id>`; front matter `domain` is a name like `tpch_supply_chain`, not an id). Without `domain_id`, missing pages are `error` results. Match by title, case-insensitive, among `list_pages(domain)`; `get_page` then diff `description`, `synonyms`, `body` and PATCH only changed fields. New pages are DRAFT, owner unset; existing `state`/`owner_ids` are never touched; never deletes. Several pages with the same title -> `error`. A failing term is reported and the batch continues.
* **Payload**: `display_name`, `description` (first sentence of Definition, <= 160 chars), `synonyms` (deduped, term itself removed, <= 50), `body` sections Definition, Business context, Data usage, any extra sections, Related terms, Source; `domain` when given. Heading aliases: `Business use` -> Business context.
* **Glossary parsing**: skips `INDEX.md`, `README.md` and markdown without front matter; front matter without `term` or duplicate terms raise `ValueError`.
* **Genie API** (confirmed in databricks-sdk 0.122.0): `ws.genie.start_conversation_and_wait(space_id, content, timeout=timedelta)` and `ws.genie.get_message_attachment_query_result(space_id, conversation_id, message_id, attachment_id)` -> `.statement_response` (status.state, manifest.schema.columns, result.data_array). Verified end to end against real SDK dataclasses (`GenieMessage`, `StatementResponse`) with a stub transport.
* **Scoring** (docstring; sessions 16/17 quote it): `matches_expected` is `None` when not evaluated; `expected_sql` needs an optional `warehouse_id` kwarg on `run_benchmark` (runs it via `ws.statement_execution` and compares row multisets). accuracy = matches / evaluated expectations, else succeeded / total. Numeric tolerance rel 1e-4; strings trimmed, case-insensitive. Scalar answers match a cell of the first row. Interpretation is left as a blank review column in the markdown.

## Checks

| Check | Result |
|---|---|
| Gate-style pytest from a `/tmp` copy of build_root (`cp -r ... /tmp/gos-04 && python -m pytest -q`) | pass — 91 passed (whole suite as present at run time) |
| `tests/test_pages.py` + `tests/test_benchmark.py` >= 10 tests | pass — 31 passed |
| `upsert_pages(..., dry_run=True)` makes no write calls | pass — `test_dry_run_makes_no_writes`, `test_dry_run_is_the_default` |
| Idempotent upsert (second run 0 changed pages) | pass — `test_upsert_creates_then_is_idempotent` |
| Scoring definition in `benchmark.py` docstring | pass — `test_score_definition_is_documented` |
| Real SDK types through `run_benchmark` | pass (manual check, see Decisions) |

## Notes for later sessions

* Session 13: `upsert_pages(parse_glossary(dir), RestPagesClient(ws), dry_run=False, domain_id=<id>)`; list domains with `GET /api/2.0/domains`. Domain-filtered listing needs domain admin. In an unattended job, page writes may be rejected; report the drafted payloads (`to_page_payload`) instead.
* Session 16: `run_benchmark(space_id, load_questions(path), ws, warehouse_id=<wh>)` so `expected_sql` questions are scored; `score(...).passes_gate`; `write_results_md(...)`.

## Requests

None.
