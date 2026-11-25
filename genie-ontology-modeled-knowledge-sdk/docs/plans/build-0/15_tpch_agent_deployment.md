# Session 15: TPC-H Dogfood — Genie Agent Deployment

## Scope
Deploy `examples/tpch/ontology-genie-agents` to `dev`, confirm each Genie Agent exists with the expected warehouse and tables, and ask 3 probe questions through `genie_ontology_modeled_knowledge_sdk.benchmark`. Each probe must generate SQL that runs. Fix defects (max 4 deploy attempts) and record the results in `examples/tpch/docs/deployment/agent_validation.md`.

## Context
* The only deploying session in its wave (`allow_deploy: true`). Render (if the template uses rendering), `bundle validate --strict -t dev`, `bundle deploy -t dev` (runDatabricksCli tool with `workingDirectory`). Run `bundle plan -t dev` first to see creates/changes.
* Find the space id with `bundle summary -t dev`. Ids, titles with the dev prefix, and conversation ids go only in the session summary.
* Probe questions: 3 of the agent's sample questions (simple counts or totals). Pass = Genie returned SQL and the statement SUCCEEDED; the answer content is not judged here (that is session 16).
* Users other than the owner would need `USE CATALOG` / `USE SCHEMA` / `SELECT` on the metric views. Dev is owner-only; note this for prd in the summary.

## Tasks
1. Deploy; check the agent has the expected warehouse and every table identifier resolves (`DESCRIBE` each metric view).
2. Run the 3 probes with `benchmark.run_benchmark`; write `agent_validation.md` (question, SQL generated, statement status).
3. A template defect (session 07 files) is fixed in `examples/tpch/` only and listed under "Template fixes for build 1".

## Acceptance Criteria
- [ ] Integrator check `agent_probe`: `agent_validation.md` shows 3/3 probes with SQL generated and SUCCEEDED.
- [ ] `bundle validate --strict -t dev` exits 0 at the end; deploy exit 0.
- [ ] No resolved names or ids in committed files.

## Owned Paths / Assets
- `examples/tpch/ontology-genie-agents/**`
- `examples/tpch/docs/deployment/**`
- Workspace: the dev deployment of the dogfood agents bundle and its Genie Agent(s).

## Dependencies
- Session 14: agent files. Session 12: registered MVs. Session 04: `benchmark.py`.
