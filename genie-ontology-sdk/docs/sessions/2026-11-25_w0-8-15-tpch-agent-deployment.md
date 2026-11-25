# 2026-11-25 — Wave 0-8, Session 15: TPC-H Genie Agent Deployment

Build run `1082430844509839`, continuation 0. Mode: edit (`allow_execute`, `allow_deploy`). Branch `mg-genie-ontology-modeled-knowledge-sdk` (checked read-only: the Git folder is on the branch). No Git write commands, no memory writes.

## Result: blocked (no deploy)

The session stopped before attempt 1. Deploying with the current dev overrides would create the Genie Agent over metric views that do not exist, so the probes could not pass and the space would be wrong. The cause is in a file this session may not edit.

## Problem
Session 14 reported this and it is still not fixed. The gitignored `examples/tpch/ontology-genie-agents/.databricks/bundle/dev/variable-overrides.json` sets `schema` to `dev_<user>_ontology_tpch`. Checked in this session:
* `<catalog>.information_schema.schemata`: that schema **does not exist** (0 rows).
* `<catalog>.information_schema.tables` (`table_type = 'METRIC_VIEW'`, `mv_tpch_supply_chain_%`): all **7** metric views are in `dev_<user>_ontology`, the schema DAB 1 (session 12) registered into.

The file matches `exclude_paths` (`examples/tpch/**/.databricks/**`), and PROJECT_MEMORY says the owner writes it by hand. A `--var schema=...` override on the deploy command would work around the owner's file without approval, so it was not used.

## Checks
| Check | Result |
|---|---|
| Branch is `mg-genie-ontology-modeled-knowledge-sdk` | pass |
| Overrides `schema` resolves to the registered metric views | fail (schema missing; views are in `dev_<user>_ontology`) |
| `bundle validate --strict --target dev` (existing render) | pass (Validation OK; it does not resolve tables) |
| `bundle plan` / `bundle deploy -t dev` | skipped (blocked) |
| Agent warehouse + `DESCRIBE` of each table identifier | skipped (blocked) |
| `agent_probe` (3 probes via `benchmark.run_benchmark`) | skipped (blocked) |

## Files modified
None. `examples/tpch/docs/deployment/agent_validation.md` was not written because no probe ran.

## Requests
* Owner (high): set `schema` in `examples/tpch/ontology-genie-agents/.databricks/bundle/dev/variable-overrides.json` to the schema DAB 1 registered into (`dev_<user>_ontology`), then re-run this session. It re-renders `.rendered/`, deploys and runs the probes.
* Owner (normal, carried over from session 14): delete the unreferenced template placeholder `agents/ontology_agent.geniespace.json`.

## Notes for prd
Users other than the owner need `USE CATALOG`, `USE SCHEMA` and `SELECT` on the metric views to use the agent. Dev is owner-only.

## Template / skill gaps for build 1
* The DAB 1 dev schema name (dev prefix + base schema) and the `schema` value the agents bundle expects are set by hand in two places and have already drifted. Derive the agents bundle `schema` from DAB 1 (for example, have the render step check `information_schema` and fail when the schema is missing).
* The render CLI should fail when the target schema or any rendered identifier does not resolve, not only when a token is unresolved.
