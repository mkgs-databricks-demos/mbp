# 2026-11-25 — Wave 0-8, Session 15: TPC-H Genie Agent Deployment

Mode: edit (`allow_execute`, `allow_deploy`). Branch `mg-genie-ontology-modeled-knowledge-sdk` (checked read-only: the Git folder is on the branch, before deploy and again at the end). No Git write commands, no memory writes.

## Run `440901917884797` (continuation 0): pass

The owner fixed the blocker from the earlier run: the dev `variable-overrides.json` now sets `schema` to the schema DAB 1 registered into. This summary covers both runs. The earlier blocked run is described below.

### What was done
1. Checked `hls_fde_dev.information_schema.tables`: all 7 `mv_tpch_supply_chain_*` `METRIC_VIEW`s are in `dev_matthew_giglia_ontology`, which matches the overrides.
2. Render step from the README (`python -m genie_ontology_sdk.geniespace render agents .rendered --params .databricks/bundle/dev/variable-overrides.json`): exit 0, and no `${` left in `.rendered/tpch_supply_chain_agent.geniespace.json`. `.rendered/` is gitignored.
3. `bundle validate --strict -t dev`: Validation OK. `bundle plan -t dev`: create `genie_spaces.tpch_supply_chain_agent` and its `.permissions` (2 to add, 0 change, 0 delete).
4. Deploy attempt 1: `bundle deploy -t dev` exit 0 (2 created; deployment `4398315338762631`, version 1). One attempt was used out of the 4 allowed.
5. Verified the space with `w.genie.get_space(include_serialized_space=True)`:
   * warehouse `24087b85239cacac` matches the override
   * `DESCRIBE TABLE` resolves for all 7 identifiers
   * each of the 3 example SQLs returns a physical plan from `EXPLAIN` (no planning error)
6. Probes: `benchmark.run_benchmark` ran 3 of the agent's sample questions (on-time shipping rate by ship mode, return rate by customer nation, revenue by market segment per order year). For all 3, the message was `COMPLETED`, SQL was generated over the matching metric view with `MEASURE()`, and the statement `SUCCEEDED`. `score`: 3/3 SQL generated, 3/3 succeeded, 0 errors. Results are in `examples/tpch/docs/deployment/agent_validation.md` (tokenized identifiers).
7. Final `bundle validate --strict -t dev`: Validation OK. A check of the committed files I own (agent files, resources, `databricks.yml`, README, `agent_validation.md`) found no resolved catalog, schema, warehouse or space ids.

### Resolved ids (summary only)
* Genie space `tpch_supply_chain_agent`: `01f1e8a428241105b01bbc2f4e355e30`, title `[dev matthew_giglia] TPC-H Supply Chain Agent`, parent `/Workspace/Users/matthew.giglia@databricks.com/.bundle/ontology-genie-agents/dev/genie`
* Probe conversation ids are not recorded. The benchmark returns them but they were not persisted. Session 16 starts new conversations.

### Checks (this run)
| Check | Result |
|---|---|
| Branch is `mg-genie-ontology-modeled-knowledge-sdk` | pass |
| Overrides `schema` holds the 7 registered metric views | pass |
| Render leaves no `${` | pass |
| `bundle validate --strict -t dev` (before and after deploy) | pass |
| `bundle deploy -t dev` | pass (exit 0) |
| Space warehouse + `DESCRIBE` of 7 identifiers | pass |
| Example SQL `EXPLAIN` (3) | pass |
| `agent_probe` (3/3 SQL generated + SUCCEEDED) | pass |
| No resolved names/ids in committed files | pass |

### Files modified (this run)
* `examples/tpch/docs/deployment/agent_validation.md` (new)
* Gitignored render output: `examples/tpch/ontology-genie-agents/.rendered/*.geniespace.json` (regenerated)

### Template fixes for build 1
None were needed in `examples/tpch/`. The template/skill gaps listed below still apply.

### Requests (still open)
* Owner (normal): delete the unreferenced template placeholder `agents/ontology_agent.geniespace.json` (carried over from session 14).

## Earlier run `1082430844509839`: blocked (no deploy)

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
