# 2026-11-24 — Wave 0-7, Session 14: TPC-H Genie Agent Curation

Build run `1082430844509839`, continuation 0. Mode: edit (`allow_execute`). Branch `mg-genie-ontology-modeled-knowledge-sdk` (checked read-only: Git folder is on the branch). No deploy, no Git commands, no Genie API writes.

## Result: pass

One agent, `tpch_supply_chain_agent`, over all 7 registered TPC-H metric views. `validate_space`: 0 errors. 3 example SQLs pass `EXPLAIN`. `bundle validate --strict -t dev`: Validation OK.

## What was done
1. Read `PROJECT_MEMORY.md` (no `hi_genie/` at the build root), plan `build-0/14`, the session 12 summary, `skills/ontology-agent-curation/SKILL.md`, the agents bundle README (render approach), `registration_results.md`, `manifest.json`, the 7 MV YAMLs, `02_kpi_definitions.md` and `data_model_summary.md`.
2. `plan_agents(mv_refs_from_manifest(manifest), max_per_agent=50)` (from `sdk_config.json`): 7 views <= 50, so **1 agent** `tpch_supply_chain_agent`, domain `tpch_supply_chain`, no subdomain split. All 7 views are in `registration_results.md` as registered + smoke + cardinality pass.
3. `build_space` -> `validate_space` (0 errors) -> `space_to_json`, written to `examples/tpch/ontology-genie-agents/agents/tpch_supply_chain_agent.geniespace.json`. Identifiers are tokenized (`${target_catalog}.${target_schema}.mv_tpch_supply_chain_*`); no resolved catalog/schema names in the file.
4. `resources/genie_agents.yml`: replaced the template `ontology_agent` entry with `tpch_supply_chain_agent` (`file_path: ../.rendered/tpch_supply_chain_agent.geniespace.json`, same warehouse, parent path and permissions).
5. Render: `python -m genie_ontology_sdk.geniespace render agents .rendered --params .databricks/bundle/dev/variable-overrides.json` exit 0, no `${` left. `bundle validate --strict --target dev`: Validation OK.
6. `examples/tpch/docs/domain_manifest.yml`: content of `write_domain_manifest(plans, ..., descriptions)` (generated to a scratch path, then written with the workspace file tools; byte-identical). **Proposal only**: no UC domain was created.

## Agent content
**Sample questions (8)**, each traceable to a KPI in `02_kpi_definitions.md`:
| Question | KPI | View |
|---|---|---|
| What was revenue by market segment for each order year? | Revenue | revenue |
| What is the on-time shipping rate by ship mode? | Delivery performance | fulfillment |
| Which part types had the highest profit margin in 1997? | Product type profit | profit |
| What is the inventory value at supply cost by supplier nation? | Inventory value | supply_cost |
| What is the return rate by customer nation? | Return rate | returns |
| What share of market volume in the AMERICA region came from BRAZIL suppliers in 1995 and 1996? | National market share | market_share |
| Which 10 customers lost the most revenue to returns in the fourth quarter of 1993? | Returned item revenue lost | returns |
| How did order count and average order total change year over year? | Order volume / AOV | orders |

**Example SQL (3, multi-step only):** market share ratio (`MEASURE() FILTER`), top-10 returned revenue (ranking), year-over-year orders (`LAG` over a CTE). All use `MEASURE()` and backtick names from the YAML.

**Text instructions (2):**
* Revenue = discounted `Revenue` measure; `Order Total Price` (orders view) is the tax-inclusive header total. Reason: two views carry revenue-like totals, a genuine ambiguity across views.
* National market share = supplier nation's `Market Volume` / total `Market Volume` for the same customer region and order year. Reason: the market_share view has only `Market Volume`; the ratio for a chosen nation cannot be a static measure.

**Join specs: none.** `data_model_summary.md` verifies joins between source tables only; there is no verified relationship between metric views, and each view already contains its joins.

## Decisions
* The template placeholder `agents/ontology_agent.geniespace.json` (`mv_placeholder`) is **kept** but no longer referenced by `resources/genie_agents.yml`. The curation skill forbids file deletion in unattended sessions. It passes `validate_space` and has no resolved names. Request to owner: delete it.
* `.geniespace.json` files cannot be created with the workspace file editor ("Requested node type [UNKNOWN] is not supported", as the README says). The agent file was written with the workspace import API (`format: RAW`, SDK `w.workspace.import_`) and read back: sha256 matches the `space_to_json` output.

## Problem found: dev overrides schema does not match the registered schema
The gitignored `ontology-genie-agents/.databricks/bundle/dev/variable-overrides.json` sets `schema` to a schema where the metric views do **not** exist (EXPLAIN: `TABLE_OR_VIEW_NOT_FOUND`). `information_schema.tables` shows all 7 `METRIC_VIEW`s in the schema session 12 deployed (`dev_<user>_ontology`, see the session 12 summary), not `dev_<user>_ontology_tpch`. The example SQL EXPLAIN checks were therefore run with that registered schema substituted in memory; all 3 pass. `bundle validate` passes either way (it does not resolve tables), but a deploy (wave 0-8) with the current overrides would create an agent over missing tables. **Owner action:** set `schema` in that overrides file to the schema DAB 1 registered into, then re-render. Session 14 does not own that file.

## Checks
| Check | Result |
|---|---|
| Branch is `mg-genie-ontology-modeled-knowledge-sdk` | pass |
| `plan_agents` agent count (1 for 7 views) | pass |
| `validate_space` on every `agents/*.geniespace.json` (2 files) | pass (0 errors) |
| Only registered MVs referenced | pass (7/7) |
| 5-10 sample questions | pass (8) |
| Example SQL `EXPLAIN` (3) on the overrides' warehouse | pass, against the registered schema (overrides schema fails, see above) |
| No resolved catalog/schema names in committed agent files | pass |
| Render leaves no `${` | pass |
| `bundle validate --strict --target dev` | pass |

## Files modified
* `examples/tpch/ontology-genie-agents/agents/tpch_supply_chain_agent.geniespace.json` (new)
* `examples/tpch/ontology-genie-agents/resources/genie_agents.yml`
* `examples/tpch/docs/domain_manifest.yml` (new)
* Gitignored render output: `ontology-genie-agents/.rendered/*.geniespace.json`

## Skill gaps (for build 1)
* `ontology-agent-curation` says to write the domain manifest with `write_domain_manifest(path)` and the agent file directly, but unattended sessions must use workspace file tools, which cannot create `*.geniespace.json`. Document the import-API path (or add a `geniespace write` CLI) in the skill.
* `domain_manifest` for a single-agent plan collapses the subdomains into one named after the domain, so the manifest's `subdomain` values (sales, fulfillment, procurement) are lost from the proposal. Consider listing the real subdomains with the same agent.
* `render_space_text` only accepts full JSON documents; resolving a single SQL string for `EXPLAIN` needs a token-substitution helper (e.g. `render_text`).
* The skill should tell the session to check that the overrides' `catalog`/`schema` match where DAB 1 registered the views (an `information_schema` check) before running EXPLAIN.
* The skill does not say what to do with the template placeholder agent (delete vs keep) given its no-deletion rule.

## Requests
* Owner: fix `schema` in `ontology-genie-agents/.databricks/bundle/dev/variable-overrides.json` (high for wave 0-8 deploy).
* Owner: delete `agents/ontology_agent.geniespace.json` (template placeholder, unreferenced).
