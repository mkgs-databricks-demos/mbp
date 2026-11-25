# 2026-11-25 - Wave 1-1, session 19: agent config fixes (R4.1, R4.4)

Run `1057400752545739`, branch `mg-genie-ontology-build-1-plan` (checked read-only: clean, on branch), mode `edit` (allow_execute). No Git commands beyond `status`; no deploys, no workspace writes outside owned paths.

## Problems and root causes

* **G5 / R4.1:** `plan_agents` split at `max_per_agent` (default 50) while `validate_space` allows 30 data sources, so 31-50 metric views gave one invalid agent.
* **Obs 24:** `domain_manifest` named the single subdomain of a single-agent plan after the domain and dropped the real subdomains.
* **Obs 25:** `render_space_text` only rendered whole JSON documents; one SQL string could not be resolved for `EXPLAIN`.
* **Obs 28/29 / R4.4:** `render` needed a JSON file and failed only on unresolved tokens, not on identifiers that do not exist.

## Changes

* `geniespace.py`
  * `effective_max_per_agent(m) = min(m, MAX_DATA_SOURCES)`; `plan_agents` uses it for the single-agent test and the chunk size.
  * `domain_manifest`: a single-agent plan lists every real subdomain of its metric views, all pointing at the same agent (no-subdomain views go to `general`). Only when no view has a subdomain does it fall back to one entry named after the domain.
  * `render_text(text, params, *, json_escape=False)`: token substitution for any string, raising on unresolved tokens. `render_space_text` = `render_text(..., json_escape=True)` + JSON check.
  * `render_texts(src_dir, params)` (in-memory render); `render_dir` is now built on it.
  * `space_identifiers(doc)`, `check_identifiers(idents, ws, warehouse_id, target=...)`: runs bound-parameter queries on `system.information_schema.schemata` / `.tables` through `ws.statement_execution` and returns the missing schemas and identifiers.
  * CLI `render`: `--params` is now optional and accepts `resolved_target.json` (extra keys `source`, `resolved_at` and a null `warehouse_id` are ignored). Added `--catalog`, `--schema` and `--warehouse-id` (these override `--params`). `--check` resolves the target schema and every identifier before writing and exits 1 listing the missing ones (nothing written). `main(argv, *, ws=None)` injects a client for tests; otherwise it uses `WorkspaceClient()`.
  * `build_space(..., benchmarks=None)`: accepts a `{"questions": [...]}` section or a list. Each question is in serialized form `{id, question, answer}` or short form `{id?, question, sql}`. A missing id becomes `stable_id("benchmark", question)`; questions are sorted by id; nothing is dropped.
  * `validate_space` checks benchmarks: at most `MAX_BENCHMARK_QUESTIONS = 500`, 32-hex unique ids not shared with `config.sample_questions`, a non-empty question, and exactly one answer with `format: SQL` and non-empty content.
* `config.py`: `AGENT_DATA_SOURCE_LIMIT = 30`; `config_warnings(d)`; `validate_config` emits a `UserWarning` (not an error) when `max_metric_views_per_agent > 30`.
* Tests: updated 4 build-0 tests whose expectations assumed a 50-view split (120 -> 90 views, 50/50/10 -> 30/30/30/20, single-agent manifest subdomain). New tests: 29/30/31/50 split matrix x 3 subdomain layouts all passing `validate_space`; single-agent manifest; `render_text`; benchmarks (498 round trip, 500 pass, 501 fail, duplicate id, missing/blank SQL, wrong format, two answers, bad id, empty question, id shared with a sample question, section shape); CLI with `resolved_target.json`, flags alone and overriding; `--check` with a fake client for resolving, missing identifier, missing schema, no warehouse and a FAILED statement; and a config warning test.
* Fixture: `tests/fixtures/geniespace/resolved_target.json` (contract shape, placeholder values).

## Benchmarks section shape

The build-0 TPC-H agent was read with `GET /api/2.0/genie/spaces/{id}?include_serialized_space=true` (read-only). Its serialized space has **no** `benchmarks` key, so the field names could not be verified on an export. The shape is a top-level `benchmarks.questions[]` with `id`, `question` [str] and `answer` [{`format`: `SQL`, `content` [lines]}]. It comes from the Genie Agents API docs ("exactly one answer with format set to SQL"; benchmark ids unique across sample questions) and is marked **from docs, not verified** in the module docstring.

## Checks (fresh /tmp copy of build_root)

| Check | Result |
|---|---|
| pytest (all, `GENIE_BUILD_WAVES_DIR` set) | pass: 371 passed. Baseline before this session: 301. My /tmp working copy with only my files changed: 334. The fresh copy likely also picks up files from parallel wave 1-1 sessions; I did not check which |
| pytest test_geniespace + test_config | pass: 93 passed |
| r4_tests split part (29/30/31/50 x 3 layouts) | pass: 12 parametrized cases |
| benchmarks 498 round trip / 501 fail | pass |
| `render --params ... --check` with a fake client, resolving + missing | pass |
| ruff check . / ruff format --check . | pass |
| mypy src | pass |
| bundle validate | skipped: no YAML touched |

## Decisions

* Chunks stay at the literal limit (30, 30, ..., remainder) rather than being balanced, to keep the build-0 behaviour apart from the limit.
* The config warning is a Python `UserWarning` plus `config_warnings()`, not an entry in the error list, because a config above 30 still works (agents split at 30). The TPC-H `sdk_config.json` sets 50 explicitly, so it now warns.
* `--check` uses `system.information_schema` with bound parameters (no identifier interpolation) and runs before any file is written.

## Requests

* **Session 25** (owns `skills/ontology-agent-curation`): the L200-G rule text says "<= `max_per_agent` views: one agent". It should say agents are split at `min(max_metric_views_per_agent, 30)` (`geniespace.effective_max_per_agent`), that a single-agent `domain_manifest.yml` lists every real subdomain, and that the render example can use `--params docs/registration/resolved_target.json --check`.
* **Session 22:** `to_space_benchmarks` should return `{"questions": [{"id", "question": [str], "answer": [{"format": "SQL", "content": [lines]}]}]}` (the short `{question, sql}` list is accepted too), with ids that do not reuse sample-question ids. The default id is `stable_id("benchmark", question)`.
* **Owner of `notebooks/init_ontology_project.ipynb`:** show `config_warnings(raw)` next to the `validate_config` error count.
* **Owner of `examples/tpch/` (session 30):** consider `max_metric_views_per_agent: 30` in `sdk_config.json` (it is 50 and now warns; behaviour is unchanged for 7 views).

## Files modified

* `src/genie_ontology_modeled_knowledge_sdk/geniespace.py`
* `src/genie_ontology_modeled_knowledge_sdk/config.py`
* `tests/test_geniespace.py`
* `tests/test_config.py`
* `tests/fixtures/geniespace/resolved_target.json` (new)

## Re-run 109257611554257 (already completed)

Run `109257611554257` found this session already done: run `1057400752545739` passed and its files are committed in `b16746e` (`wave(1-1): 19, 20, 22`); the owned paths have no uncommitted changes. Branch checked read-only (`mg-genie-ontology-build-1-plan`). No files edited. Re-validated in a fresh /tmp copy (which also contains the uncommitted session 21 work in the shared tree):

| Check | Result |
|---|---|
| pytest (all, `GENIE_BUILD_WAVES_DIR` set) | pass: 403 passed |
| pytest test_geniespace + test_config | pass: 93 passed |
| split / benchmark / `--check` tests (`-k`) | pass: 28 passed |
| ruff check . / ruff format --check . | pass |
| mypy src | pass: no issues in 9 source files |

The requests above (sessions 25, 22, init notebook owner, session 30) still stand.
