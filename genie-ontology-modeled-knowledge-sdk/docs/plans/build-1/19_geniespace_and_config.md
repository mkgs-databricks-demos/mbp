# Session 19: Agent Config Fixes (R4.1, R4.4)

## Scope
`geniespace.py` and `config.py` fixes: agent split limit, real subdomains, a token-substitution helper, render from a resolved-target file with an identifier check, and a benchmarks section in agent files. Mocked tests only.

## Context
* [REQUESTS R4](REQUESTS.md#r4-fix-the-library-and-template-defects) items 1 and 4; review gap G5.
* Build-0 observations: 24 (`write_domain_manifest` collapses subdomains for a single-agent plan), 25 (`render_space_text` accepts only full JSON), 28/29 (the agents bundle `schema` drifted from DAB 1; render fails only on unresolved tokens).
* Contracts in [INDEX](INDEX.md#cross-session-contracts): `resolved_target.json` (written by session 21's `targets.py`); the benchmarks section shape returned by session 22's `benchmark.to_space_benchmarks`.
* Genie allows up to 500 benchmark questions per agent. Read the benchmarks field names from an exported space (`GET /api/2.0/genie/spaces/{id}?include_serialized_space=true` on the build-0 TPC-H agent, read-only) or the Genie API docs, and record them in the module docstring. If no space is readable, follow the docs and mark the shape "from docs, not verified".

## Tasks
1. `plan_agents`: split at `min(max_per_agent, MAX_DATA_SOURCES)`; tests with 29, 30, 31 and 50 metric views, all agents pass `validate_space`.
2. `config.validate_config`: warning when `max_metric_views_per_agent > 30`.
3. `write_domain_manifest`: a single-agent plan lists every real subdomain with the same agent (obs 24).
4. `render_text(text, params)`: token substitution for any string (obs 25); `render_space_text` uses it.
5. `geniespace render`: `--params <resolved_target.json>` (keys `catalog`, `schema`, `warehouse_id`) as an alternative to individual flags; `--check` resolves the target schema and every metric view identifier through `information_schema` with a `WorkspaceClient` + warehouse and exits non-zero listing the missing ones (obs 28, 29).
6. `build_space(..., benchmarks=None)` and `validate_space`: optional benchmarks section; error above 500 questions, on duplicate ids, or on a question without SQL answer text.
7. Update the L200-G rule text in `skills/ontology-agent-curation` **as a request to session 25** (it owns that skill) if anything there must change; do not edit skills.

## Acceptance Criteria
- [ ] Gate check `r4_tests` (the split part) and `pytest` pass.
- [ ] `render --params ... --check` is tested with a fake client for both a resolving and a missing identifier.
- [ ] Benchmarks section round-trips through `build_space` -> `validate_space` with 498 questions and fails with 501.

## Owned Paths
- `src/genie_ontology_modeled_knowledge_sdk/geniespace.py`, `src/genie_ontology_modeled_knowledge_sdk/config.py`
- `tests/test_geniespace.py`, `tests/test_config.py`, `tests/fixtures/geniespace/**`

## Dependencies
- Session 18 (lint/type config: new code must pass ruff and mypy).
