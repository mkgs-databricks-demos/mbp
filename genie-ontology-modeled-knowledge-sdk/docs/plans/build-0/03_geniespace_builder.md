# Session 03: Genie Agent Config Builder

## Scope
Build `src/genie_ontology_modeled_knowledge_sdk/geniespace.py`: organize metric views into agents (50-MV rule), build and validate `.geniespace.json` (serialized space v2), and write `domain_manifest.yml`. Include tests.

## Context
* [L200-G](../../design/L200-G-genie-agent-curator.md): organization logic, section sources, domain manifest example.
* [research/genie-agent-api-deployment.md](../../research/genie-agent-api-deployment.md); sample `examples/agents/sales_agent.geniespace.json`.
* The Declarative Automation Bundles `genie_spaces` resource (CLI >= 1.3.0, `engine: direct`) takes `file_path` to a `*.geniespace.json`. That JSON has `version: 2`, `config.sample_questions[] {id (32 hex), question[]}`, `data_sources.tables[] {identifier, column_configs[]}`, `instructions {text_instructions, example_question_sqls, join_specs}`. Re-check the shape with docSearch ("genie_spaces resource file_path") before coding.
* Tune metric views before agents: generated text instructions stay minimal (L200-H Phase 2).
* API contract: [INDEX.md](../INDEX.md#cross-session-contracts).

## Tasks
1. `plan_agents(mvs: list[MvRef], max_per_agent=50) -> list[AgentPlan]`. `MvRef` is `{name, fq_name, domain, subdomain}`. If there are <= max MVs, return one agent; otherwise group by subdomain, keep each MV in exactly one agent, and assign cross-domain MVs to their subdomain.
2. `build_space(plan, *, warehouse_id=None, sample_questions, text_instructions, example_sqls, join_specs) -> dict`: deterministic ids (uuid5 of the question text -> 32 hex), sorted keys, metric view identifiers using `${target_catalog}.${target_schema}` tokens resolved by the caller.
3. `validate_space(doc) -> list[str]`: version 2, 1-30 tables, unique sample-question ids, every identifier is 3-part, no duplicate text instructions.
4. `write_domain_manifest(plans, path)`: the L200-G YAML shape.
4b. `render_space_file(src, dst, params)` + CLI `python -m genie_ontology_modeled_knowledge_sdk.geniespace render <src_dir> <dst_dir> --params <json file>`. It substitutes `${target_catalog}` / `${target_schema}` (and `${warehouse_id}` if present) in tokenized `.geniespace.json` files and fails on any unresolved token. `--params` accepts a bundle `variable-overrides.json` (keys `catalog`, `schema`, `warehouse_id` map to the tokens). Committed agent files stay tokenized; rendered copies go to a gitignored folder (session 07 decides the folder).
5. Tests: 3 MVs -> 1 agent; 120 MVs over 3 subdomains -> 3 agents with no duplicates; deterministic output (build twice -> equal JSON); validation errors.

## Acceptance Criteria
- [ ] pytest (from a `/tmp` copy) passes, with at least 8 tests in `tests/test_geniespace.py`.
- [ ] The example `sales_agent.geniespace.json` passes `validate_space`, or the test documents exactly which field it lacks.
- [ ] Building the same plan twice gives byte-identical JSON.
- [ ] `render` with a params file leaves no `${` in the output, and exits 1 when a token is missing.

## Owned Paths / Assets
- `src/genie_ontology_modeled_knowledge_sdk/geniespace.py`
- `tests/test_geniespace.py`, `tests/fixtures/geniespace/**`

## Dependencies
- Session 01: package layout and test scaffold.
