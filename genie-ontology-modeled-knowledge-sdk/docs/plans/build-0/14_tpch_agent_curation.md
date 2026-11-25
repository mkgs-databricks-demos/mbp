# Session 14: TPC-H Dogfood — Genie Agent Curation

## Scope
Dogfood the `ontology-agent-curation` skill:
* plan the agents for the registered TPC-H metric views (expected: 1 agent, since there are fewer than 50 MVs)
* write tokenized `examples/tpch/ontology-genie-agents/agents/*.geniespace.json`, the matching `resources/genie_agents.yml` entries, and `examples/tpch/docs/domain_manifest.yml`
* render the agent files and validate the bundle

## Context
* Load `skills/ontology-agent-curation/SKILL.md` (session 05b); session 03 `geniespace.py`; the session 07 template README (interpolation vs render approach).
* Inputs:
  * `examples/tpch/ontology-metric-views/metric_views/manifest.json`
  * `examples/tpch/docs/registration/registration_results.md` (only registered MVs)
  * research KPIs for 5-10 sample questions
  * `data_model_summary.md` for join specs
* Keep text instructions minimal. Add example SQL only for multi-step questions, and every example SQL must pass `EXPLAIN` on the overrides' warehouse (read-only).
* Session 13 runs in parallel; do not touch `docs/pages/`.

## Tasks
1. `plan_agents` -> `build_space` -> `validate_space` (0 errors). Write the agent file(s) tokenized per the template approach.
2. Update `resources/genie_agents.yml` (one resource per agent, `file_path` per the template approach).
3. Render (if the template uses rendering) and run `bundle validate --strict -t dev` (runDatabricksCli tool with `workingDirectory`).
4. `write_domain_manifest` -> `examples/tpch/docs/domain_manifest.yml` (proposal only).
5. A "Skill gaps" section in the session summary.

## Acceptance Criteria
- [ ] At least 1 `.geniespace.json`, which passes `validate_space`, references only registered MVs, and has 5-10 sample questions.
- [ ] Every example SQL passes `EXPLAIN`.
- [ ] The dogfood agents bundle passes `bundle validate --strict -t dev`. No deploy in this session.
- [ ] Committed agent files contain no resolved catalog/schema names (tokens or `${var.*}` only).

## Owned Paths / Assets
- `examples/tpch/ontology-genie-agents/agents/**`
- `examples/tpch/ontology-genie-agents/resources/**`
- `examples/tpch/docs/domain_manifest.yml`

## Dependencies
- Session 12: registered MVs. Sessions 03, 05b, 07.
